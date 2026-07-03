"""Shared configuration, constants and mutable runtime state for the crawler.

This module is the single source of truth for state that is shared across the
split crawler modules. Constants are read once at import time; mutable holders
(``persona_manager``, ``sites``, ``fatigue_model``) are populated at runtime by
the orchestrator and referenced elsewhere as ``config.<name>`` so that
reassignment is visible to every importer.
"""

import os
import logging

logger = logging.getLogger('crawler.config')

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
