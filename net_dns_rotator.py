#!/usr/bin/env python3
"""net-dns-rotator — rotate the WHOLE NETWORK's upstream DNS at the OPNsense router.

Where ``dns_rotator.py`` churns the Selenium *browser nodes'* ``/etc/resolv.conf``,
this sidecar churns the *entire LAN's* egress DNS by rotating OPNsense Unbound's
query-forwarding targets. Every ``NET_DNS_ROTATE_INTERVAL`` seconds it picks a
fresh weighted-random SUBSET of validated public :53 resolvers (from
``crawler/dns_resolvers.json``, the same pool the node rotator uses), always
including a stable fallback, and — unless in DRY_RUN — applies it to Unbound via
:class:`opnsense.OPNsenseClient`. Over time real network DNS is smeared across
the whole validated pool, drowning genuine lookups in the crawler's noise.

THIS TOUCHES A PRODUCTION ROUTER. It is therefore aggressively defensive:

* DEFAULT OFF — both ``OPNSENSE_ENABLED`` and ``NET_DNS_ROTATE_ENABLED`` must be
  ``true`` before any connection is attempted. When off, the sidecar is inert.
* DRY_RUN defaults ``true`` — it computes + LOGS the intended forwarder set but
  does NOT apply it until DRY_RUN is explicitly disabled.
* SNAPSHOT once on first successful connect (persisted to disk by the client);
  ``--restore`` puts the original config back and exits.
* The fallback resolver (``NET_DNS_FALLBACK``, default ``1.1.1.1``) is ALWAYS in
  every applied set, so the LAN can never be left with only dead upstreams.
* Every network call is wrapped; the loop never raises. On ANY apply error the
  client re-applies last-known-good / fallback-only and this loop logs LOUDLY.

Only the router-side forwarding *subset* is rotated — the safe, reversible core.
Spreading egress further via OPNsense NAT / firewall round-robin is a documented
future option (fragile, non-reversible) and is deliberately NOT built here.

CLI:
    python net_dns_rotator.py            # run the rotation loop (respects env)
    python net_dns_rotator.py --once     # a single cycle, then exit (honors DRY_RUN)
    python net_dns_rotator.py --restore   # restore the original config, then exit

Pure stdlib; no third-party deps. Credentials are read from env only and are
never logged or committed.
"""
import os
import re
import sys
import json
import time
import random
import logging

from opnsense import OPNsenseClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S')
logger = logging.getLogger('net-dns-rotator')

# Two independent kill-switches, BOTH default off — belt and suspenders for a
# change that can black-hole DNS for the whole LAN. Either being false = inert.
OPNSENSE_ENABLED = os.getenv('OPNSENSE_ENABLED', 'false').lower() == 'true'
ROTATE_ENABLED = os.getenv('NET_DNS_ROTATE_ENABLED', 'false').lower() == 'true'
# Compute-and-log only until an operator explicitly sets DRY_RUN=false.
DRY_RUN = os.getenv('DRY_RUN', 'true').lower() == 'true'

FALLBACK = os.getenv('NET_DNS_FALLBACK', '1.1.1.1')
INTERVAL = int(os.getenv('NET_DNS_ROTATE_INTERVAL', '600'))
SUBSET_SIZE = int(os.getenv('NET_DNS_SUBSET_SIZE', '8'))
# Hard ceiling so a mis-set env can never bloat the Unbound config.
SUBSET_HARD_MAX = 16
MARKER = os.getenv('NET_DNS_MARKER', 'adnauseam-netrot')
POOL_PATH = os.getenv('NET_DNS_POOL_PATH', '/app/crawler/dns_resolvers.json')
SNAPSHOT_PATH = os.getenv('NET_DNS_SNAPSHOT_PATH', '/data/opnsense/original_dns.json')
HEARTBEAT_FILE = os.getenv('NET_DNS_HEARTBEAT_FILE', '/tmp/net_dns_heartbeat')

