"""Shared configuration, constants and mutable runtime state for the crawler.

This module is the single source of truth for state that is shared across the
split crawler modules. Constants are read once at import time; mutable holders
(``persona_manager``, ``sites``, ``fatigue_model``) are populated at runtime by
the orchestrator and referenced elsewhere as ``config.<name>`` so that
reassignment is visible to every importer.
"""

import os
import time
import logging
from collections import Counter

logger = logging.getLogger('crawler.config')


def touch_heartbeat():
    """Write the liveness heartbeat file. Called from the browse loop AND from
    every recovery step (probe, session recreation, driver retries) so that a
    slow-but-progressing recovery is never mistaken for a hang by the container
    healthcheck / autoheal.
    """
    try:
        with open(os.getenv('HEARTBEAT_FILE', '/tmp/crawler_heartbeat'), 'w') as _hb:
            _hb.write(str(time.time()))
    except Exception:
        pass

# Cumulative runtime metrics, shared across modules. Incremented in place
# (e.g. ``config.STATS['ads_clicked'] += 1``) and periodically summarized by
# the orchestrator so an operator can see success/skip/error rates per process.
STATS = Counter()

# Import persona manager for persistent fingerprint rotation.
try:
    from persona_manager import PersonaManager, fingerprint_to_dict
    PERSONA_MANAGER_AVAILABLE = True
except ImportError:
    logger.warning('PersonaManager not available, running without persistence')
    PersonaManager = None
    fingerprint_to_dict = None
    PERSONA_MANAGER_AVAILABLE = False

# Run a driver health check every N successfully-visited websites.
HEALTH_CHECK_INTERVAL = 5

# Weighted browser pool: relative share reflects real-world market usage.
browsers = (
    ['chrome'] * 40 +      # 40% - Most popular browser
    ['firefox'] * 30 +     # 30% - Second most popular
    ['edge'] * 20 +        # 20% - Growing market share
    ['chromium'] * 10      # 10% - Open-source variant for extra diversity
)

# Persona rotation configuration from environment.
PERSONA_ROTATION_STRATEGY = os.getenv('PERSONA_ROTATION_STRATEGY', 'weighted')
PERSONA_MAX_AGE_DAYS = int(os.getenv('PERSONA_MAX_AGE_DAYS', '30'))
PERSONA_MAX_USES = int(os.getenv('PERSONA_MAX_USES', '100'))

# ---- Mutable runtime state (populated by orchestrator.setup()/browse()) ----
# Global persona manager instance. Lazily created by setup() so that merely
# importing this package does not construct the manager or touch its storage.
persona_manager = None

# Site list. Populated by setup(); empty at import time so importing this
# package never reads websites.txt from disk.
sites = []

# Per-session fatigue model. Created by browse() at the start of each session
# and consumed by humanize.realistic_delay().
fatigue_model = None
