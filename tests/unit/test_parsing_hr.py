import pytest

from strava_predictor.domain.parsing import parse_activities, parse_avg_hr
from tests.fixtures.builders import make_csv, run


@pytest.mark.parametrize(
    ("description", "expected"),
    [
        ("Avg 165", 165),
        ("Avg: 165", 165),
        ("avg165", 165),
        ("AVG 165", 165),
        ("Felt good. Avg 165 Max 190, 12 laps", 165),
        ("Avg 30", 30),
        ("Avg 250", 250),
        ("Average 150", None),
        ("Max 190 only", None),
        ("12 laps", None),
        ("Avg 29", None),
        ("Avg 251", None),
        ("Avg 5", None),
        ("", None),
        (None, None),
    ],
)
def test_parse_avg_hr(description, expected):
    assert parse_avg_hr(description) == expected


def test_activity_gets_avg_hr_from_description():
    text = make_csv([run(1, 5.0, 25.0, description="Avg: 158 bpm, 3 laps"), run(2, 5.0, 25.0)])
    first, second = parse_activities(text)
    assert first.avg_hr == 158
    assert second.avg_hr is None
