#!/usr/bin/env python3
"""opnsense — thin, defensive OPNsense Unbound query-forwarding client.

This is the apply-layer for network-wide DNS rotation (see ``net_dns_rotator``).
It manages ONLY our own empty-domain forward entries in OPNsense Unbound, tagged
by ``description == MARKER`` (default ``adnauseam-netrot``). User-created
forwarders and domain-specific split-DNS entries are never touched — and in
Unbound a domain-specific forward always outranks an empty-domain one, so
internal/split-DNS resolution keeps working regardless of our churn.

Design constraints (mirrors ``dns_rotator``'s ethos):
  * Pure stdlib (``urllib`` for HTTP, ``ssl`` for the self-signed LAN cert,
    ``subprocess`` for the SSH/``configctl`` fallback). No third-party deps.
  * Credentials read from the caller-supplied ``config`` dict (sourced from env
    by the sidecar) only — never logged, never hardcoded, never committed.
  * Every network call is wrapped; the client NEVER raises into a caller's loop.
    On any transport/HTTP error a method logs and returns a benign value.
  * DEFAULT-OFF / DRY-RUN are enforced by the *sidecar*; this client only acts
    when asked to. It refuses destructive full-config ``set`` fallbacks: if the
    documented ``*_forward`` endpoints misbehave, it marks itself ``degraded``
    and the sidecar stays snapshot-only.

Two auth strategies, chosen by which config keys are populated:
  (A) OPNsense core REST API over HTTPS with api_key/api_secret — PREFERRED.
  (B) SSH fallback running ``configctl`` (keys only; password auth unsupported).
      The forward-entry mutation surface is API-only, so an SSH-only client is
      ``degraded`` for mutations (reconfigure/status still work over SSH).

Pure helpers (``ensure_fallback`` / ``build_unbound_forward_payload``) are import-
safe and network-free so they can be unit-tested without a router.
"""
import os
import ssl
import json
import base64
import logging
import subprocess
import urllib.error
import urllib.request

logger = logging.getLogger('net-dns.opnsense')

# Hard upper bound on how many forwarders we will ever push, to bound the size of
# the generated Unbound config regardless of a mis-set subset size.
MAX_FORWARDERS = 16
DEFAULT_MARKER = 'adnauseam-netrot'
DEFAULT_FALLBACK = '1.1.1.1'
DEFAULT_SUBSET = 8


def ensure_fallback(ips, fallback, cap=MAX_FORWARDERS):
    """Return a de-duplicated forwarder list that always contains ``fallback``.

    Order-preserving dedup; guarantees ``fallback`` is present (appended if the
    input omitted it); caps the result at ``cap`` entries while GUARANTEEING the
    fallback survives the cap (the network can never be left with only rotating,
    possibly-dead upstreams). Non-string / empty entries are dropped.
    """
    out = []
    seen = set()
    for ip in (ips or []):
        if isinstance(ip, str) and ip and ip not in seen:
            seen.add(ip)
            out.append(ip)
    if fallback and fallback not in seen:
        out.append(fallback)
        seen.add(fallback)
    cap = min(int(cap or MAX_FORWARDERS), MAX_FORWARDERS)
    if cap > 0 and len(out) > cap:
        kept = out[:cap]
        if fallback and fallback not in kept:
            # Sacrifice the last rotating pick so the fallback always makes the cut.
            kept[-1] = fallback
        out = kept
    return out


def build_unbound_forward_payload(ip, marker=DEFAULT_MARKER):
    """Return the ``add_forward`` request body for a single upstream ``ip``.

    OPNsense adds one ``dot`` per API call, so this yields one entry. A one-element
    list/tuple is tolerated for convenience. An empty ``domain`` makes Unbound
    forward *all* domains to ``ip``; multiple such entries spread queries across
    the whole set. ``forward_first="1"`` is the deep safety net: if every forwarder
    SERVFAILs, Unbound falls back to its own recursion instead of black-holing.
    """
    if isinstance(ip, (list, tuple)):
        ip = ip[0] if ip else ''
    return {
        'dot': {
            'enabled': '1',
            'type': 'forward',
            'domain': '',
            'server': str(ip),
            'port': '53',
            'verify': '',
            'forward_tcp_upstream': '0',
            'forward_first': '1',
            'description': marker,
        }
    }


