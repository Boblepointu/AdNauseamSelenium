/*
 * noise_engine.js — injected browser-side network-noise generator.
 *
 * Generates NON-EXECUTING full-spectrum request noise toward random domains to
 * defeat DNS/ISP profiling and traffic analysis. It NEVER injects <script src>
 * or <iframe src> (those would execute remote — possibly malware — code); it only
 * ever uses request primitives that fetch bytes without running them.
 *
 * Contract (set by the Python side BEFORE this source is evaluated):
 *   window.__NOISE = { domains: ["a.com", ...],
 *                      config: { ratio, maxConcurrency, sampleRefreshMs, enabled } }
 * Re-injection on a later page just refreshes the pool and keeps going.
 * Exposes: window.__noiseStats = () => ({ sent, real, target, pool }).
 */
(function () {
  'use strict';

  var N = window.__NOISE || { domains: [], config: {} };
  var cfg = Object.assign(
    { ratio: 10, maxConcurrency: 10, sampleRefreshMs: 15000, enabled: true, dohRatio: 0.22 },
    N.config || {}
  );

  // DoH resolver pool (weighted-expanded base URLs, e.g. https://dns.google/dns-query).
  // A minority (~dohRatio) of DNS-generating emissions are DoH queries fired at these
  // globally-rotating resolvers; the majority are STANDARD DNS lookups (fetch/img/link
  // resolve through the browser node's system resolver, which the dns-rotator sidecar
  // rotates across validated public :53 resolvers). Together: ~78% standard / ~22% DoH.
  var dohPool = Array.isArray(N.doh) ? N.doh.slice() : [];
  var dohRatio = (typeof cfg.dohRatio === 'number') ? cfg.dohRatio : 0.22;

  // ---- Double-injection guard -------------------------------------------------
  // If already running, just refresh the live pool and bail. This keeps a single
  // engine alive across intra-page re-injections while swapping in fresh domains.
  if (window.__noiseEngineActive) {
    try {
      if (typeof window.__noiseRefresh === 'function') {
        window.__noiseRefresh((window.__NOISE && window.__NOISE.domains) || []);
      }
    } catch (e) { /* never throw into host page */ }
    return;
  }

  // ---- Bail-out conditions ----------------------------------------------------
  var pool = Array.isArray(N.domains) ? N.domains.slice() : [];
  if (cfg.enabled === false || pool.length === 0) {
    // Still expose a stats shim so Python probes never crash.
    window.__noiseStats = function () {
      return { sent: 0, real: 0, target: 0, pool: pool.length };
    };
    return;
  }

  window.__noiseEngineActive = true;

  // ---- Engine state -----------------------------------------------------------
  var stopped = false;
  var noiseSent = 0;          // number of noise requests we have issued
  var dohSent = 0;            // subset of noiseSent that were DoH DNS queries
  var inFlight = 0;           // current concurrency (fetch/image slots)
  var ownUrls = Object.create(null); // URLs WE issued, to subtract from "real"
  var seenReal = Object.create(null); // real resource URLs already counted
  var realCount = 0;

  var socketCount = 0;        // bounded live WebSocket/EventSource count
  var MAX_SOCKETS = 4;
  var liveSockets = [];       // {close:fn} handles to force-close on teardown

  var tickTimer = null;
  var refreshTimer = null;
  var observer = null;
  var container = null;       // hidden div holding <link> nodes

  var TICK_MS = 300;          // pacing cadence
  var BATCH_MAX = 6;          // max requests kicked off per tick
  var REQ_TIMEOUT_MS = 9000;  // force-release a fetch/image slot after this

  function clamp(n, lo, hi) { return n < lo ? lo : (n > hi ? hi : n); }
  function maxConc() { return clamp(cfg.maxConcurrency | 0 || 10, 1, 64); }

  // ---- Real-request accounting ------------------------------------------------
  // A "real" request is any resource timing entry that is NOT one we issued.
  function noteResource(url) {
    if (!url) { return; }
    if (ownUrls[url]) { return; }       // it's our own noise
    if (seenReal[url]) { return; }      // already counted this exact URL
    seenReal[url] = 1;
    realCount++;
  }

  function seedReal() {
    try {
      var entries = performance.getEntriesByType('resource');
      for (var i = 0; i < entries.length; i++) {
        noteResource(entries[i].name);
      }
    } catch (e) { /* ignore */ }
    // Count the document navigation itself as one real request.
    realCount++;
  }

  function startObserver() {
    try {
      // Our own fetch/image noise floods the resource-timing buffer (default
      // ~250). Enlarge it and drop our noise on overflow so genuinely new real
      // resources keep being observed and realCount (=> target) doesn't plateau.
      if (typeof performance.setResourceTimingBufferSize === 'function') {
        performance.setResourceTimingBufferSize(1e5);
        performance.addEventListener('resourcetimingbufferfull', function () {
          try { performance.clearResourceTimings(); } catch (e) {}
        });
      }
    } catch (e) { /* ignore */ }
    try {
      observer = new PerformanceObserver(function (list) {
        if (stopped) { return; }
        var ents = list.getEntries();
        for (var i = 0; i < ents.length; i++) {
          noteResource(ents[i].name);
        }
      });
      observer.observe({ type: 'resource', buffered: true });
    } catch (e) {
      observer = null; // older engines without PerformanceObserver
    }
  }

  function target() {
    return (cfg.ratio | 0 || 10) * realCount;
  }

  // ---- URL construction -------------------------------------------------------
  var PATHS = [
    'assets', 'static', 'img', 'images', 'js', 'css', 'api', 'v1', 'v2',
    'cdn', 'media', 'content', 'data', 'track', 'pixel', 'beacon', 'ping',
    'ads', 'analytics', 'collect', 'event', 'metrics', 'feed', 'rss', 'tag'
  ];
  var EXTS = ['', '.js', '.css', '.png', '.gif', '.json', '.svg', '.woff2', ''];

  function rand(n) { return Math.floor(Math.random() * n); }
  function pick(arr) { return arr[rand(arr.length)]; }
  function pickDomain() { return pool[rand(pool.length)]; }

  var LABELCH = 'abcdefghijklmnopqrstuvwxyz0123456789';
  function randLabel() {
    var len = 4 + rand(10), s = '';
    for (var i = 0; i < len; i++) { s += LABELCH.charAt(rand(LABELCH.length)); }
    return s;
  }

  // Most standard-DNS noise uses a fresh random subdomain so each request forces a
  // NEW recursive lookup at the (rotating) system resolver instead of hitting cache —
  // this is what makes the DNS noise voluminous and unique rather than repetitive.
  function noisyHost(domain) {
    return (Math.random() < 0.65) ? (randLabel() + '.' + domain) : domain;
  }

  function cacheBust() {
    return 'nb=' + Date.now().toString(36) + rand(1e6).toString(36);
  }

  function buildPath() {
    var depth = 1 + rand(3);
    var segs = [];
    for (var i = 0; i < depth; i++) { segs.push(pick(PATHS)); }
    return '/' + segs.join('/') + '/' + rand(1e6).toString(36) + pick(EXTS);
  }

  function buildUrl(domain, scheme) {
    var s = scheme || (Math.random() < 0.9 ? 'https' : 'http');
    return s + '://' + noisyHost(domain) + buildPath() + '?' + cacheBust();
  }

  // ---- Concurrency slot helpers ----------------------------------------------
  function acquire() { inFlight++; }
  function release() { if (inFlight > 0) { inFlight--; } }

  // ---- Non-executing request primitives --------------------------------------
  function viaFetch(domain) {
    var url = buildUrl(domain);
    var method = pick(['GET', 'GET', 'HEAD', 'POST']);
    ownUrls[url] = 1;
    acquire();
    noiseSent++;
    var done = false;
    var timer = null;
    var fin = function () {
      if (done) { return; }
      done = true;
      if (timer) { clearTimeout(timer); timer = null; }
      release();
    };
    try {
      // Bound each request: the corpus is full of dead/malware hosts that can
      // complete a handshake then stall forever, which would pin the
      // concurrency cap and starve emission. Abort after REQ_TIMEOUT_MS.
      var ctrl = (typeof AbortController !== 'undefined') ? new AbortController() : null;
      var opts = {
        mode: 'no-cors',
        method: method,
        cache: 'no-store',
        keepalive: true,
        redirect: 'follow',
        credentials: 'omit'
      };
      if (ctrl) { opts.signal = ctrl.signal; }
      if (method === 'POST') { opts.body = 'n=' + rand(1e6); }
      timer = setTimeout(function () { try { if (ctrl) { ctrl.abort(); } } catch (e) {} fin(); }, REQ_TIMEOUT_MS);
      fetch(url, opts).then(fin, fin);
    } catch (e) {
      fin();
    }
  }

  function viaImage(domain) {
    var url = buildUrl(domain);
    ownUrls[url] = 1;
    acquire();
    noiseSent++;
    try {
      var img = new Image();
      var done = false;
      var timer = null;
      var fin = function () {
        if (done) { return; }
        done = true;
        if (timer) { clearTimeout(timer); timer = null; }
        img.onload = img.onerror = null;
        release();
      };
      // A stuck image (host stalls after connect) fires neither onload nor
      // onerror, so force-release the slot after REQ_TIMEOUT_MS.
      timer = setTimeout(fin, REQ_TIMEOUT_MS);
      img.onload = fin;
      img.onerror = fin;
      img.src = url;
    } catch (e) {
      release();
    }
  }

  function viaLink(domain) {
    // Pure DNS / connection warm-up noise; no slot needed (no load callback).
    try {
      if (!container) { return; }
      var rel = pick(['dns-prefetch', 'preconnect', 'prefetch']);
      noiseSent++;  // count only once we know a link node will be appended
      var link = document.createElement('link');
      link.rel = rel;
      if (rel === 'dns-prefetch') {
        link.href = '//' + noisyHost(domain);
      } else if (rel === 'preconnect') {
        link.href = 'https://' + noisyHost(domain);
      } else {
        var url = buildUrl(domain);
        ownUrls[url] = 1;
        link.href = url;
      }
      container.appendChild(link);
      setTimeout(function () {
        try { if (link && link.parentNode) { link.parentNode.removeChild(link); } }
        catch (e) { /* ignore */ }
      }, 4000 + rand(4000));
    } catch (e) { /* ignore */ }
  }

  function viaBeacon(domain) {
    if (!navigator || typeof navigator.sendBeacon !== 'function') {
      return false;
    }
    var url = buildUrl(domain);
    ownUrls[url] = 1;
    try {
      var blob = new Blob(['x' + rand(1e6)], { type: 'text/plain' });
      var ok = navigator.sendBeacon(url, blob);
      if (ok) { noiseSent++; return true; }
    } catch (e) { /* ignore */ }
    return false;
  }

  function viaSocket(domain) {
    if (socketCount >= MAX_SOCKETS) { return false; }
    var useWs = Math.random() < 0.6;
    try {
      if (useWs && typeof WebSocket === 'function') {
        var ws = new WebSocket('wss://' + domain + '/' + cacheBust());
        socketCount++;
        noiseSent++;
        var wsHandle = { close: function () { try { ws.close(); } catch (e) {} } };
        liveSockets.push(wsHandle);
        var wsGone = false;
        var closeWs = function () {
          if (wsGone) { return; }
          wsGone = true;
          if (socketCount > 0) { socketCount--; }
          try { ws.onopen = ws.onerror = ws.onclose = null; } catch (e) {}
          try { ws.close(); } catch (e) {}
        };
        ws.onopen = function () { setTimeout(closeWs, 500 + rand(1000)); };
        ws.onerror = closeWs;
        ws.onclose = closeWs;
        setTimeout(closeWs, 3000);
        return true;
      }
      if (typeof EventSource === 'function') {
        var url = buildUrl(domain);
        ownUrls[url] = 1;
        var es = new EventSource(url);
        socketCount++;
        noiseSent++;
        liveSockets.push({ close: function () { try { es.close(); } catch (e) {} } });
        var esGone = false;
        var closeEs = function () {
          if (esGone) { return; }
          esGone = true;
          if (socketCount > 0) { socketCount--; }
          try { es.onerror = es.onopen = null; } catch (e) {}
          try { es.close(); } catch (e) {}
        };
        es.onopen = function () { setTimeout(closeEs, 500 + rand(1000)); };
        es.onerror = closeEs;
        setTimeout(closeEs, 3000);
        return true;
      }
    } catch (e) { /* ignore */ }
    return false;
  }

  // ---- DoH (RFC 8484 wireformat) DNS query noise ------------------------------
  // Encodes a DNS query for a random (usually fresh-subdomain) name with a random
  // record type, base64url it, and GET it at a weighted-random global DoH resolver.
  // no-cors: we never read the answer — the point is that the query is RESOLVED at a
  // rotating set of resolvers worldwide, so no single resolver sees a coherent picture.
  var QTYPES = [1, 1, 1, 28, 28, 16, 15, 2, 65]; // A (weighted), AAAA, TXT, MX, NS, HTTPS
  function b64url(bytes) {
    var bin = '';
    for (var i = 0; i < bytes.length; i++) { bin += String.fromCharCode(bytes[i] & 255); }
    return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  }
  function dnsWire(name, qtype) {
    var id = rand(65536);
    var b = [(id >> 8) & 255, id & 255, 0x01, 0x00, 0, 1, 0, 0, 0, 0, 0, 0];
    var labels = name.split('.');
    for (var i = 0; i < labels.length; i++) {
      var l = labels[i]; if (!l.length) { continue; }
      b.push(l.length & 255);
      for (var j = 0; j < l.length; j++) { b.push(l.charCodeAt(j) & 255); }
    }
    b.push(0);                              // root label
    b.push((qtype >> 8) & 255, qtype & 255); // QTYPE
    b.push(0, 1);                            // QCLASS = IN
    return b64url(b);
  }
  function viaDoH() {
    if (!dohPool.length) { return; }
    var base = dohPool[rand(dohPool.length)];
    var name = randLabel() + '.' + pickDomain();
    var url = base + (base.indexOf('?') < 0 ? '?' : '&') + 'dns=' + dnsWire(name, pick(QTYPES));
    ownUrls[url] = 1;
    acquire();
    noiseSent++;
    dohSent++;
    var done = false, timer = null;
    var fin = function () {
      if (done) { return; }
      done = true;
      if (timer) { clearTimeout(timer); timer = null; }
      release();
    };
    try {
      var ctrl = (typeof AbortController !== 'undefined') ? new AbortController() : null;
      var opts = { mode: 'no-cors', method: 'GET', cache: 'no-store', keepalive: true,
                   credentials: 'omit', headers: { 'accept': 'application/dns-message' } };
      if (ctrl) { opts.signal = ctrl.signal; }
      timer = setTimeout(function () { try { if (ctrl) { ctrl.abort(); } } catch (e) {} fin(); }, REQ_TIMEOUT_MS);
      fetch(url, opts).then(fin, fin);
    } catch (e) {
      fin();
    }
  }

  // ---- One noise emission, random primitive -----------------------------------
  function emitOne() {
    // ~dohRatio of DNS-generating emissions are DoH; the rest are standard-DNS
    // primitives (fetch/img/link) that resolve via the rotating system resolver.
    if (dohPool.length && Math.random() < dohRatio) { viaDoH(); return; }
    var domain = pickDomain();
    if (!domain) { return; }
    var r = Math.random();
    // Weighted mix: fetch and image dominate; links give DNS noise; sockets/beacon rare.
    if (r < 0.42) {
      viaFetch(domain);
    } else if (r < 0.74) {
      viaImage(domain);
    } else if (r < 0.90) {
      viaLink(domain);
    } else if (r < 0.96) {
      if (!viaBeacon(domain)) { viaImage(domain); }
    } else {
      if (!viaSocket(domain)) { viaFetch(domain); }
    }
  }

  // ---- Pacing loop ------------------------------------------------------------
  function tick() {
    if (stopped) { return; }
    try {
      var tgt = target();
      var budget = tgt - noiseSent;
      if (budget <= 0) { return; }
      var cap = maxConc();
      var n = 0;
      while (n < BATCH_MAX && noiseSent < tgt && inFlight < cap) {
        emitOne();
        n++;
      }
    } catch (e) { /* never throw into host page */ }
  }

  // ---- Pool refresh (live, and via periodic re-read of window.__NOISE) --------
  function refreshPool(domains) {
    try {
      if (Array.isArray(domains) && domains.length) {
        pool = domains.slice();
      }
    } catch (e) { /* ignore */ }
  }
  window.__noiseRefresh = refreshPool;

  function periodicRefresh() {
    if (stopped) { return; }
    try {
      var d = window.__NOISE && window.__NOISE.domains;
      if (Array.isArray(d) && d.length) { pool = d.slice(); }
      var dh = window.__NOISE && window.__NOISE.doh;
      if (Array.isArray(dh) && dh.length) { dohPool = dh.slice(); }
    } catch (e) { /* ignore */ }
  }

  // ---- Teardown ---------------------------------------------------------------
  function teardown() {
    if (stopped) { return; }
    stopped = true;
    try { if (tickTimer !== null) { clearInterval(tickTimer); } } catch (e) {}
    try { if (refreshTimer !== null) { clearInterval(refreshTimer); } } catch (e) {}
    tickTimer = null;
    refreshTimer = null;
    try { if (observer) { observer.disconnect(); } } catch (e) {}
    observer = null;
    for (var i = 0; i < liveSockets.length; i++) {
      try { liveSockets[i].close(); } catch (e) {}
    }
    liveSockets = [];
    socketCount = 0;
    try {
      if (container && container.parentNode) {
        container.parentNode.removeChild(container);
      }
    } catch (e) {}
    container = null;
  }

  // Pause emission while the page is hidden and resume when visible again.
  // A transient hide (tab backgrounded, or an automation context that reports
  // 'hidden') must NOT permanently kill the engine — teardown() is reserved for
  // pagehide/beforeunload, which are terminal.
  function onVisibility() {
    try {
      if (stopped) { return; }
      if (document.visibilityState === 'hidden') {
        if (tickTimer !== null) { clearInterval(tickTimer); tickTimer = null; }
      } else if (tickTimer === null) {
        tickTimer = setInterval(tick, TICK_MS);
      }
    } catch (e) {}
  }

  // ---- Boot -------------------------------------------------------------------
  function boot() {
    try {
      container = document.createElement('div');
      container.style.cssText =
        'position:absolute;width:0;height:0;overflow:hidden;' +
        'left:-9999px;top:-9999px;pointer-events:none;';
      container.setAttribute('aria-hidden', 'true');
      var host = document.body || document.documentElement;
      if (host) { host.appendChild(container); }
    } catch (e) { container = null; }

    seedReal();
    startObserver();

    try { tickTimer = setInterval(tick, TICK_MS); } catch (e) { tickTimer = null; }
    try {
      refreshTimer = setInterval(
        periodicRefresh,
        clamp(cfg.sampleRefreshMs | 0 || 15000, 2000, 600000)
      );
    } catch (e) { refreshTimer = null; }

    try {
      window.addEventListener('pagehide', teardown, { once: true });
      window.addEventListener('beforeunload', teardown, { once: true });
      document.addEventListener('visibilitychange', onVisibility);
    } catch (e) { /* ignore */ }
  }

  // ---- Public stats probe -----------------------------------------------------
  window.__noiseStats = function () {
    return {
      sent: noiseSent,
      doh: dohSent,
      real: realCount,
      target: target(),
      pool: pool.length,
      dohPool: dohPool.length
    };
  };

  try {
    boot();
  } catch (e) {
    // As a last resort, tear down so we never leave partial state running.
    try { teardown(); } catch (e2) {}
  }
})();
