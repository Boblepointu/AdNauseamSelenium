"""Website list loading and URL helpers (split from crawl.py)."""
import logging
from urllib.parse import urlparse

logger = logging.getLogger('crawler.sites')


def load_websites(file_path='/app/websites.txt'):
    """Load websites from a text file, ignoring comments and empty lines"""
    websites = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    websites.append(line)
        
        logger.info(f'✓ Loaded {len(websites)} websites from {file_path}')
        return websites
    except FileNotFoundError:
        logger.warning(f'⚠ Warning: {file_path} not found, using fallback websites')
        # Fallback to a minimal list if file not found
        return [
            "https://google.com", "https://bing.com", "https://yahoo.com",
            "https://cnn.com", "https://bbc.com", "https://forbes.com"
        ]
    except Exception as e:
        logger.warning(f'⚠ Error loading websites: {e}')
        return [
            "https://google.com", "https://bing.com", "https://yahoo.com"
        ]


def get_domain(url):
    """Extract domain from URL"""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return ''


def is_safe_url(url):
    """Return True only for http/https URLs.

    Rejects file://, data:, chrome://, about:, javascript:, ftp:, blob:, etc. so a
    poisoned website list entry cannot make the browser read local files or hit
    privileged internal pages.
    """
    try:
        if not url or not isinstance(url, str):
            return False
        scheme = urlparse(url.strip()).scheme.lower()
        return scheme in ('http', 'https')
    except Exception:
        return False
