"""002 FR-002 to FR-004: the runner's own trend, blended with the typical rate."""

import pytest

from strava_predictor.domain.models import NoTrendReason, RunnerInputs
from strava_predictor.domain.prediction import predict
from tests.unit.domain_helpers import act, summary


def _predict(runs, **summary_args):
    return predict(runs, summary(**summary_args), RunnerInputs(10.0, 10, 290, 4, 201))


def _improving(count=5, weekly=0.005, gap_days=14, km=10.0):
    """Hard runs `gap_days` apart, each `weekly` a week faster than the one before."""
    weeks_between = gap_days / 7
    return [
        act(gap_days * (count - 1 - i), km, 50.0 * (1 - weekly) ** (weeks_between * i), avg=170)
        for i in range(count)
    ]


def test_scenario_4_trend_weight_and_rate():
    result = _predict(_improving())
    assert result.trend_rate == pytest.approx(0.005)
    assert result.trend_runs == 5
    assert result.trend_weight == pytest.approx(5 / 13)
    assert result.weekly_rate == pytest.approx(0.0037692, abs=1e-7)
    assert result.no_trend_reason is None


def test_more_runs_give_the_trend_more_weight():
    result = _predict(_improving(count=8, gap_days=10))
    assert result.trend_weight == pytest.approx(8 / 16)
    assert result.weekly_rate == pytest.approx(0.5 * 0.005 + 0.5 * 0.003)


def test_too_few_runs():
    result = _predict(_improving(count=3))
    assert result.trend_rate is None
    assert result.trend_weight == 0.0
    assert result.trend_runs == 3
    assert result.no_trend_reason == NoTrendReason.TOO_FEW_RUNS
    assert result.weekly_rate == pytest.approx(0.003)


@pytest.mark.parametrize(("gap_days", "used"), [(9, False), (10, True)])
def test_runs_must_span_28_days(gap_days, used):
    """4 runs `gap_days` apart span 27 days (9) or 30 days (10)."""
    result = _predict(_improving(count=4, gap_days=gap_days))
    assert (result.trend_rate is not None) is used
    if not used:
        assert result.no_trend_reason == NoTrendReason.TOO_SHORT_SPAN


def test_exactly_28_days_is_enough():
    runs = [act(days, 10.0, 50.0, avg=170) for days in (28, 20, 10, 0)]
    assert _predict(runs).trend_rate == pytest.approx(0.0)


def test_no_trend_with_the_fallback():
    runs = [act(days, 10.0, 60.0 - days / 10) for days in (60, 45, 30, 15, 0)]
    result = _predict(runs)
    assert result.used_fallback
    assert result.trend_rate is None
    assert result.trend_runs == 0
    assert result.no_trend_reason == NoTrendReason.FALLBACK


def test_only_hard_runs_of_3_km_or_more_count():
    runs = [
        *_improving(),
        act(35, 10.0, 40.0, avg=140),  # easy: ignored
        act(21, 2.5, 8.0, avg=175),  # hard but short: ignored
    ]
    result = _predict(runs)
    assert result.trend_runs == 5
    assert result.trend_rate == pytest.approx(0.005)


def test_runs_on_the_same_date_are_skipped_in_pairs():
    runs = [*_improving(), act(0, 10.0, 52.0, avg=170)]  # same date as the newest run
    result = _predict(runs)
    assert result.trend_runs == 6


def test_one_bad_run_does_not_move_the_trend():
    runs = _improving(count=6)
    runs[2] = act(42, 10.0, 56.0, avg=170)  # a hot, hilly day: about 10% slow
    assert _predict(runs).trend_rate == pytest.approx(0.005)


@pytest.mark.parametrize(("weekly", "limited"), [(0.03, 0.010), (-0.03, -0.005)])
def test_trend_is_limited(weekly, limited):
    assert _predict(_improving(weekly=weekly)).trend_rate == pytest.approx(limited)


def test_trend_uses_every_hard_run_not_just_the_basis():
    result = _predict(_improving(count=7, gap_days=10))
    assert len(result.basis_runs) == 3
    assert result.trend_runs == 7
