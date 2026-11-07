import pytest

from strava_predictor.domain.effort import classify_effort, effort_thresholds
from strava_predictor.domain.models import EffortClass


def test_thresholds_at_201():
    assert effort_thresholds(201) == (151, 165)


def test_thresholds_follow_max_hr():
    assert effort_thresholds(180) == (135, 148)


@pytest.mark.parametrize(
    ("avg", "expected"),
    [
        (150, EffortClass.EASY),
        (151, EffortClass.EASY),
        (152, EffortClass.MODERATE),
        (164, EffortClass.MODERATE),
        (165, EffortClass.HARD),
        (166, EffortClass.HARD),
        (None, EffortClass.UNKNOWN),
    ],
)
def test_classify_at_201(avg, expected):
    assert classify_effort(avg, 201) == expected


@pytest.mark.parametrize(
    ("avg", "expected"),
    [(135, EffortClass.EASY), (136, EffortClass.MODERATE), (148, EffortClass.HARD)],
)
def test_classify_at_180(avg, expected):
    assert classify_effort(avg, 180) == expected
