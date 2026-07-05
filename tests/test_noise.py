"""Tests for the AdNauseam-style noise feature.

These exercise only pure, in-memory helpers — nothing here touches the network,
a Selenium driver, or the real blocklist corpus. Module-level imports prove the
package (and the standalone corpus builder) load without a browser or network.

Contract under test (agreed with the integrator):
  * ``build_noise_corpus.parse_hosts_lines(lines) -> set[str]``
  * ``crawler.noise.sample_domains(n) -> list[str]`` (samples module pool ``_POOL``)
  * ``crawler.noise.build_injection(domains, cfg) -> str``
  * ``crawler.noise.clean_hostnames(urls) -> set[str]``
"""
import json
import os
import sys

import pytest

# Mirror the repo-root-on-path trick used by the pytest config so that both a
# bare ``pytest`` run and a direct ``python tests/test_noise.py`` can import the
# top-level corpus builder that lives beside the package (not inside it).
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import build_noise_corpus  # noqa: E402  (import after sys.path shim)
from crawler import noise  # noqa: E402


class TestParseHostsLines:
    """The pi-hole/blocklist hosts parser keeps only real domains."""

    def test_mixed_lines(self):
        lines = [
            "0.0.0.0 evil.com",
            "127.0.0.1 tracker.net",
            "# comment",
            "",
            "bare-domain.org",
            "0.0.0.0 localhost",
        ]
        assert build_noise_corpus.parse_hosts_lines(lines) == {
            "evil.com",
            "tracker.net",
            "bare-domain.org",
        }

    def test_returns_a_set(self):
        assert isinstance(build_noise_corpus.parse_hosts_lines([]), set)

    def test_localhost_and_comments_and_blanks_excluded(self):
        lines = [
            "# header comment",
            "   ",
            "0.0.0.0 localhost",
            "127.0.0.1 localhost",
            "\t",
        ]
        assert build_noise_corpus.parse_hosts_lines(lines) == set()

    def test_deduplicates(self):
        lines = ["0.0.0.0 dup.com", "dup.com", "127.0.0.1 dup.com"]
        assert build_noise_corpus.parse_hosts_lines(lines) == {"dup.com"}


class TestSampleDomains:
    """``sample_domains`` draws from the module pool without ever raising."""

    def test_returns_subset_of_pool(self, monkeypatch):
        pool = ["a.com", "b.net", "c.org", "d.io", "e.co"]
        monkeypatch.setattr(noise, "_POOL", list(pool))
        picked = noise.sample_domains(3)
        assert len(picked) <= 3
        assert set(picked) <= set(pool)

    def test_all_items_from_pool_over_many_draws(self, monkeypatch):
        pool = ["a.com", "b.net", "c.org", "d.io", "e.co"]
        monkeypatch.setattr(noise, "_POOL", list(pool))
        for _ in range(200):
            for d in noise.sample_domains(4):
                assert d in pool

    def test_n_larger_than_pool_does_not_raise(self, monkeypatch):
        pool = ["only.com", "two.net"]
        monkeypatch.setattr(noise, "_POOL", list(pool))
        picked = noise.sample_domains(50)
        assert set(picked) <= set(pool)
        assert len(picked) <= 50

    def test_empty_pool_returns_empty(self, monkeypatch):
        monkeypatch.setattr(noise, "_POOL", [])
        picked = noise.sample_domains(10)
        assert list(picked) == []

    def test_zero_request_is_empty(self, monkeypatch):
        monkeypatch.setattr(noise, "_POOL", ["a.com", "b.net"])
        assert list(noise.sample_domains(0)) == []


class TestBuildInjection:
    """The injected string sets ``window.__NOISE`` then appends the engine."""

    DOMAINS = ["ads.evil.com", "track.example.net", "malware.bad.io"]
    CFG = {
        "ratio": 10,
        "maxConcurrency": 10,
        "sampleRefreshMs": 15000,
        "enabled": True,
    }

    def _payload(self, injection):
        # The payload is a single JSON line: ``window.__NOISE=<json>;`` followed
        # by a newline and the engine source. Recover it robustly.
        prefix = "window.__NOISE="
        assert injection.startswith(prefix)
        first_line = injection.split("\n", 1)[0]
        json_text = first_line[len(prefix):].rstrip()
        assert json_text.endswith(";")
        return json.loads(json_text[:-1])

    def test_starts_with_noise_assignment(self):
        out = noise.build_injection(self.DOMAINS, self.CFG)
        assert out.startswith("window.__NOISE=")

    def test_payload_contains_domains_and_config(self):
        out = noise.build_injection(self.DOMAINS, self.CFG)
        payload = self._payload(out)
        assert set(payload["domains"]) == set(self.DOMAINS)
        assert payload["config"] == self.CFG

    def test_domains_appear_in_emitted_json(self):
        out = noise.build_injection(self.DOMAINS, self.CFG)
        json_line = out.split("\n", 1)[0]
        for d in self.DOMAINS:
            assert d in json_line

    def test_engine_source_follows_the_assignment(self):
        out = noise.build_injection(self.DOMAINS, self.CFG)
        marker = "window.__noiseEngineActive"
        assert marker in out
        # The engine (and its double-start guard) come after the assignment.
        assert out.index(marker) > out.index("window.__NOISE=")

    def test_empty_domains_still_valid(self):
        out = noise.build_injection([], self.CFG)
        payload = self._payload(out)
        assert payload["domains"] == []
        assert "window.__noiseEngineActive" in out


class TestCleanHostnames:
    """Harvest helper: resource URLs -> lowercase http(s) hostnames only."""

    def test_keeps_http_https_drops_the_rest(self):
        urls = [
            "https://good.example.com/path?q=1",
            "http://tracker.net/beacon.gif",
            "https://sub.domain.org/",
            "HTTPS://UPPER.EXAMPLE.COM/x",
            "ftp://files.example.com/x",
            "data:text/html,<h1>x</h1>",
            "javascript:alert(1)",
            "about:blank",
            "chrome://settings",
            "blob:https://good.example.com/uuid",
            "not-a-real-url",
            "",
            None,
        ]
        assert noise.clean_hostnames(urls) == {
            "good.example.com",
            "tracker.net",
            "sub.domain.org",
            "upper.example.com",
        }

    def test_returns_a_set(self):
        assert isinstance(noise.clean_hostnames([]), set)

    def test_non_http_schemes_excluded(self):
        bad = ["ftp://a.com", "data:x", "javascript:void(0)", "about:blank", "file:///etc/passwd"]
        assert noise.clean_hostnames(bad) == set()

    def test_malformed_and_none_do_not_raise(self):
        junk = [None, "", "   ", "http://", "https://", "://nohost", 12345]
        # Must return cleanly without raising; no usable hostnames here.
        assert noise.clean_hostnames(junk) == set()


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