class OPNsenseClient:
    """OPNsense Unbound forwarder manager (REST API primary, SSH/configctl fallback).

    ``config`` keys (all optional; sourced from env by the sidecar):
      url, api_key, api_secret, verify_tls, marker, fallback,
      subset_max / subset_size, snapshot_path, timeout,
      ssh_host, ssh_user, ssh_key.
    """

    def __init__(self, config=None):
        config = config or {}
        self.url = (config.get('url') or 'https://10.128.112.1').rstrip('/')
        self._key = config.get('api_key') or ''
        self._secret = config.get('api_secret') or ''
        self.verify_tls = bool(config.get('verify_tls', False))
        self.marker = config.get('marker') or DEFAULT_MARKER
        self.fallback = config.get('fallback') or DEFAULT_FALLBACK
        # Accept either ``subset_max`` (what the sidecar passes) or ``subset_size``;
        # hard-cap at MAX_FORWARDERS regardless so a mis-set env can't bloat config.
        raw_cap = config.get('subset_max', config.get('subset_size', DEFAULT_SUBSET))
        self.subset_max = min(int(raw_cap or DEFAULT_SUBSET), MAX_FORWARDERS)
        self.snapshot_path = config.get('snapshot_path') or '/data/opnsense/original_dns.json'
        self.stats_path = config.get('stats_path') or '/api/unbound/diagnostics/stats'
        self.timeout = int(config.get('timeout', 10) or 10)

        self.ssh_host = config.get('ssh_host') or ''
        self.ssh_user = config.get('ssh_user') or ''
        self.ssh_key = config.get('ssh_key') or ''

        if self._key and self._secret:
            self.strategy = 'api'
        elif self.ssh_host and self.ssh_user and self.ssh_key:
            self.strategy = 'ssh'
        else:
            self.strategy = 'none'

        # ``degraded`` gates every mutation: while set, the sidecar must refuse to
        # apply and stay snapshot-only. SSH-only and no-creds start degraded; a
        # failed API probe flips it on too.
        self.degraded = self.strategy != 'api'
        self.last_good = None

    def ensure_fallback(self, ips, fallback=None):
        """Instance wrapper around the pure helper, using this client's cap."""
        return ensure_fallback(ips, fallback or self.fallback, self.subset_max)

    # ---- transport ------------------------------------------------------
    def _ssl_ctx(self):
        ctx = ssl.create_default_context()
        if not self.verify_tls:
            # Self-signed LAN-management cert: verification off is documented
            # LAN-only risk — never expose the mgmt API to the WAN.
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        return ctx

    def _request(self, method, path, body=None):
        """Perform one API call. Returns ``(status, parsed)`` and NEVER raises.

        ``status`` is an int HTTP code, or ``None`` on a transport failure.
        ``parsed`` is the decoded JSON (dict/list) or ``{}`` when absent/bad.
        """
        if self.strategy != 'api':
            return None, {}
        url = self.url + path
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        if self._key or self._secret:
            token = base64.b64encode(('%s:%s' % (self._key, self._secret)).encode()).decode()
            req.add_header('Authorization', 'Basic ' + token)
        if data is not None:
            req.add_header('Content-Type', 'application/json')
        try:
            with urllib.request.urlopen(req, timeout=self.timeout, context=self._ssl_ctx()) as resp:
                raw = resp.read()
                status = getattr(resp, 'status', None) or resp.getcode()
                try:
                    parsed = json.loads(raw or b'{}')
                except (ValueError, TypeError):
                    parsed = {}
                return status, parsed
        except urllib.error.HTTPError as e:
            logger.warning('OPNsense %s %s -> HTTP %s', method, path, e.code)
            return e.code, {}
        except Exception as e:  # noqa: BLE001 — never raise into a caller loop
            logger.warning('OPNsense %s %s failed: %s', method, path, str(e)[:120])
            return None, {}

    def _ssh(self, args):
        """Run one ``configctl``-style command over SSH (keys only, BatchMode).

        Returns ``(ok, stdout)``. Wrapped; never raises. Used for reconfigure /
        status when the client is in SSH-fallback mode.
        """
        if not (self.ssh_host and self.ssh_user and self.ssh_key):
            return False, ''
        cmd = [
            'ssh', '-i', self.ssh_key,
            '-o', 'BatchMode=yes',
            '-o', 'StrictHostKeyChecking=accept-new',
            '-o', 'ConnectTimeout=%d' % max(1, min(self.timeout, 30)),
            '%s@%s' % (self.ssh_user, self.ssh_host),
        ] + list(args)
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout + 10)
        except Exception as e:  # noqa: BLE001 — SSH transport is best-effort
            logger.warning('OPNsense ssh %s failed: %s', args[:2], str(e)[:120])
            return False, ''
        if proc.returncode != 0:
            logger.warning('OPNsense ssh %s -> rc=%s %s', args[:2], proc.returncode,
                           (proc.stderr or '')[:120])
            return False, proc.stdout or ''
        return True, proc.stdout or ''

    # ---- parsing helpers ------------------------------------------------
    @staticmethod
    def _dot_rows(settings):
        """Defensively pull the list of forward ``dot`` rows from settings/get.

        The ``dot`` container may be a dict-of-dicts keyed by uuid, a list, or an
        empty string when there are none.
        """
        try:
            container = settings.get('unbound', {}).get('dots', {}).get('dot', {})
        except AttributeError:
            return []
        if isinstance(container, dict):
            return [v for v in container.values() if isinstance(v, dict)]
        if isinstance(container, list):
            return [v for v in container if isinstance(v, dict)]
        return []

    @staticmethod
    def _leaf(value):
        """Collapse an OPNsense field to a plain string. A select field arrives as
        ``{option: {"value": ..., "selected": "1"}}``; return the selected key.
        Plain strings pass through."""
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            for key, opt in value.items():
                if isinstance(opt, dict) and str(opt.get('selected')) in ('1', 'true', 'True'):
                    return str(key)
            return ''
        return '' if value is None else str(value)

    # ---- read -----------------------------------------------------------
    def get_dns_state(self):
        """Return the current Unbound forwarding state (never raises).

        ``{"reachable": bool, "mode": str, "forwarders": [ip,...], "rows": [...]}``
        where ``forwarders`` are the empty-domain forward targets.
        """
        status, data = self._request('GET', '/api/unbound/settings/get')
        reachable = status == 200
        rows = self._dot_rows(data) if reachable else []
        forwarders = []
        for r in rows:
            server = self._leaf(r.get('server', ''))
            domain = self._leaf(r.get('domain', ''))
            if server and not domain:
                forwarders.append(server)
        mode = ''
        if reachable and isinstance(data, dict):
            unbound = data.get('unbound', {})
            general = unbound.get('general', {}) if isinstance(unbound, dict) else {}
            mode = self._leaf(general.get('enabled', '')) if isinstance(general, dict) else ''
        return {
            'reachable': reachable,
            'mode': mode,
            'forwarders': forwarders,
            'rows': rows,
        }

    def _search_forward(self):
        """Return the list of forward rows (each has ``uuid``+``description``)."""
        status, data = self._request('POST', '/api/unbound/settings/search_forward', {})
        if status != 200 or not isinstance(data, dict):
            return []
        rows = data.get('rows', [])
        return rows if isinstance(rows, list) else []

    def _our_uuids(self):
        return [r.get('uuid') for r in self._search_forward()
                if r.get('uuid') and r.get('description') == self.marker]

    # ---- write ----------------------------------------------------------
    def _add_forward(self, ip):
        """Add one marked forward entry. Returns ``(saved_ok, uuid)``.

        OPNsense returns HTTP 200 even on validation FAILURE, with body
        ``{"result":"failed",...}``; only ``{"result":"saved"}`` means the row was
        actually created — so success is read from the BODY, not the status code.
        """
        status, data = self._request('POST', '/api/unbound/settings/add_forward',
                                     build_unbound_forward_payload(ip, self.marker))
        ok = status == 200 and isinstance(data, dict) and data.get('result') == 'saved'
        return ok, (data.get('uuid') if isinstance(data, dict) else None)

    def _del_forward(self, uuid):
        status, data = self._request('POST', '/api/unbound/settings/del_forward/%s' % uuid, {})
        return status == 200 and isinstance(data, dict) and data.get('result') in ('deleted', 'ok')

    def set_forwarders(self, ips):
        """Replace OUR marked forwarders with ``ips`` (fallback always included).

        Idempotent w.r.t. our own entries: deletes existing MARKER rows, then adds
        one forward per surviving IP. Does NOT reconfigure — the config is not live
        until :meth:`reload_unbound`, so a crash mid-add leaves an inert config the
        next cycle self-heals. Returns the applied list on success, else ``None``.
        Never raises.
        """
        if self.strategy != 'api' or self.degraded:
            logger.warning('set_forwarders refused — client not in API mode / degraded')
            return None
        applied = ensure_fallback(ips, self.fallback, self.subset_max)
        try:
            for uuid in self._our_uuids():
                self._del_forward(uuid)
            added = 0
            fallback_ok = False
            for ip in applied:
                ok, _uuid = self._add_forward(ip)
                if ok:
                    added += 1
                    if ip == self.fallback:
                        fallback_ok = True
                else:
                    logger.warning('set_forwarders: add %s -> not saved', ip)
            # The fallback exists so the network is NEVER left with only (possibly
            # dead) rotating upstreams. If the fallback's OWN add did not land, treat
            # the whole apply as a FAILURE so the caller recovers — do not record
            # last_good and never let a reload commit a fallback-less set.
            if not fallback_ok:
                logger.error('set_forwarders: FALLBACK %s did not apply — unsafe, FAILURE',
                             self.fallback)
                return None
            self.last_good = list(applied)
            logger.info('set_forwarders staged %d/%d entries (fallback %s live)',
                        added, len(applied), self.fallback)
            return applied
        except Exception as e:  # noqa: BLE001 — belt-and-suspenders, never escape the loop
            logger.error('set_forwarders CRASHED: %s', str(e)[:160])
            return None

    def reload_unbound(self):
        """Regenerate + reload Unbound, then gate on service status.

        Returns ``True`` only when the service reports running afterwards. On the
        API path, a non-running service triggers one restart attempt before the
        caller escalates to :meth:`restore`. Never raises.
        """
        if self.strategy == 'ssh':
            ok, _ = self._ssh(['configctl', 'unbound', 'reconfigure'])
            if not ok:
                logger.error('unbound reconfigure over SSH failed')
            return self._service_running()
        status, data = self._request('POST', '/api/unbound/service/reconfigure', {})
        if status != 200:
            logger.error('unbound reconfigure returned HTTP %s', status)
            return False
        # OPNsense returns HTTP 200 with {"status":"failed"} when config generation
        # rejects the change — a 200 alone is not proof the new config is live.
        if isinstance(data, dict) and str(data.get('status', 'ok')).lower() == 'failed':
            logger.error('unbound reconfigure body reported failed')
            return False
        if self._service_running():
            return True
        logger.error('Unbound NOT running after reconfigure — attempting restart')
        self._request('POST', '/api/unbound/service/restart', {})
        return self._service_running()

    def _service_running(self):
        if self.strategy == 'ssh':
            ok, out = self._ssh(['configctl', 'unbound', 'status'])
            return ok and 'running' in (out or '').lower()
        status, data = self._request('GET', '/api/unbound/service/status')
        if status != 200 or not isinstance(data, dict):
            return False
        return str(data.get('status', '')).lower() == 'running'

    # ---- read-only diagnostics -----------------------------------------
    def get_unbound_stats(self):
        """Return Unbound resolver statistics (total queries, cache hits, etc).

        Read-only: this is the authoritative count of the STANDARD DNS the whole
        network actually resolved (DoH bypasses Unbound). Returns the parsed dict
        on HTTP 200, else ``{}``. The endpoint path is configurable because it has
        varied across OPNsense releases; the default is the current diagnostics one.
        Never raises.
        """
        path = self.stats_path
        status, data = self._request('GET', path)
        if status == 200 and isinstance(data, dict):
            return data
        logger.warning('get_unbound_stats: %s -> HTTP %s (endpoint may differ on this release)',
                       path, status)
        return {}

    # ---- snapshot / restore --------------------------------------------
    def snapshot(self):
        """Capture and PERSIST the original Unbound forwarding config, once.

        Reads the raw forward rows + general mode, then writes them atomically to
        ``snapshot_path`` only if no snapshot exists yet (the true original must
        survive restarts and is NEVER overwritten). Returns the snapshot dict;
        ``{}`` if no state can be read (nothing is written then). Never raises.
        """
        existing = self._load_snapshot()
        if existing is not None:
            return existing
        status, data = self._request('GET', '/api/unbound/settings/get')
        if status != 200:
            self.degraded = True
            logger.error('snapshot: settings/get failed (HTTP %s) — client degraded', status)
            return {}
        rows = self._dot_rows(data)
        unbound = data.get('unbound', {}) if isinstance(data, dict) else {}
        general = unbound.get('general', {}) if isinstance(unbound, dict) else {}
        snap = {
            'dots': rows,
            'general': {k: general.get(k) for k in ('enabled', 'dnssec')} if isinstance(general, dict) else {},
        }
        self._persist_snapshot(snap)
        return snap

    def _load_snapshot(self):
        try:
            if not self.snapshot_path or not os.path.exists(self.snapshot_path):
                return None
            with open(self.snapshot_path, encoding='utf-8') as fh:
                return json.load(fh)
        except Exception as e:  # noqa: BLE001 — best-effort read
            logger.warning('snapshot read %s failed: %s', self.snapshot_path, str(e)[:80])
            return None

    def _persist_snapshot(self, snap):
        """Atomically persist the snapshot ONCE; never overwrite an existing file."""
        path = self.snapshot_path
        if not path or os.path.exists(path):
            return False
        try:
            directory = os.path.dirname(path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            tmp = path + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as fh:
                json.dump(snap, fh, indent=2, sort_keys=True)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, path)
            logger.info('snapshot persisted to %s', path)
            return True
        except Exception as e:  # noqa: BLE001 — persistence is best-effort
            logger.warning('snapshot persist failed %s: %s', path, str(e)[:80])
            return False

    def restore(self, snap=None):
        """Undo our churn: delete all MARKER entries, re-create the snapshot's own
        marked entries (usually none), then reconfigure.

        The original config had no MARKER entries (snapshot is taken before the
        first apply), so removing ours returns the network to its original state.
        Loads the on-disk snapshot when ``snap`` is omitted. Returns ``True`` on a
        confirmed reconfigure. Never raises.
        """
        if self.strategy != 'api' or self.degraded:
            logger.warning('restore refused — client not in API mode / degraded')
            return False
        if snap is None:
            snap = self._load_snapshot() or {}
        snap = snap or {}
        try:
            for uuid in self._our_uuids():
                self._del_forward(uuid)
            # Re-create any of OUR entries the snapshot legitimately held (usually none).
            recreated = 0
            for row in snap.get('dots', []):
                if isinstance(row, dict) and self._leaf(row.get('description', '')) == self.marker:
                    server = self._leaf(row.get('server', ''))
                    if server:
                        self._add_forward(server)
                        recreated += 1
            ok = self.reload_unbound()
            if ok:
                logger.info('restore complete — %d original marked entries re-created', recreated)
            else:
                logger.error('restore reconfigure did NOT confirm Unbound running')
            return ok
        except Exception as e:  # noqa: BLE001 — never escape into the loop
            logger.error('restore CRASHED: %s', str(e)[:160])
            return False

    # ---- probe ----------------------------------------------------------
    def probe(self):
        """First-connect validation. Probes the documented paths and sets
        ``degraded`` on any failure (the sidecar then stays snapshot-only).
        Returns ``True`` only when the client may safely mutate. Never raises.
        """
        if self.strategy == 'none':
            logger.warning('OPNsense: no API creds and no SSH key — client inert/degraded')
            self.degraded = True
            return False
        if self.strategy == 'ssh':
            ok, _ = self._ssh(['configctl', 'unbound', 'status'])
            self.degraded = True  # SSH transport cannot safely mutate forward entries
            if ok:
                logger.info('OPNsense: SSH transport reachable (mutation degraded — status/reload only)')
            else:
                logger.error('OPNsense: SSH probe failed — client degraded')
            return False
        status, _ = self._request('GET', '/api/unbound/settings/get')
        self.degraded = status != 200
        if self.degraded:
            logger.error('OPNsense probe failed (HTTP %s) — refusing to apply', status)
        else:
            logger.info('OPNsense API reachable at %s (verify_tls=%s)', self.url, self.verify_tls)
        return not self.degraded


