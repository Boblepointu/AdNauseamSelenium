#!/usr/bin/env python3
"""Build the noise domain corpus used by the injected noise engine.

This standalone script is executed by the Docker entrypoint (NOT imported by
the ``crawler`` package and NOT run during pytest). It downloads category
files from the pi-hole ``blocklistproject/Lists`` project (ad / tracker /
malware / fraud / phishing / scam / ransomware / redirect lists), parses the
hosts-format entries into plain domains, merges them with the bundled seed
file, deduplicates, and writes the result atomically to ``NOISE_CORPUS_PATH``.

A freshness guard lets many container replicas start without every one of them
re-fetching the lists: if the target already exists, is non-trivially large and
younger than ``NOISE_CORPUS_MAX_AGE_DAYS``, the script exits 0 immediately.

Safety note: the corpus intentionally contains malware/phishing domains. It is
consumed ONLY by non-executing request primitives (fetch no-cors, Image, etc.)
and those domains are never navigated to. This script merely assembles the
list; it does not contact any of the listed domains.
"""

import logging
import os
import sys
import time
import urllib.request

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
)
logger = logging.getLogger('build_noise_corpus')

# ---- Configuration (env-driven, stdlib-only) --------------------------------
NOISE_CORPUS_PATH = os.getenv('NOISE_CORPUS_PATH', '/data/noise/noise_domains.txt')
NOISE_SEED_PATH = os.getenv('NOISE_SEED_PATH', '/app/crawler/noise_seed.txt')
NOISE_CORPUS_MAX_AGE_DAYS = float(os.getenv('NOISE_CORPUS_MAX_AGE_DAYS', '7'))
NOISE_FETCH_TIMEOUT = float(os.getenv('NOISE_FETCH_TIMEOUT', '30'))

# Minimum line count for an existing corpus to be considered "good enough" to
# skip a rebuild. Below this we assume it is a partial/corrupt write.
MIN_CORPUS_LINES = 1000

# blocklistproject/Lists categories to pull. Ad + tracker to fill the corpus,
# plus the malware/fraud/phishing/scam/ransomware families for full-spectrum
# noise targeting.
BLOCKLIST_CATEGORIES = (
    'ads',
    'tracking',
    'malware',
    'fraud',
    'phishing',
    'scam',
    'ransomware',
    'redirect',
)
BLOCKLIST_URL_TEMPLATE = (
    'https://raw.githubusercontent.com/blocklistproject/Lists/master/{category}.txt'
)

USER_AGENT = (
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
)

# Sentinel/placeholder hostnames that appear in hosts files and must never be
# treated as real noise domains.
_SKIP_HOSTS = frozenset((
    'localhost',
    'localhost.localdomain',
    'local',
    'broadcasthost',
    'ip6-localhost',
    'ip6-loopback',
    'ip6-localnet',
    'ip6-mcastprefix',
    'ip6-allnodes',
    'ip6-allrouters',
    'ip6-allhosts',
    '0.0.0.0',
    '127.0.0.1',
    '255.255.255.255',
))


def _is_plausible_domain(token):
    """Return True if ``token`` looks like a bare registrable domain.

    Requires a dot, rejects anything with whitespace, a URL scheme, a path or
    obvious junk. Kept deliberately permissive (we do not validate TLDs) since
    the consumer only ever fires non-executing requests at these names.
    """
    if not token or '.' not in token:
        return False
    if token in _SKIP_HOSTS:
        return False
    # No whitespace, no scheme, no path/query fragments, no wildcards.
    for bad in (' ', '\t', '/', '\\', '://', '?', '#', '*', '@', ':'):
        if bad in token:
            return False
    # A domain cannot start or end with a dot or hyphen.
    if token[0] in '.-' or token[-1] in '.-':
        return False
    return True


def parse_hosts_lines(iterable):
    """Parse hosts-format / bare-domain lines into a set of clean domains.

    Pure and I/O-free so tests can exercise it directly. Handles:
      * ``0.0.0.0 domain.com`` and ``127.0.0.1 domain.com`` hosts entries
      * bare ``domain.com`` lines
      * inline trailing comments (``domain.com # note``)
    Skips blank lines, comments (starting with ``#`` or ``!``), and
    localhost/broadcast/sentinel entries. Everything is lowercased and stripped.
    """
    domains = set()
    for raw in iterable:
        line = raw.strip()
        if not line or line[0] in '#!':
            continue
        # Drop inline comments.
        for marker in ('#', '!'):
            idx = line.find(marker)
            if idx != -1:
                line = line[:idx].strip()
        if not line:
            continue
        parts = line.split()
        # Hosts format: "<ip> <domain> [<domain> ...]"; take the trailing
        # tokens. Bare "domain.com" also handled (single token).
        if len(parts) >= 2:
            candidates = parts[1:]
        else:
            candidates = parts[:1]
        for token in candidates:
            token = token.strip().lower().rstrip('.')
            if _is_plausible_domain(token):
                domains.add(token)
    return domains


