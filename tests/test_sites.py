"""Tests for crawler.sites URL helpers and website loading.

These import the crawler package at module level to prove that importing it
requires no running Selenium Grid / browser (all side effects are lazy).
"""
from crawler import sites


class TestGetDomain:
    def test_basic_https(self):
        assert sites.get_domain("https://example.com/path?q=1") == "example.com"

    def test_http(self):
        assert sites.get_domain("http://example.com") == "example.com"

    def test_subdomain(self):
        assert sites.get_domain("https://www.sub.example.co.uk/page") == "www.sub.example.co.uk"

    def test_lowercases_host(self):
        assert sites.get_domain("https://Example.COM/Path") == "example.com"

    def test_port_is_kept_in_netloc(self):
        assert sites.get_domain("http://localhost:8080/x") == "localhost:8080"

    def test_userinfo_and_port(self):
        assert sites.get_domain("http://user:pass@Host.EXAMPLE.com:443/") == "user:pass@host.example.com:443"

    def test_no_scheme_returns_empty_netloc(self):
        # Without a scheme urlparse treats the whole thing as a path -> empty netloc.
        assert sites.get_domain("example.com/path") == ""

    def test_empty_string(self):
        assert sites.get_domain("") == ""

    def test_non_string_input_does_not_raise(self):
        # Bad input must be handled gracefully: return an empty/falsy value
        # rather than raising (urlparse may yield a bytes empty for None).
        assert not sites.get_domain(None)
        assert not sites.get_domain(12345)


class TestIsSafeUrl:
    def test_accepts_http(self):
        assert sites.is_safe_url("http://example.com") is True

    def test_accepts_https(self):
        assert sites.is_safe_url("https://example.com/a/b?c=d") is True

    def test_accepts_with_leading_whitespace(self):
        assert sites.is_safe_url("   https://example.com") is True

    def test_scheme_case_insensitive(self):
        assert sites.is_safe_url("HTTPS://example.com") is True

    def test_rejects_file(self):
        assert sites.is_safe_url("file:///etc/passwd") is False

    def test_rejects_data(self):
        assert sites.is_safe_url("data:text/html,<h1>x</h1>") is False

    def test_rejects_chrome(self):
        assert sites.is_safe_url("chrome://settings") is False

    def test_rejects_about(self):
        assert sites.is_safe_url("about:blank") is False

    def test_rejects_javascript(self):
        assert sites.is_safe_url("javascript:alert(1)") is False

    def test_rejects_ftp_and_blob(self):
        assert sites.is_safe_url("ftp://example.com") is False
        assert sites.is_safe_url("blob:https://example.com/uuid") is False

    def test_rejects_empty_and_none(self):
        assert sites.is_safe_url("") is False
        assert sites.is_safe_url(None) is False

    def test_rejects_non_string(self):
        assert sites.is_safe_url(123) is False
        assert sites.is_safe_url(["http://example.com"]) is False


class TestLoadWebsites:
    def test_loads_and_filters_comments_and_blanks(self, tmp_path):
        f = tmp_path / "websites.txt"
        f.write_text(
            "# a comment\n"
            "https://example.com\n"
            "\n"
            "   \n"
            "https://another.com  \n"
            "# trailing comment\n",
            encoding="utf-8",
        )
        result = sites.load_websites(str(f))
        assert result == ["https://example.com", "https://another.com"]

    def test_fallback_when_file_missing(self, tmp_path):
        missing = tmp_path / "does_not_exist.txt"
        result = sites.load_websites(str(missing))
        # Fallback list is non-empty and all entries are http(s) URLs.
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(url.startswith("http") for url in result)
