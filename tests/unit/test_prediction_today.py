import pytest

from strava_predictor.domain.models import DataError, DataErrorCode, RunnerInputs
from strava_predictor.domain.prediction import predict, riegel
from tests.unit.domain_helpers import act, summary


def _inputs(km=10.0, weeks=10):
    return RunnerInputs(km, weeks, 290, 4, 201)


def test_riegel_known_value():
    assert riegel(1500.0, 5.0, 10.0) == pytest.approx(3127.4, abs=0.1)


def test_single_hard_run():
    result = predict([act(3, 5.0, 25.0, avg=170)], summary(), _inputs())
    assert result.today_time_s == pytest.approx(3127.4, abs=0.1)
    assert result.hard_runs_used == 1
    assert not result.used_fallback


def test_three_fastest_of_five_hard_runs():
    runs = [
        act(1, 10.0, 50.0, avg=170),
        act(2, 10.0, 48.0, avg=170),
        act(3, 10.0, 52.0, avg=170),
        act(4, 10.0, 49.0, avg=170),
        act(5, 10.0, 55.0, avg=170),
    ]
    result = predict(runs, summary(), _inputs())
    assert result.today_time_s == pytest.approx((48 + 49 + 50) * 60 / 3)
    assert result.hard_runs_used == 5
    assert {run.moving_time_s for run in result.basis_runs} == {2880.0, 2940.0, 3000.0}


def test_two_hard_runs_are_both_averaged():
    runs = [act(1, 10.0, 50.0, avg=170), act(2, 10.0, 48.0, avg=170), act(3, 10.0, 70.0)]
    result = predict(runs, summary(), _inputs())
    assert result.today_time_s == pytest.approx(49 * 60)


def test_hard_runs_under_3km_are_ignored():
    runs = [act(1, 2.9, 10.0, avg=180), act(2, 10.0, 50.0, avg=170)]
    result = predict(runs, summary(), _inputs())
    assert result.today_time_s == pytest.approx(3000.0)
    assert result.hard_runs_used == 1


def test_fallback_uses_three_fastest_runs_over_3km():
    runs = [
        act(1, 10.0, 60.0, avg=140),
        act(2, 10.0, 58.0),
        act(3, 10.0, 62.0),
        act(4, 10.0, 70.0),
        act(5, 2.0, 8.0),
    ]
    result = predict(runs, summary(), _inputs())
    assert result.used_fallback
    assert result.hard_runs_used == 0
    assert result.today_time_s == pytest.approx((58 + 60 + 62) * 60 / 3)


def test_no_run_of_3km_is_an_error():
    with pytest.raises(DataError) as error:
        predict([act(1, 2.5, 12.0), act(2, 2.0, 10.0)], summary(), _inputs())
    assert error.value.code == DataErrorCode.NO_RUN_OVER_3KM


def test_interval_only_basis():
    runs = [act(1, 6.0, 28.0, avg=172, name="Intervals"), act(2, 10.0, 60.0, avg=140)]
    assert predict(runs, summary(), _inputs()).interval_only


def test_mixed_basis_is_not_interval_only():
    runs = [act(1, 6.0, 28.0, avg=172, name="Intervals"), act(2, 10.0, 50.0, avg=170)]
    assert not predict(runs, summary(), _inputs()).interval_only


def test_ten_k_pace_uses_same_method():
    result = predict([act(3, 5.0, 25.0, avg=170)], summary(), _inputs(km=5.0))
    assert result.today_time_s == pytest.approx(1500.0)
    assert result.today_10k_pace_s_per_km == pytest.approx(312.74, abs=0.01)


def test_hard_depends_on_max_hr():
    runs = [act(1, 10.0, 50.0, avg=150), act(2, 10.0, 60.0, avg=120)]
    low_max = predict(runs, summary(), RunnerInputs(10.0, 10, 290, 4, 180))
    assert low_max.hard_runs_used == 1
    high_max = predict(runs, summary(), RunnerInputs(10.0, 10, 290, 4, 201))
    assert high_max.used_fallback