def fetch_url(url, timeout=NOISE_FETCH_TIMEOUT):
    """Fetch ``url`` and return its decoded text, or None on any failure.

    Best-effort: network errors are logged and swallowed so a flaky mirror
    never crashes the container.
    """
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            raw = resp.read()
        return raw.decode('utf-8', errors='replace')
    except Exception as exc:
        logger.warning('Failed to fetch %s: %s', url, exc)
        return None


def load_seed_domains(seed_path):
    """Load and parse the bundled seed file; empty set if it is missing."""
    if not seed_path or not os.path.exists(seed_path):
        logger.info('No seed file at %s (skipping seed merge)', seed_path)
        return set()
    try:
        with open(seed_path, encoding='utf-8', errors='replace') as fh:
            domains = parse_hosts_lines(fh)
        logger.info('Loaded %d domain(s) from seed %s', len(domains), seed_path)
        return domains
    except Exception as exc:
        logger.warning('Failed to read seed %s: %s', seed_path, exc)
        return set()


def corpus_is_fresh(path, max_age_days, min_lines=MIN_CORPUS_LINES):
    """Return True if ``path`` is a large-enough, recent-enough corpus.

    Used so that when several replicas boot at once, only a stale/missing
    corpus triggers a rebuild.
    """
    if not os.path.exists(path):
        return False
    try:
        age_seconds = time.time() - os.path.getmtime(path)
        if age_seconds > max_age_days * 86400:
            logger.info(
                'Corpus %s is %.1f days old (max %.1f); rebuilding',
                path, age_seconds / 86400, max_age_days,
            )
            return False
        line_count = 0
        with open(path, encoding='utf-8', errors='replace') as fh:
            for line_count, _ in enumerate(fh, start=1):
                if line_count >= min_lines:
                    break
        if line_count < min_lines:
            logger.info(
                'Corpus %s has only %d line(s) (< %d); rebuilding',
                path, line_count, min_lines,
            )
            return False
        return True
    except Exception as exc:
        logger.warning('Could not stat corpus %s: %s', path, exc)
        return False


def write_corpus_atomic(path, domains):
    """Write ``domains`` (sorted) to ``path`` atomically via a temp + replace."""
    directory = os.path.dirname(path) or '.'
    os.makedirs(directory, exist_ok=True)
    tmp_path = '{0}.tmp.{1}'.format(path, os.getpid())
    try:
        with open(tmp_path, 'w', encoding='utf-8') as fh:
            for domain in sorted(domains):
                fh.write(domain)
                fh.write('\n')
        os.replace(tmp_path, path)
    except Exception:
        # Clean up the partial temp file on failure.
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
        raise


def build_corpus():
    """Fetch, parse, merge and write the corpus. Returns the exit code."""
    if corpus_is_fresh(NOISE_CORPUS_PATH, NOISE_CORPUS_MAX_AGE_DAYS):
        logger.info(
            'Corpus %s is fresh and large enough; skipping rebuild',
            NOISE_CORPUS_PATH,
        )
        return 0

    all_domains = set()
    for category in BLOCKLIST_CATEGORIES:
        url = BLOCKLIST_URL_TEMPLATE.format(category=category)
        text = fetch_url(url)
        if text is None:
            continue
        parsed = parse_hosts_lines(text.splitlines())
        logger.info('Fetched %-10s: %d domain(s) from %s', category, len(parsed), url)
        all_domains |= parsed

    seed_domains = load_seed_domains(NOISE_SEED_PATH)
    all_domains |= seed_domains

    if not all_domains:
        logger.warning(
            'No domains collected (network down and no seed?); leaving %s untouched',
            NOISE_CORPUS_PATH,
        )
        return 0

    write_corpus_atomic(NOISE_CORPUS_PATH, all_domains)
    logger.info(
        'Wrote %d unique domain(s) to %s (%d from seed)',
        len(all_domains), NOISE_CORPUS_PATH, len(seed_domains),
    )
    return 0


if __name__ == '__main__':
    try:
        sys.exit(build_corpus())
    except Exception as exc:
        # Never crash the container entrypoint on a corpus-build hiccup.
        logger.error('build_noise_corpus failed: %s', exc)
        sys.exit(0)
