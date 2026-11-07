from datetime import timedelta

import pytest

from strava_predictor.domain.analysis import analyse
from strava_predictor.domain.models import DataError, Rating
from strava_predictor.domain.parsing import parse_activities
from strava_predictor.domain.prediction import riegel

# Hard runs in typical_runner.csv (avg >= 165 at max HR 201): (km, minutes)
HARD_RUNS = [(10.0, 46.0), (5.0, 22.5), (8.0, 37.0), (6.0, 27.6), (10.0, 47.0), (4.0, 18.4)]


def test_typical_runner_matches_hand_calculation(load_fixture, default_inputs, reference_date):
    result = analyse(load_fixture("typical_runner.csv"), default_inputs, reference_date)
    predictions = sorted(riegel(minutes * 60, km, 10.0) for km, minutes in HARD_RUNS)
    expected_today = sum(predictions[:3]) / 3
    assert result.prediction.today_time_s == pytest.approx(expected_today)
    assert result.prediction.hard_runs_used == 6
    assert result.summary.hard_runs_used == 6
    assert result.summary.runs_used == 30
    # 12 weeks: taper 1, so 11 pre-taper weeks; longest run 16 km reaches the 12 km target.
    assert result.prediction.distance_slowdown_pct == 0
    assert result.prediction.likely.time_s == pytest.approx(expected_today * (1 - 0.003 * 12))
    assert result.rating.rating == Rating.CONSERVATIVE


def test_same_inputs_give_same_result(load_fixture, default_inputs, reference_date):
    text = load_fixture("typical_runner.csv")
    assert analyse(text, default_inputs, reference_date) == analyse(
        text, default_inputs, reference_date
    )


def test_parsed_activities_give_same_result(load_fixture, default_inputs, reference_date):
    text = load_fixture("typical_runner.csv")
    from_text = analyse(text, default_inputs, reference_date)
    from_runs = analyse(parse_activities(text), default_inputs, reference_date)
    assert from_text == from_runs


def test_reference_date_moves_the_window(load_fixture, default_inputs, reference_date):
    text = load_fixture("typical_runner.csv")
    later = analyse(text, default_inputs, reference_date + timedelta(days=30))
    assert later.summary.runs_used < 30


def test_errors_propagate(load_fixture, default_inputs, reference_date):
    with pytest.raises(DataError):
        analyse(load_fixture("too_few_runs.csv"), default_inputs, reference_date)
