import pytest

from strava_predictor.domain.analysis import analyse
from strava_predictor.domain.models import RunnerInputs
from strava_predictor.domain.numbers import format_duration, format_pace
from tests.integration.helpers import REFERENCE_DATE, make_client, post


def test_results_show_every_summary_value(load_fixture):
    text = load_fixture("typical_runner.csv")
    response = post(make_client(), text)
    assert response.status_code == 200
    html = response.text
    expected = analyse(text, RunnerInputs(10.0, 12, 290, 4, 201), REFERENCE_DATE).prediction
    assert 'id="results"' in html
    for value in (
        expected.today_pace_s_per_km,
        expected.safe.pace_s_per_km,
        expected.likely.pace_s_per_km,
        expected.stretch.pace_s_per_km,
    ):
        assert format_pace(value) in html
    for value in (expected.today_time_s, expected.safe.time_s, expected.stretch.time_s):
        assert format_duration(value) in html
    assert "4:50" in html
    assert format_duration(2900) in html  # goal time for 10 km at 4:50
    assert "Conservative" in html
    assert 'id="confidence"' in html
    assert "estimates, not guarantees" in html
    assert "not medical advice" in html


def test_interval_only_note(load_fixture):
    html = post(make_client(), load_fixture("interval_only.csv")).text
    assert "probably slower than your true fitness" in html


def test_low_confidence_reason_shown(load_fixture):
    html = post(make_client(), load_fixture("no_hard_runs.csv")).text
    assert "Low" in html
    assert "no hard runs" in html


@pytest.mark.parametrize(
    ("overrides", "warning"),
    [
        ({"race_distance_km": "2"}, "less reliable"),
        ({"race_distance_km": "50"}, "less reliable"),
        ({"weeks_to_race": "3"}, "fewer than 4 weeks"),
    ],
)
def test_input_warnings_do_not_block_results(load_fixture, overrides, warning):
    response = post(make_client(), load_fixture("typical_runner.csv"), **overrides)
    assert response.status_code == 200
    assert 'id="results"' in response.text
    assert warning in response.text


@pytest.mark.parametrize(
    ("fixture", "message"),
    [
        ("missing_columns.csv", "Moving Time"),
        ("empty.csv", "empty"),
        ("malformed.csv", "could not be read"),
        ("too_few_runs.csv", "at least 3"),
    ],
)
def test_data_errors_block_results(load_fixture, fixture, message):
    response = post(make_client(), load_fixture(fixture))
    assert response.status_code == 400
    assert 'id="results"' not in response.text
    assert message in response.text


def test_non_utf8_file_is_rejected():
    response = post(make_client(), b"\xff\xfe\x00bad")
    assert response.status_code == 400
    assert "could not be read" in response.text
