#!/usr/bin/env python3
"""dns-rotator — rotate the browser nodes' upstream DNS resolver over time.

Selenium browser-node containers resolve every page-load (and the noise engine's
standard-DNS primitives) through their own ``/etc/resolv.conf``. This sidecar
rewrites that file on each node every ``ROTATE_INTERVAL_SECS`` to a fresh
weighted-random public :53 resolver drawn from ``crawler/dns_resolvers.json``
(validated + geoip'd out-of-band), so standard DNS traffic egresses through a
globe-spanning, ever-changing set of resolvers — no single resolver ever sees a
coherent picture of what this host browses.

Safety: a stable fallback nameserver (``FALLBACK_DNS``) is always written as the
SECOND nameserver with ``options timeout:2 attempts:1 rotate`` so that a slow or
blocked rotating pick can never break real crawling — glibc falls through to the
fallback within two seconds.

Talks to the Docker Engine API directly over the unix socket (no docker CLI in
the image). Runs as a trusted infra sidecar (like autoheal); never raises out of
its loop.
"""
import os
import re
import json
import time
import random
import socket
import logging
import http.client
from urllib.parse import quote

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S')
logger = logging.getLogger('dns-rotator')

ENABLED = os.getenv('DNS_ROTATE_ENABLED', 'true').lower() == 'true'
INTERVAL = int(os.getenv('ROTATE_INTERVAL_SECS', '90'))
FALLBACK_DNS = os.getenv('FALLBACK_DNS', '1.1.1.1')
NODE_CONTAINERS = [c.strip() for c in os.getenv(
    'NODE_CONTAINERS',
    'adnauseam-node-chrome,adnauseam-node-firefox,adnauseam-node-edge'
).split(',') if c.strip()]
POOL_PATH = os.getenv('DNS_POOL_PATH', '/app/crawler/dns_resolvers.json')
DOCKER_SOCK = os.getenv('DOCKER_SOCK', '/var/run/docker.sock')

_IPV4 = re.compile(r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$')


def _is_ipv4(s):
    m = _IPV4.match(s or '')
    return bool(m) and all(0 <= int(x) <= 255 for x in m.groups())


class _UHTTP(http.client.HTTPConnection):
    """HTTPConnection over a unix domain socket."""
    def __init__(self, sockpath):
        super().__init__('localhost')
        self._sockpath = sockpath

    def connect(self):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(15)
        s.connect(self._sockpath)
        self.sock = s


def _api(method, url, body=None):
    conn = _UHTTP(DOCKER_SOCK)
    try:
        payload = json.dumps(body).encode() if body is not None else None
        headers = {'Content-Type': 'application/json'} if body is not None else {}
        conn.request(method, url, body=payload, headers=headers)
        resp = conn.getresponse()
        data = resp.read()
        return resp.status, data
    finally:
        conn.close()


def _container_id(name):
    """Resolve a running container's id from its name (None if not found)."""
    flt = json.dumps({'name': [name], 'status': ['running']})
    status, data = _api('GET', '/containers/json?filters=' + quote(flt))
    if status != 200:
        return None
    for c in json.loads(data or b'[]'):
        for nm in c.get('Names', []):
            if nm.lstrip('/') == name:
                return c['Id']
    return None


def _exec(cid, cmd):
    """Run cmd (list) inside container cid via the Docker exec API."""
    status, data = _api('POST', '/containers/%s/exec' % cid,
                        {'AttachStdout': False, 'AttachStderr': False, 'Cmd': cmd})
    if status != 201:
        return False, 'create exec HTTP %s' % status
    exec_id = json.loads(data)['Id']
    status, _ = _api('POST', '/exec/%s/start' % exec_id, {'Detach': True, 'Tty': False})
    return status in (200, 201), 'start HTTP %s' % status


def _write_resolv(cid, primary):
    content = ('nameserver %s\nnameserver %s\noptions timeout:2 attempts:1 rotate\n'
               % (primary, FALLBACK_DNS))
    # `>` truncates the bind-mounted resolv.conf inode in place (allowed); we do NOT
    # move/replace the file, which Docker forbids on that bind mount.
    cmd = ['sh', '-c', 'printf %s > /etc/resolv.conf' % _shquote(content)]
    return _exec(cid, cmd)


def _shquote(s):
    return "'" + s.replace("'", "'\\''") + "'"


def load_pool():
    """Return a weight-expanded list of validated resolver IPs."""
    try:
        with open(POOL_PATH, encoding='utf-8') as fh:
            data = json.load(fh)
    except Exception as e:
        logger.warning('could not read pool %s: %s — using fallback only', POOL_PATH, str(e)[:80])
        return []
    expanded = []
    prio = 0
    for r in data.get('resolvers', []):
        ip = r.get('ip')
        if not _is_ipv4(ip) or ip == FALLBACK_DNS:
            continue
        w = int(r.get('weight', 1))
        expanded.extend([ip] * max(1, w))
        if r.get('priority'):
            prio += 1
    logger.info('loaded %d resolvers (%d in priority countries), weight-expanded to %d picks',
                len({x for x in expanded}), prio, len(expanded))
    return expanded


def main():
    if not ENABLED:
        logger.info('DNS_ROTATE_ENABLED=false — sidecar idle')
        while True:
            time.sleep(3600)
    logger.info('dns-rotator up: interval=%ss fallback=%s nodes=%s',
                INTERVAL, FALLBACK_DNS, ','.join(NODE_CONTAINERS))
    pool = load_pool()
    reload_every = max(1, int(3600 / max(INTERVAL, 1)))  # reload the pool ~hourly
    cycle = 0
    while True:
        try:
            if pool:
                for node in NODE_CONTAINERS:
                    cid = _container_id(node)
                    if not cid:
                        continue
                    primary = random.choice(pool)  # different pick per node per cycle
                    ok, why = _write_resolv(cid, primary)
                    if ok:
                        logger.info('%s -> nameserver %s (fallback %s)', node, primary, FALLBACK_DNS)
                    else:
                        logger.warning('%s: resolv.conf update failed (%s)', node, why)
            else:
                logger.warning('empty resolver pool — leaving node DNS untouched this cycle')
            cycle += 1
            if cycle % reload_every == 0:
                pool = load_pool() or pool
        except Exception as e:
            logger.warning('rotation cycle error: %s', str(e)[:120])
        time.sleep(INTERVAL)


if __name__ == '__main__':
    main()
