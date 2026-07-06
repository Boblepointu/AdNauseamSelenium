"""Tests for network-wide OPNsense DNS rotation (``opnsense`` + ``net_dns_rotator``).

These exercise only pure, in-memory helpers and a fully MOCKED ``urlopen`` — nothing
here touches the network, the real router, or any live credential. Module-level
imports prove both modules load without a router or the ``requests`` package.

Contract under test (a hard contract with the modules):
  * ``opnsense.ensure_fallback(ips, fallback, cap=...) -> list[str]`` — dedups,
    always includes the fallback, caps length (fallback survives the cap).
  * ``opnsense.build_unbound_forward_payload(ip) -> dict`` — the add_forward body.
  * ``opnsense.OPNsenseClient`` — ``get_dns_state`` / ``set_forwarders`` drive the
    expected HTTP requests and NEVER raise on HTTP/transport errors.
  * ``net_dns_rotator.pick_subset(n, exclude_fallback, pool) -> list[str]`` —
    distinct, weighted, bounded, and excludes the fallback.
  * ``net_dns_rotator.run_cycle`` — the DRY_RUN path applies NOTHING.
"""
import json
import os
import sys
from unittest.mock import MagicMock

import pytest

# Mirror the repo-root-on-path shim used by the other test modules so both a bare
# ``pytest`` run (CI) and a direct ``python tests/test_net_dns.py`` can import the
# top-level modules that live beside the crawler package (not inside it).
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import opnsense  # noqa: E402  (import after sys.path shim)
import net_dns_rotator  # noqa: E402


# --------------------------------------------------------------------------- #
#  Fake HTTP layer — a drop-in for ``urllib.request.urlopen``.
# --------------------------------------------------------------------------- #
class _FakeResp:
    """Minimal context-manager response with ``.read()`` + ``.status``."""

    def __init__(self, payload, status=200):
        self._body = json.dumps(payload).encode() if payload is not None else b""
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._body

    def getcode(self):
        return self.status


class _Recorder:
    """A fake ``urlopen`` that records Requests and answers by URL suffix.

    ``routes`` maps a path suffix -> payload dict (or a callable(req) -> payload).
    Unmatched paths get ``{}`` / 200. Set ``raise_http`` to force an HTTPError on
    every call (to prove the client never raises).
    """

    def __init__(self, routes=None, raise_http=False):
        self.routes = routes or {}
        self.raise_http = raise_http
        self.calls = []  # list of (method, url, parsed_body)

    def __call__(self, req, timeout=None, context=None):
        import urllib.error

        body = None
        if getattr(req, "data", None):
            try:
                body = json.loads(req.data.decode())
            except (ValueError, TypeError):
                body = req.data
        self.calls.append((req.get_method(), req.full_url, body))

        if self.raise_http:
            raise urllib.error.HTTPError(req.full_url, 500, "boom", {}, None)

        for suffix, payload in self.routes.items():
            if req.full_url.endswith(suffix):
                if callable(payload):
                    payload = payload(req)
                return _FakeResp(payload, 200)
        return _FakeResp({}, 200)

    def paths(self):
        return [url for _method, url, _body in self.calls]


def _client(**overrides):
    cfg = {
        "url": "https://router.test",
        "api_key": "k",
        "api_secret": "s",
        "verify_tls": False,
        "marker": "adnauseam-netrot",
        "fallback": "1.1.1.1",
        "subset_max": 8,
        "snapshot_path": "",  # empty => snapshot never persisted to disk in tests
    }
    cfg.update(overrides)
    return opnsense.OPNsenseClient(cfg)


