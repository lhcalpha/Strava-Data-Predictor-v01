"""002 FR-001, FR-005, FR-007 to FR-009: the levelling-off curve and safe/likely/stretch."""

import math
from statistics import NormalDist

import pytest

from strava_predictor.domain.models import NoTrendReason, RunnerInputs
from strava_predictor.domain.numbers import format_duration, format_pace
from strava_predictor.domain.prediction import predict
from tests.unit.domain_helpers import act, summary

TODAY_RUN = [act(3, 10.0, 50.0, avg=170)]  # 3000 s for 10 km
Z = NormalDist().inv_cdf(0.8)


def _predict(race_weeks=10, runs=TODAY_RUN, race_km=10.0, **summary_args):
    inputs = RunnerInputs(race_km, race_weeks, 290, 4, 201)
    return predict(runs, summary(**summary_args), inputs)


def test_scenario_1_ten_weeks_from_fifty_minutes():
    """002 US1 scenario 1: 48:45 likely, 49:41 safe, 47:50 stretch."""
    result = _predict()
    assert result.today_time_s == pytest.approx(3000.0)
    assert result.weekly_rate == pytest.approx(0.003)
    assert result.improvement == pytest.approx(0.0250169, abs=1e-6)
    assert result.likely.time_s == pytest.approx(2924.949, abs=0.01)
    assert result.safe.time_s == pytest.approx(2980.867, abs=0.01)
    assert result.stretch.time_s == pytest.approx(2870.081, abs=0.01)
    assert format_duration(result.likely.time_s) == "48:45"
    assert format_duration(result.safe.time_s) == "49:41"
    assert format_duration(result.stretch.time_s) == "47:50"
    assert format_pace(result.likely.pace_s_per_km) == "4:52"
    assert format_pace(result.safe.pace_s_per_km) == "4:58"
    assert format_pace(result.stretch.pace_s_per_km) == "4:47"
    assert result.rate_multiplier == 1.0
    assert result.no_trend_reason == NoTrendReason.TOO_FEW_RUNS


def test_likely_follows_the_curve():
    result = _predict(race_weeks=17)
    gmax = 0.08
    expected = gmax * (1 - math.exp(-0.003 * 17 / gmax))
    assert result.max_improvement == pytest.approx(gmax)
    assert result.improvement == pytest.approx(expected)
    assert result.likely.time_s == pytest.approx(3000.0 * (1 - expected))


@pytest.mark.parametrize(
    ("summary_args", "multiplier"),
    [
        ({"weeks": 7}, 1.25),
        ({"weeks": 8}, 1.0),
        ({"avg12": 14.9}, 1.25),
        ({"avg12": 15.0}, 1.0),
        ({"avg12": 60.0}, 1.0),
        ({"avg12": 60.1}, 0.75),
        ({"weeks": 7, "avg12": 61.0}, 0.9375),
    ],
)
def test_multiplier_scales_rate_limit_and_rate_uncertainty(summary_args, multiplier):
    result = _predict(**summary_args)
    assert result.rate_multiplier == pytest.approx(multiplier)
    assert result.typical_rate == pytest.approx(0.003 * multiplier)
    assert result.weekly_rate == pytest.approx(0.003 * multiplier)
    gmax = 0.08 * multiplier
    assert result.max_improvement == pytest.approx(gmax)
    decay = math.exp(-0.003 * multiplier * 10 / gmax)
    assert result.improvement == pytest.approx(gmax * (1 - decay))
    assert result.sigma_improvement == pytest.approx(0.0015 * multiplier * 10 * decay)


def test_improvement_levels_off_below_the_limit():
    """002 US1 scenario 7."""
    gains = [_predict(race_weeks=weeks).improvement for weeks in range(1, 53)]
    steps = [later - earlier for earlier, later in zip(gains, gains[1:], strict=False)]
    assert all(step > 0 for step in steps)
    assert all(later < earlier for earlier, later in zip(steps, steps[1:], strict=False))
    assert gains[-1] == pytest.approx(0.0686181, abs=1e-6)
    assert gains[-1] < 0.08


def test_short_plans_start_at_the_weekly_rate():
    assert _predict(race_weeks=1).improvement == pytest.approx(0.003, rel=0.02)


def test_safe_and_stretch_are_the_80_and_20_percentiles():
    result = _predict(race_weeks=12)
    sigma = math.hypot(result.sigma_today, result.sigma_improvement)
    assert result.sigma == pytest.approx(sigma)
    assert result.safe.time_s == pytest.approx(result.likely.time_s * math.exp(Z * sigma))
    assert result.stretch.time_s == pytest.approx(result.likely.time_s * math.exp(-Z * sigma))


def _slowing_runs(count=6):
    """Hard 10 km runs two weeks apart, each 1% a week slower than the one before."""
    return [act(14 * (count - 1 - i), 10.0, 50.0 * 1.01 ** (2 * i), avg=170) for i in range(count)]


def test_slowing_trend_floors_the_rate_at_zero():
    """002 US1 scenario 6: 6 runs give weight 6/14, which outweighs the typical rate."""
    result = _predict(runs=_slowing_runs())
    assert result.trend_rate == pytest.approx(-0.005)
    assert result.weekly_rate == 0.0
    assert result.improvement == 0.0
    assert result.likely.time_s == pytest.approx(result.today_time_s)
    assert result.sigma_improvement == pytest.approx(0.0015 * math.sqrt(1 - 6 / 14) * 10)


DISTANCES = (3.0, 5.0, 10.0, 21.1, 42.195, 100.0)


@pytest.mark.parametrize("race_km", DISTANCES)
@pytest.mark.parametrize("summary_args", [{}, {"weeks": 5, "avg12": 10.0}, {"avg12": 80.0}])
def test_order_and_chances_hold_for_every_distance_and_week(race_km, summary_args):
    """002 SC-002: safe >= likely >= stretch with 80/50/20 chances."""
    for weeks in range(1, 53):
        result = _predict(race_weeks=weeks, race_km=race_km, **summary_args)
        assert result.safe.time_s > result.likely.time_s > result.stretch.time_s
        spread = NormalDist(math.log(result.likely.time_s), result.sigma)
        assert spread.cdf(math.log(result.safe.time_s)) == pytest.approx(0.8)
        assert spread.cdf(math.log(result.stretch.time_s)) == pytest.approx(0.2)
        assert result.likely.pace_s_per_km == pytest.approx(result.likely.time_s / race_km)
