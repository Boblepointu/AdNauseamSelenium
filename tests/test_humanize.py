"""Tests for crawler.humanize pure helpers.

Only the deterministic / pure math helpers are exercised here — anything that
touches a Selenium driver is out of scope. Module-level import proves the
package loads without a browser.
"""
import random

import pytest

from crawler import humanize


class TestBezierCurve:
    def test_endpoints_match_start_and_end(self):
        start = (0, 0)
        end = (100, 200)
        control = [(30, 80), (70, 120)]
        pts = humanize.bezier_curve(start, end, control, steps=50)
        assert pts[0] == start
        assert pts[-1] == end

    def test_number_of_points_is_steps_plus_one(self):
        for steps in (1, 10, 25, 50):
            pts = humanize.bezier_curve((0, 0), (10, 10), [(5, 5)], steps=steps)
            assert len(pts) == steps + 1

    def test_points_are_integer_tuples(self):
        pts = humanize.bezier_curve((0, 0), (10, 10), [(5, 5)], steps=5)
        for x, y in pts:
            assert isinstance(x, int)
            assert isinstance(y, int)

    def test_no_control_points_is_linear(self):
        # With zero control points it degenerates to a straight line; endpoints
        # must still be honoured.
        pts = humanize.bezier_curve((0, 0), (100, 0), [], steps=10)
        assert pts[0] == (0, 0)
        assert pts[-1] == (100, 0)


class TestTimeOfDayMultiplier:
    def test_returns_known_multiplier(self):
        mult = humanize.get_time_of_day_multiplier()
        assert mult in {1.0, 1.05, 1.2, 1.3, 1.5}

    def test_is_positive_float(self):
        mult = humanize.get_time_of_day_multiplier()
        assert isinstance(mult, float)
        assert mult > 0


class TestHumanDelay:
    def test_returns_positive_float(self):
        random.seed(1234)
        for _ in range(200):
            d = humanize.human_delay(2.0)
            assert isinstance(d, float)
            assert d > 0

    def test_never_below_floor(self):
        # Documented invariant: never less than 0.3s.
        random.seed(42)
        for _ in range(500):
            d = humanize.human_delay(0.5, variance=0.5)
            assert d >= 0.3

    def test_scales_with_base_on_average(self):
        random.seed(7)
        small = [humanize.human_delay(1.0, variance=0.1) for _ in range(300)]
        large = [humanize.human_delay(10.0, variance=0.1) for _ in range(300)]
        assert sum(large) / len(large) > sum(small) / len(small)


class TestRealisticDelay:
    def test_returns_positive_float(self):
        random.seed(99)
        for _ in range(200):
            d = humanize.realistic_delay(2.0)
            assert isinstance(d, float)
            assert d > 0

    def test_within_broad_expected_bounds(self):
        # base 2s, floor 0.3s; circadian <= 1.5x, distraction up to 5x, no
        # fatigue model configured by default. Assert a generous upper bound
        # rather than an exact value to stay deterministic across seeds.
        random.seed(2024)
        for _ in range(300):
            d = humanize.realistic_delay(2.0, variance=0.3)
            assert 0.3 <= d < 200

    def test_fatigue_disabled_ignores_model(self):
        # apply_fatigue=False must not require config.fatigue_model.
        random.seed(5)
        d = humanize.realistic_delay(1.0, apply_fatigue=False)
        assert d > 0


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
