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
        # 003: dash and "HR" forms
        ("Avg - 187", 187),
        ("Avg -187", 187),
        ("Avg HR - 176", 176),
        ("Avg HR: 175", 175),
        ("Avg HR-168", 168),
        ("Avg HR 182", 182),
        ("avg hr 150", 150),
        ("Avg HR - 160bpm", 160),
        ("Avg HR - 152(Polar H10)", 152),
        ("Avg - 147\nWatch got off during last 1k", 147),
        ("With [strava://athletes/12345678/12]Some Friend \nAvg - 143", 143),
        ("5x1km Pace, Rest runs 6x1k in between \nAvg HR 173", 173),
        ("Avg HR - 29", None),
        ("Avg - 251", None),
        ("Avg - 1650", None),
        ("Overall Rank: 125", None),
        ("19x400m Reps", None),
        ("Max : 199", None),
        ("Average pace: 04:58/km", None),
        ("Avg pace 4:50", None),
        ("Avg - 15:30 pace", None),
    ],
)
def test_parse_avg_hr(description, expected):
    assert parse_avg_hr(description) == expected


def test_activity_gets_avg_hr_from_description():
    text = make_csv([run(1, 5.0, 25.0, description="Avg: 158 bpm, 3 laps"), run(2, 5.0, 25.0)])
    first, second = parse_activities(text)
    assert first.avg_hr == 158
    assert second.avg_hr is None