# --------------------------------------------------------------------------- #
#  ensure_fallback — pure helper
# --------------------------------------------------------------------------- #
class TestEnsureFallback:
    def test_appends_fallback_when_absent(self):
        out = opnsense.ensure_fallback(["8.8.8.8", "9.9.9.9"], "1.1.1.1")
        assert "1.1.1.1" in out
        assert out[:2] == ["8.8.8.8", "9.9.9.9"]

    def test_does_not_duplicate_existing_fallback(self):
        out = opnsense.ensure_fallback(["1.1.1.1", "8.8.8.8"], "1.1.1.1")
        assert out.count("1.1.1.1") == 1

    def test_dedups_preserving_order(self):
        out = opnsense.ensure_fallback(["8.8.8.8", "8.8.8.8", "9.9.9.9"], "1.1.1.1")
        assert out == ["8.8.8.8", "9.9.9.9", "1.1.1.1"]

    def test_empty_input_yields_fallback_only(self):
        assert opnsense.ensure_fallback([], "1.1.1.1") == ["1.1.1.1"]

    def test_caps_length_and_fallback_always_survives(self):
        ips = ["10.0.0.%d" % i for i in range(20)]  # 20 non-fallback picks
        out = opnsense.ensure_fallback(ips, "1.1.1.1", cap=5)
        assert len(out) == 5
        assert "1.1.1.1" in out  # the cap must never evict the fallback

    def test_cap_keeps_fallback_when_it_was_already_present(self):
        ips = ["1.1.1.1"] + ["10.0.0.%d" % i for i in range(20)]
        out = opnsense.ensure_fallback(ips, "1.1.1.1", cap=3)
        assert len(out) == 3
        assert "1.1.1.1" in out

    def test_drops_non_string_and_empty_entries(self):
        out = opnsense.ensure_fallback(["8.8.8.8", "", None, 123], "1.1.1.1")
        assert out == ["8.8.8.8", "1.1.1.1"]

    def test_returns_a_list(self):
        assert isinstance(opnsense.ensure_fallback([], "1.1.1.1"), list)


# --------------------------------------------------------------------------- #
#  build_unbound_forward_payload — pure helper
# --------------------------------------------------------------------------- #
class TestBuildForwardPayload:
    def test_shape(self):
        payload = opnsense.build_unbound_forward_payload("8.8.8.8")
        assert set(payload.keys()) == {"dot"}
        dot = payload["dot"]
        assert dot["server"] == "8.8.8.8"
        assert dot["domain"] == ""           # empty domain => forward ALL domains
        assert dot["type"] == "forward"
        assert dot["port"] == "53"
        assert dot["enabled"] == "1"
        assert dot["forward_first"] == "1"   # deep safety net: recurse if all SERVFAIL
        assert dot["description"] == "adnauseam-netrot"

    def test_marker_override(self):
        payload = opnsense.build_unbound_forward_payload("9.9.9.9", marker="custom-mark")
        assert payload["dot"]["description"] == "custom-mark"

    def test_values_are_strings_and_json_serializable(self):
        payload = opnsense.build_unbound_forward_payload("1.0.0.1")
        # OPNsense's API expects string fields; body must round-trip through JSON.
        assert payload["dot"]["server"] == "1.0.0.1"
        assert json.loads(json.dumps(payload)) == payload


# --------------------------------------------------------------------------- #
#  pick_subset — weighted, distinct, bounded, excludes fallback
# --------------------------------------------------------------------------- #
POOL = [
    {"ip": "8.8.8.8", "weight": 3, "priority": True},
    {"ip": "9.9.9.9", "weight": 3, "priority": True},
    {"ip": "1.0.0.1", "weight": 2, "priority": False},
    {"ip": "80.80.81.81", "weight": 1, "priority": False},
    {"ip": "168.95.1.1", "weight": 1, "priority": False},
    {"ip": "1.1.1.1", "weight": 2, "priority": False},  # == FALLBACK
]