_IPV4 = re.compile(r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$')


def _is_ipv4(s):
    m = _IPV4.match(s or '')
    return bool(m) and all(0 <= int(x) <= 255 for x in m.groups())


def _touch_heartbeat():
    """Write a liveness marker each cycle (mirrors dns_rotator's healthcheck contract)."""
    try:
        with open(HEARTBEAT_FILE, 'w') as fh:
            fh.write(str(time.time()))
    except Exception:
        pass


def client_config():
    """Build the OPNsenseClient config dict from env (credentials never logged)."""
    return {
        'url': os.getenv('OPNSENSE_URL', 'https://10.128.112.1'),
        'api_key': os.getenv('OPNSENSE_API_KEY', ''),
        'api_secret': os.getenv('OPNSENSE_API_SECRET', ''),
        'verify_tls': os.getenv('OPNSENSE_VERIFY_TLS', 'false').lower() == 'true',
        'ssh_host': os.getenv('OPNSENSE_SSH_HOST', ''),
        'ssh_user': os.getenv('OPNSENSE_SSH_USER', ''),
        'ssh_key': os.getenv('OPNSENSE_SSH_KEY', ''),
        'marker': MARKER,
        'fallback': FALLBACK,
        'subset_max': min(SUBSET_SIZE, SUBSET_HARD_MAX),
        'snapshot_path': SNAPSHOT_PATH,
    }


def load_pool(path=POOL_PATH):
    """Return the list of validated resolver dicts from the shared pool file.

    Defensive: on any read/parse error, returns ``[]`` (the caller then falls
    back to the fallback-only set) rather than raising into the loop.
    """
    try:
        with open(path, encoding='utf-8') as fh:
            data = json.load(fh)
    except Exception as e:
        logger.warning('could not read pool %s: %s — fallback-only this run', path, str(e)[:80])
        return []
    resolvers = []
    for r in data.get('resolvers', []):
        ip = r.get('ip')
        if _is_ipv4(ip):
            resolvers.append({'ip': ip, 'weight': max(1, int(r.get('weight', 1))),
                              'priority': bool(r.get('priority'))})
    return resolvers


def pick_subset(n, exclude_fallback=True, pool=None):
    """Pick ``n`` DISTINCT resolver IPs by weighted-random sampling (no replacement).

    Weights bias selection toward priority-country / anchor resolvers exactly as
    in ``dns_rotator``. Returns fewer than ``n`` IPs only if the pool is smaller.
    ``exclude_fallback`` drops the stable fallback from candidates so the caller's
    ``ensure_fallback`` can add it back deterministically (avoids double-weighting).
    """
    if pool is None:
        pool = load_pool()
    candidates = [r for r in pool
                  if _is_ipv4(r.get('ip')) and not (exclude_fallback and r.get('ip') == FALLBACK)]
    n = max(0, min(int(n), SUBSET_HARD_MAX, len(candidates)))
    chosen = []
    remaining = list(candidates)
    for _ in range(n):
        total = sum(r['weight'] for r in remaining)
        if total <= 0:
            break
        pivot = random.uniform(0, total)
        upto = 0.0
        for i, r in enumerate(remaining):
            upto += r['weight']
            if upto >= pivot:
                chosen.append(r['ip'])
                remaining.pop(i)
                break
    return chosen


def _log_subset(prefix, subset):
    logger.info('%s %d forwarder(s): %s', prefix, len(subset), ', '.join(subset))


def run_cycle(client, pool, dry_run):
    """Build a fresh subset and (unless dry_run) apply it. Never raises.

    Returns the subset that was applied/intended, or ``None`` on hard failure.
    """
    try:
        picks = pick_subset(SUBSET_SIZE, exclude_fallback=True, pool=pool)
        # ensure_fallback (a pure helper in opnsense) dedups, guarantees the
        # fallback is present, and caps the length — the single source of truth
        # for the applied set's shape, shared with set_forwarders.
        subset = client.ensure_fallback(picks, FALLBACK)
    except Exception as e:
        logger.warning('subset build failed: %s', str(e)[:120])
        return None

    if not subset:
        # Should be impossible (ensure_fallback guarantees the fallback), but never
        # apply an empty set — that would black-hole the LAN.
        logger.error('LOUD: computed forwarder set is EMPTY — refusing to apply, forcing fallback-only')
        subset = [FALLBACK]

    if dry_run:
        _log_subset('DRY_RUN would set', subset)
        return subset

    # set_forwarders / reload_unbound NEVER raise — they return None / False on
    # failure. We MUST inspect those returns (not merely catch exceptions), or a
    # black-holed router (Unbound down, forwarders dead) gets logged as 'applied'.
    applied = None
    ok = False
    try:
        applied = client.set_forwarders(subset)          # None on any apply failure
        ok = bool(client.reload_unbound()) if applied is not None else False
    except Exception as e:  # defensive — the client shouldn't raise
        logger.error('LOUD: apply raised unexpectedly: %s', str(e)[:120])
    if applied is not None and ok:
        _log_subset('applied', subset)
        return subset
    logger.error('LOUD: apply FAILED (set_forwarders=%s reload=%s) — recovering',
                 'None' if applied is None else 'ok', ok)
    _recover(client)
    return None


def _recover(client):
    """Never leave the router mid-change: force fallback-only, else restore snapshot."""
    try:
        fb = client.set_forwarders([FALLBACK])
        fbok = bool(client.reload_unbound()) if fb is not None else False
        if fb is not None and fbok:
            logger.error('LOUD: recovered to fallback-only (%s)', FALLBACK)
            return
        logger.error('LOUD: fallback-only incomplete — restoring original snapshot')
        client.restore(client.snapshot())
        client.reload_unbound()
    except Exception as e:
        logger.error('LOUD: recovery FAILED: %s', str(e)[:120])


def _make_client_or_none():
    """Instantiate the client, snapshot once. Returns client or None (never raises)."""
    try:
        client = OPNsenseClient(client_config())
    except Exception as e:
        logger.error('LOUD: could not construct OPNsenseClient: %s', str(e)[:120])
        return None
    # Snapshot the original config exactly once before any mutation. The client
    # persists it atomically to SNAPSHOT_PATH and will not overwrite an existing
    # snapshot. If we can't snapshot, we must NOT apply — stay snapshot-gated.
    try:
        client.snapshot()
    except Exception as e:
        logger.error('LOUD: initial snapshot failed: %s — staying DRY-RUN-equivalent', str(e)[:120])
        return client if DRY_RUN else None
    # Validate reachability BEFORE any mutation. probe() sets `degraded` on failure
    # and set_forwarders refuses while degraded, so an unreachable/authless router
    # can only ever be read, never mutated.
    try:
        if not client.probe():
            logger.warning('LOUD: OPNsense probe failed — client degraded, read/dry-only')
    except Exception:
        pass
    return client


def do_restore():
    """Restore the persisted original config, then return an exit code."""
    logger.info('net-dns-rotator --restore: restoring original OPNsense DNS config')
    try:
        with open(SNAPSHOT_PATH, encoding='utf-8') as fh:
            snap = json.load(fh)
    except Exception as e:
        logger.error('LOUD: cannot read snapshot %s: %s — nothing to restore', SNAPSHOT_PATH, str(e)[:120])
        return 1
    try:
        client = OPNsenseClient(client_config())
        client.restore(snap)
        client.reload_unbound()
    except Exception as e:
        logger.error('LOUD: restore failed: %s', str(e)[:120])
        return 1
    logger.info('restore complete — original forwarders re-applied')
    return 0


def do_once():
    """Run exactly one cycle (honoring DRY_RUN), then return an exit code."""
    if not (OPNSENSE_ENABLED and ROTATE_ENABLED):
        logger.info('OPNSENSE_ENABLED=%s NET_DNS_ROTATE_ENABLED=%s — disabled, no connection attempted',
                    OPNSENSE_ENABLED, ROTATE_ENABLED)
        return 0
    client = _make_client_or_none()
    if client is None:
        return 1
    _touch_heartbeat()
    subset = run_cycle(client, load_pool(), DRY_RUN)
    return 0 if subset is not None else 1


def main():
    # --- CLI dispatch --------------------------------------------------------
    args = sys.argv[1:]
    if '--restore' in args:
        sys.exit(do_restore())
    if '--once' in args:
        sys.exit(do_once())

    # --- disabled = inert (no connection attempts) ---------------------------
    if not (OPNSENSE_ENABLED and ROTATE_ENABLED):
        logger.info('net-dns-rotator idle: OPNSENSE_ENABLED=%s NET_DNS_ROTATE_ENABLED=%s (default OFF)',
                    OPNSENSE_ENABLED, ROTATE_ENABLED)
        _touch_heartbeat()
        while True:
            time.sleep(3600)

    logger.info('net-dns-rotator up: interval=%ss subset<=%d fallback=%s dry_run=%s url=%s',
                INTERVAL, min(SUBSET_SIZE, SUBSET_HARD_MAX), FALLBACK, DRY_RUN,
                os.getenv('OPNSENSE_URL', 'https://10.128.112.1'))

    client = _make_client_or_none()
    _touch_heartbeat()  # alive immediately so a container healthcheck passes from boot

    pool = load_pool()
    reload_every = max(1, int(3600 / max(INTERVAL, 1)))  # refresh the pool ~hourly
    cycle = 0
    while True:
        try:
            if client is None:
                # Snapshot/connect failed earlier; keep retrying to construct so a
                # transient router/API outage self-heals without a restart.
                client = _make_client_or_none()
            if client is not None:
                run_cycle(client, pool, DRY_RUN)
            else:
                logger.warning('no OPNsense client this cycle — skipping (router unreachable?)')
            cycle += 1
            if cycle % reload_every == 0:
                pool = load_pool() or pool
        except Exception as e:
            logger.warning('rotation cycle error: %s', str(e)[:120])
        _touch_heartbeat()
        time.sleep(INTERVAL)


if __name__ == '__main__':
    main()
