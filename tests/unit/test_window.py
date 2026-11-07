from datetime import date

import pytest

from strava_predictor.domain.models import DataError, DataErrorCode, ExclusionReason
from strava_predictor.domain.window import select_window
from tests.unit.domain_helpers import REFERENCE, act


def _base():
    return [act(1, 5.0, 30.0, avg=140), act(2, 6.0, 36.0), act(3, 7.0, 42.0)]


def test_only_running_types_are_used():
    runs = _base() + [
        act(1, 6.0, 36.0, type="Trail Run"),
        act(1, 6.0, 36.0, type="Virtual Run"),
        act(1, 30.0, 60.0, type="Ride"),
        act(1, 2.0, 30.0, type="Walk"),
    ]
    used, summary = select_window(runs, REFERENCE)
    assert len(used) == 5
    assert summary.excluded == {ExclusionReason.NOT_A_RUN: 2}


def test_window_is_84_days_including_reference_date():
    runs = _base() + [act(0, 5.0, 30.0), act(83, 5.0, 30.0), act(84, 5.0, 30.0), act(-1, 5.0, 30.0)]
    used, summary = select_window(runs, REFERENCE)
    assert len(used) == 5
    assert summary.excluded == {ExclusionReason.OUTSIDE_WINDOW: 2}


def test_unusable_distance_time_and_pace_are_excluded():
    runs = _base() + [
        act(1, None, 30.0),
        act(1, 5.0, None),
        act(1, 10.0, 15.0),
        act(1, 1.0, 25.0),
        act(1, 5.0, 10.0),
        act(1, 1.0, 20.0),
    ]
    used, summary = select_window(runs, REFERENCE)
    assert len(used) == 5
    assert summary.excluded == {
        ExclusionReason.NO_DISTANCE: 1,
        ExclusionReason.NO_MOVING_TIME: 1,
        ExclusionReason.IMPLAUSIBLE_PACE: 2,
    }
    assert summary.excluded_total == 4


def test_excluded_runs_keep_their_reason():
    used, _ = select_window(_base() + [act(1, None, 30.0)], REFERENCE)
    assert all(run.exclusion is None for run in used)


def test_runs_without_heart_rate_count_for_volume():
    used, summary = select_window(_base(), REFERENCE)
    assert summary.runs_used == 3
    assert summary.runs_with_hr == 1
    assert summary.avg_weekly_km_12 == pytest.approx(18.0 / 12)


def test_too_few_runs():
    with pytest.raises(DataError) as error:
        select_window([act(1, 5.0, 30.0), act(2, 5.0, 30.0), act(1, 5.0, None)], REFERENCE)
    assert error.value.code == DataErrorCode.TOO_FEW_RUNS
    assert "2" in error.value.message


def test_weekly_figures_and_longest_run():
    runs = [
        act(0, 10.0, 60.0),
        act(6, 4.0, 24.0),
        act(7, 8.0, 48.0),
        act(27, 6.0, 36.0),
        act(28, 20.0, 120.0),
        act(80, 12.0, 72.0),
    ]
    _, summary = select_window(runs, REFERENCE)
    assert summary.weeks_with_runs == 5
    assert summary.avg_weekly_km_4 == pytest.approx(28.0 / 4)
    assert summary.avg_weekly_km_12 == pytest.approx(60.0 / 12)
    assert summary.longest_run_km == 20.0
    assert summary.date_range == (date(2026, 8, 17), REFERENCE)


@pytest.mark.parametrize(("newest", "stale"), [(14, False), (15, True)])
def test_stale_data_warning(newest, stale):
    runs = [act(newest, 5.0, 30.0), act(newest + 2, 5.0, 30.0), act(newest + 4, 5.0, 30.0)]
    _, summary = select_window(runs, REFERENCE)
    codes = [warning.code for warning in summary.warnings]
    assert ("STALE_DATA" in codes) is stale