def client_from_env(env=None):
    """Build an :class:`OPNsenseClient` from the process environment.

    Credentials are read from env ONLY — never hardcoded, logged, or committed.
    """
    env = env if env is not None else os.environ
    return OPNsenseClient({
        'url': env.get('OPNSENSE_URL', 'https://10.128.112.1'),
        'api_key': env.get('OPNSENSE_API_KEY', ''),
        'api_secret': env.get('OPNSENSE_API_SECRET', ''),
        'verify_tls': env.get('OPNSENSE_VERIFY_TLS', 'false').lower() == 'true',
        'marker': env.get('NET_DNS_MARKER', DEFAULT_MARKER),
        'fallback': env.get('NET_DNS_FALLBACK', DEFAULT_FALLBACK),
        'subset_size': int(env.get('NET_DNS_SUBSET_SIZE', str(DEFAULT_SUBSET)) or DEFAULT_SUBSET),
        'snapshot_path': env.get('NET_DNS_SNAPSHOT_PATH', '/data/opnsense/original_dns.json'),
        'ssh_host': env.get('OPNSENSE_SSH_HOST', ''),
        'ssh_user': env.get('OPNSENSE_SSH_USER', ''),
        'ssh_key': env.get('OPNSENSE_SSH_KEY', ''),
    })


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s',
                        datefmt='%Y-%m-%dT%H:%M:%S')
    _c = client_from_env()
    print('strategy=%s degraded=%s url=%s' % (_c.strategy, _c.degraded, _c.url))
