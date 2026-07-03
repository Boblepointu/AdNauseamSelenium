"""Tests for crawler.fingerprint generators.

Sampling-based: each generator is called many times and we assert on the
documented keys/types and internally-consistent value ranges/sets rather than
exact values (the generators are intentionally random).
"""
import random

from crawler import fingerprint

SAMPLES = 300


class TestGenerateRandomHardware:
    def test_keys_and_types(self):
        random.seed(1)
        for _ in range(SAMPLES):
            hw = fingerprint.generate_random_hardware()
            assert set(hw.keys()) == {"hardwareConcurrency", "deviceMemory", "maxTouchPoints"}
            assert isinstance(hw["hardwareConcurrency"], int)
            assert isinstance(hw["deviceMemory"], int)
            assert isinstance(hw["maxTouchPoints"], int)

    def test_value_ranges(self):
        random.seed(2)
        allowed_memory = {4, 8, 16, 32, 64}
        for _ in range(SAMPLES):
            hw = fingerprint.generate_random_hardware()
            assert hw["hardwareConcurrency"] > 0
            assert hw["deviceMemory"] in allowed_memory
            assert hw["maxTouchPoints"] >= 0


class TestGenerateRandomConnection:
    def test_keys_and_types(self):
        random.seed(3)
        for _ in range(SAMPLES):
            conn = fingerprint.generate_random_connection()
            assert set(conn.keys()) == {"effectiveType", "rtt", "downlink", "saveData"}
            assert isinstance(conn["effectiveType"], str)
            assert isinstance(conn["rtt"], int)
            assert isinstance(conn["downlink"], float)
            assert isinstance(conn["saveData"], bool)

    def test_value_ranges(self):
        random.seed(4)
        for _ in range(SAMPLES):
            conn = fingerprint.generate_random_connection()
            assert conn["effectiveType"] in {"slow-2g", "2g", "3g", "4g", "5g"}
            assert conn["rtt"] > 0
            assert conn["downlink"] > 0


class TestGenerateRandomScreen:
    def test_keys(self):
        screen = fingerprint.generate_random_screen()
        expected = {
            "width", "height", "availWidth", "availHeight",
            "colorDepth", "pixelDepth", "devicePixelRatio", "orientation",
        }
        assert set(screen.keys()) == expected

    def test_internally_consistent(self):
        random.seed(5)
        for _ in range(SAMPLES):
            s = fingerprint.generate_random_screen()
            assert s["width"] > 0 and s["height"] > 0
            assert s["width"] >= 1024 and s["height"] >= 768
            # Available area never exceeds the physical screen.
            assert s["availWidth"] <= s["width"]
            assert s["availHeight"] <= s["height"]
            assert s["colorDepth"] in {24, 30, 32}
            assert s["pixelDepth"] == s["colorDepth"]
            assert 1.0 <= s["devicePixelRatio"] <= 3.0
            assert s["orientation"] == "landscape-primary"


class TestGenerateRandomLanguage:
    def test_returns_nonempty_accept_language_string(self):
        random.seed(6)
        for _ in range(SAMPLES):
            lang = fingerprint.generate_random_language()
            assert isinstance(lang, str)
            assert len(lang) > 0
            # Accept-Language style: comma-separated tokens, first is a lang tag.
            first = lang.split(",")[0].split(";")[0]
            assert "-" in first or first.isalpha()


class TestGenerateRandomBattery:
    def test_keys_and_ranges(self):
        random.seed(7)
        for _ in range(SAMPLES):
            bat = fingerprint.generate_random_battery()
            assert set(bat.keys()) == {"charging", "chargingTime", "dischargingTime", "level"}
            assert isinstance(bat["charging"], bool)
            assert 0.0 <= bat["level"] <= 1.0


class TestGenerateRandomUserAgent:
    def test_chrome_family(self):
        random.seed(10)
        for _ in range(SAMPLES):
            ua = fingerprint.generate_random_user_agent("chrome")
            assert ua.startswith("Mozilla/5.0")
            # A Chromium UA must never advertise Firefox or the Edge token.
            assert "Firefox" not in ua
            assert "Edg/" not in ua
            # Chrome token on desktop/Android, CriOS on iOS.
            assert ("Chrome/" in ua) or ("CriOS/" in ua)

    def test_chromium_family_matches_chrome_engine(self):
        random.seed(11)
        for _ in range(SAMPLES):
            ua = fingerprint.generate_random_user_agent("chromium")
            assert "Firefox" not in ua
            assert "Edg/" not in ua
            assert ("Chrome/" in ua) or ("CriOS/" in ua)

    def test_firefox_family(self):
        random.seed(12)
        for _ in range(SAMPLES):
            ua = fingerprint.generate_random_user_agent("firefox")
            assert ua.startswith("Mozilla/5.0")
            assert "Firefox/" in ua
            assert "Gecko" in ua
            # Firefox is not the Chromium/Edge engine.
            assert "Edg/" not in ua
            assert "Chrome/" not in ua

    def test_edge_family(self):
        random.seed(13)
        for _ in range(SAMPLES):
            ua = fingerprint.generate_random_user_agent("edge")
            assert ua.startswith("Mozilla/5.0")
            # Edge carries the Edg/ token on top of a Chromium base.
            assert "Edg/" in ua
            assert "Chrome/" in ua
            assert "Firefox" not in ua

    def test_none_defaults_to_chrome_engine(self):
        random.seed(14)
        ua = fingerprint.generate_random_user_agent(None)
        assert "Firefox" not in ua
        assert "Edg/" not in ua