class TestPickSubset:
    def test_returns_distinct_within_bounds(self):
        picks = net_dns_rotator.pick_subset(3, exclude_fallback=True, pool=POOL)
        assert len(picks) == 3
        assert len(set(picks)) == 3  # distinct
        assert all(isinstance(p, str) for p in picks)

    def test_excludes_fallback(self):
        for _ in range(200):
            picks = net_dns_rotator.pick_subset(5, exclude_fallback=True, pool=POOL)
            assert net_dns_rotator.FALLBACK not in picks

    def test_all_picks_come_from_pool(self):
        pool_ips = {r["ip"] for r in POOL}
        for _ in range(200):
            for p in net_dns_rotator.pick_subset(4, exclude_fallback=True, pool=POOL):
                assert p in pool_ips

    def test_n_larger_than_pool_returns_all_non_fallback_distinct(self):
        picks = net_dns_rotator.pick_subset(999, exclude_fallback=True, pool=POOL)
        # 6 entries, one is the fallback which is excluded => at most 5 distinct.
        assert len(picks) == 5
        assert len(set(picks)) == 5
        assert net_dns_rotator.FALLBACK not in picks

    def test_zero_or_negative_is_empty(self):
        assert net_dns_rotator.pick_subset(0, pool=POOL) == []
        assert net_dns_rotator.pick_subset(-3, pool=POOL) == []

    def test_include_fallback_can_surface_it(self):
        # With exclude_fallback False and n >= pool size, the fallback becomes eligible.
        picks = net_dns_rotator.pick_subset(999, exclude_fallback=False, pool=POOL)
        assert "1.1.1.1" in picks
        assert len(set(picks)) == len(picks)

    def test_empty_pool_returns_empty(self):
        assert net_dns_rotator.pick_subset(5, pool=[]) == []


# --------------------------------------------------------------------------- #
#  OPNsenseClient — mocked urlopen, expected requests, never raises
# --------------------------------------------------------------------------- #
class TestOPNsenseClientGetState:
    def test_get_dns_state_parses_forwarders(self, monkeypatch):
        settings = {
            "unbound": {
                "dnssec": "1",
                "dots": {
                    "dot": {
                        "uuid-a": {"server": "8.8.8.8", "domain": "", "description": "adnauseam-netrot"},
                        "uuid-b": {"server": "9.9.9.9", "domain": "", "description": "adnauseam-netrot"},
                    }
                },
            }
        }
        rec = _Recorder({"/api/unbound/settings/get": settings})
        monkeypatch.setattr(opnsense.urllib.request, "urlopen", rec)

        state = _client().get_dns_state()
        assert state["reachable"] is True
        assert set(state["forwarders"]) == {"8.8.8.8", "9.9.9.9"}
        # One GET to settings/get.
        assert rec.calls[0][0] == "GET"
        assert rec.calls[0][1].endswith("/api/unbound/settings/get")

    def test_get_dns_state_handles_empty_dot_container(self, monkeypatch):
        rec = _Recorder({"/api/unbound/settings/get": {"unbound": {"dots": {"dot": ""}}}})
        monkeypatch.setattr(opnsense.urllib.request, "urlopen", rec)
        state = _client().get_dns_state()
        assert state["forwarders"] == []
        assert state["reachable"] is True

    def test_get_dns_state_never_raises_on_http_error(self, monkeypatch):
        rec = _Recorder(raise_http=True)
        monkeypatch.setattr(opnsense.urllib.request, "urlopen", rec)
        state = _client().get_dns_state()  # must not raise
        assert state["reachable"] is False
        assert state["forwarders"] == []


