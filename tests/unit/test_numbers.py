import pytest

from strava_predictor.domain.numbers import (
    format_duration,
    format_pace,
    parse_pace,
    round_half_up,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [(150.75, 151), (164.82, 165), (2.5, 3), (3.5, 4), (2.4999, 2), (0.0, 0)],
)
def test_round_half_up(value, expected):
    assert round_half_up(value) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [("4:50", 290), (" 4:50 ", 290), ("2:00", 120), ("15:00", 900), ("10:05", 605)],
)
def test_parse_pace_valid(text, expected):
    assert parse_pace(text) == expected


@pytest.mark.parametrize("text", ["4:60", "450", "", "1:59", "15:01", "abc", "4:5", "-4:50"])
def test_parse_pace_invalid(text):
    with pytest.raises(ValueError):
        parse_pace(text)


@pytest.mark.parametrize(
    ("seconds", "expected"), [(290.4, "4:50"), (290.5, "4:51"), (59.6, "1:00"), (605, "10:05")]
)
def test_format_pace(seconds, expected):
    assert format_pace(seconds) == expected


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [(3127.4, "52:07"), (5400, "1:30:00"), (59, "0:59"), (3600, "1:00:00"), (12345.6, "3:25:46")],
)
def test_format_duration(seconds, expected):
    assert format_duration(seconds) == expected
