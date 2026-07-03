#!/usr/bin/env python3
"""
Browser Chaos Generator with Advanced Anti-Fingerprinting

Thin entry shim. The implementation now lives in the ``crawler`` package;
this module preserves the Docker entrypoint contract ("python3 -u /app/crawl.py").
"""

from crawler.orchestrator import main

if __name__ == '__main__':
    main()