class TestOPNsenseClientSetForwarders:
    def _routes(self):
        # search_forward returns one existing MARKER row (to be deleted) plus a
        # user's split-DNS row (must be left alone).
        return {
            "/api/unbound/settings/searchForward": {
                "rows": [
                    {"uuid": "old-1", "description": "adnauseam-netrot", "server": "5.5.5.5"},
                    {"uuid": "user-keep", "description": "my-split-dns", "server": "192.168.1.1"},
                ],
                "total": 2,
            },
            "/api/unbound/settings/addForward": {"result": "saved", "uuid": "new"},
            "/api/unbound/service/reconfigure": {"status": "ok"},
        }

    def test_set_forwarders_deletes_ours_and_adds_each(self, monkeypatch):
        rec = _Recorder(self._routes())
        monkeypatch.setattr(opnsense.urllib.request, "urlopen", rec)

        applied = _client().set_forwarders(["8.8.8.8", "9.9.9.9"])

        # Fallback guaranteed present in the applied set.
        assert "1.1.1.1" in applied
        paths = rec.paths()
        # Enumerated existing entries.
        assert any(p.endswith("/api/unbound/settings/searchForward") for p in paths)
        # Deleted ONLY our marked uuid, never the user's split-DNS row.
        assert any(p.endswith("/api/unbound/settings/delForward/old-1") for p in paths)
        assert not any("user-keep" in p for p in paths)
        # Added one forward per applied IP.
        add_calls = [b for m, u, b in rec.calls if u.endswith("/api/unbound/settings/addForward")]
        assert len(add_calls) == len(applied)
        added_servers = {c["dot"]["server"] for c in add_calls}
        assert added_servers == set(applied)
        assert all(c["dot"]["description"] == "adnauseam-netrot" for c in add_calls)

    def test_set_forwarders_never_raises_on_http_error(self, monkeypatch):
        rec = _Recorder(raise_http=True)
        monkeypatch.setattr(opnsense.urllib.request, "urlopen", rec)
        applied = _client().set_forwarders(["8.8.8.8"])  # must not raise
        # Every add HTTP-failed, so the fallback itself never landed. The client must
        # REFUSE (return None) rather than report a success whose live config has no
        # working fallback — the caller then drives recovery.
        assert applied is None

    def test_reload_unbound_gates_on_running_status(self, monkeypatch):
        rec = _Recorder({
            "/api/unbound/service/reconfigure": {"status": "ok"},
            "/api/unbound/service/status": {"status": "running"},
        })
        monkeypatch.setattr(opnsense.urllib.request, "urlopen", rec)
        assert _client().reload_unbound() is True

    def test_reload_unbound_false_when_not_running(self, monkeypatch):
        rec = _Recorder({
            "/api/unbound/service/reconfigure": {"status": "ok"},
            "/api/unbound/service/status": {"status": "stopped"},
        })
        monkeypatch.setattr(opnsense.urllib.request, "urlopen", rec)
        assert _client().reload_unbound() is False


# --------------------------------------------------------------------------- #
#  run_cycle — DRY_RUN applies nothing
# --------------------------------------------------------------------------- #
class TestRunCycleDryRun:
    def _mock_client(self):
        client = MagicMock()
        # ensure_fallback must behave like the real pure helper so the subset shape
        # (fallback guaranteed) is realistic.
        client.ensure_fallback.side_effect = lambda picks, fb: opnsense.ensure_fallback(picks, fb)
        return client

    def test_dry_run_applies_nothing(self):
        client = self._mock_client()
        subset = net_dns_rotator.run_cycle(client, POOL, dry_run=True)
        assert net_dns_rotator.FALLBACK in subset
        # The whole point: no mutation of the production router.
        assert client.set_forwarders.call_count == 0
        assert client.reload_unbound.call_count == 0

    def test_non_dry_run_applies_the_subset(self):
        client = self._mock_client()
        subset = net_dns_rotator.run_cycle(client, POOL, dry_run=False)
        client.set_forwarders.assert_called_once_with(subset)
        client.reload_unbound.assert_called_once()

    def test_dry_run_subset_is_bounded_and_distinct(self):
        client = self._mock_client()
        subset = net_dns_rotator.run_cycle(client, POOL, dry_run=True)
        assert len(subset) == len(set(subset))
        assert len(subset) <= net_dns_rotator.SUBSET_HARD_MAX


# --------------------------------------------------------------------------- #
#  Safety defaults — the module is OFF and DRY by default.
# --------------------------------------------------------------------------- #
class TestSafetyDefaults:
    def test_defaults_are_off_and_dry(self):
        # With no env set (the CI/default case) the sidecar must be inert + dry.
        assert net_dns_rotator.OPNSENSE_ENABLED is False
        assert net_dns_rotator.ROTATE_ENABLED is False
        assert net_dns_rotator.DRY_RUN is True
        assert net_dns_rotator.FALLBACK == "1.1.1.1"

    def test_client_never_logs_credentials(self):
        # Credentials live only on private attrs, never on a public/logged surface.
        c = _client(api_key="SECRETKEY", api_secret="SECRETSECRET")
        public = {k: v for k, v in vars(c).items() if not k.startswith("_")}
        assert "SECRETKEY" not in json.dumps(public, default=str)
        assert "SECRETSECRET" not in json.dumps(public, default=str)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
