import math
from statistics import NormalDist

import pytest

from strava_predictor.domain.models import RunnerInputs
from strava_predictor.domain.prediction import long_run_target_km, predict
from tests.unit.domain_helpers import act, summary

HALF = 21.0975
Z = NormalDist().inv_cdf(0.8)


@pytest.mark.parametrize(
    ("race_km", "target"),
    [
        (3.0, 8.0),
        (5.0, 8.0),
        (10.0, 12.0),
        (15.0, 14.703),
        (HALF, 18.0),
        (42.195, 30.0),
        (50.0, 34.44),
        (100.0, 35.0),
    ],
)
def test_long_run_target(race_km, target):
    assert long_run_target_km(race_km) == pytest.approx(target, abs=0.01)


def _half(weeks, longest):
    runs = [act(3, 10.0, 50.0, avg=170)]
    return predict(runs, summary(longest=longest), RunnerInputs(HALF, weeks, 290, 4, 201))


def test_reachable_long_run_grows_over_pre_taper_weeks():
    result = _half(weeks=6, longest=10.0)
    assert result.reachable_long_run_km == pytest.approx(10.0 * 1.1**4)


def test_two_full_steps_short_slow_paces_by_two_percent():
    result = _half(weeks=1, longest=14.0)
    assert result.distance_slowdown_pct == 2
    likely = result.today_time_s * (1 - result.improvement)
    spread = math.exp(Z * result.sigma)
    assert result.likely.time_s == pytest.approx(likely * 1.02)
    assert result.safe.time_s == pytest.approx(likely * spread * 1.02)
    assert result.stretch.time_s == pytest.approx(likely / spread * 1.02)


@pytest.mark.parametrize(("longest", "steps"), [(16.218, 0), (16.2, 1), (18.0, 0), (25.0, 0)])
def test_full_steps_only(longest, steps):
    assert _half(weeks=1, longest=longest).distance_slowdown_pct == steps


def test_slowdown_is_applied_after_the_projection():
    """002 FR-009: the slowdown multiplies all three projected times."""
    result = _half(weeks=52, longest=0.12)
    assert result.distance_slowdown_pct == 2
    likely = result.today_time_s * (1 - result.improvement)
    assert result.stretch.time_s == pytest.approx(likely * math.exp(-Z * result.sigma) * 1.02)
