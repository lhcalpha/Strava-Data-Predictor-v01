import pytest

from strava_predictor.domain.taper import taper_weeks


@pytest.mark.parametrize(
    ("race_km", "weeks", "expected"),
    [
        (5.0, 12, 1),
        (10.0, 12, 1),
        (10.1, 12, 2),
        (21.1, 12, 2),
        (21.2, 12, 3),
        (42.195, 12, 3),
        (100.0, 12, 3),
        (42.195, 3, 2),
        (42.195, 2, 1),
        (42.195, 1, 1),
        (5.0, 1, 1),
        (21.1, 2, 1),
    ],
)
def test_taper_weeks(race_km, weeks, expected):
    assert taper_weeks(race_km, weeks) == expected
