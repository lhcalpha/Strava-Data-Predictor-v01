import re

import pytest

from tests.integration.helpers import VALID_FIELDS, make_client, post

INVALID = [
    ("race_distance_km", "0"),
    ("race_distance_km", "-1"),
    ("race_distance_km", "101"),
    ("race_distance_km", "abc"),
    ("race_distance_km", "nan"),
    ("race_distance_km", ""),
    ("weeks_to_race", "0"),
    ("weeks_to_race", "53"),
    ("weeks_to_race", "4.5"),
    ("weeks_to_race", ""),
    ("goal_pace", "4:60"),
    ("goal_pace", "abc"),
    ("goal_pace", "1:59"),
    ("goal_pace", ""),
    ("days_per_week", "1"),
    ("days_per_week", "8"),
    ("days_per_week", "x"),
    ("max_hr", "99"),
    ("max_hr", "241"),
    ("max_hr", ""),
]


@pytest.mark.parametrize(("field", "value"), INVALID)
def test_invalid_field_shows_message_and_keeps_other_values(load_fixture, field, value):
    response = post(make_client(), load_fixture("typical_runner.csv"), **{field: value})
    assert response.status_code == 400
    html = response.text
    assert f'id="{field}-error"' in html
    assert 'id="results"' not in html
    for other, kept in VALID_FIELDS.items():
        if other != field:
            assert re.search(rf'name="{other}"[^>]*value="{re.escape(kept)}"', html), other


def test_missing_file_on_first_submit():
    response = post(make_client(), None)
    assert response.status_code == 400
    assert 'id="csv_file-error"' in response.text
    for name, value in VALID_FIELDS.items():
        assert re.search(rf'name="{name}"[^>]*value="{re.escape(value)}"', response.text)


def test_several_errors_at_once(load_fixture):
    response = post(
        make_client(), load_fixture("typical_runner.csv"), weeks_to_race="0", days_per_week="9"
    )
    assert 'id="weeks_to_race-error"' in response.text
    assert 'id="days_per_week-error"' in response.text
