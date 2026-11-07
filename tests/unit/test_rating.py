import pytest

from strava_predictor.domain.models import Confidence, Rating
from strava_predictor.domain.rating import rate_goal
from tests.unit.domain_helpers import prediction, summary


@pytest.mark.parametrize(
    ("goal", "expected"),
    [
        (295, Rating.CONSERVATIVE),
        (294.01, Rating.CONSERVATIVE),
        (294, Rating.REALISTIC),
        (292, Rating.REALISTIC),
        (291, Rating.REALISTIC),
        (290.99, Rating.AMBITIOUS),
        (285, Rating.AMBITIOUS),
        (284.99, Rating.VERY_AMBITIOUS),
        (280, Rating.VERY_AMBITIOUS),  # spec US1 scenario 4: 4:40 per km
        (279.3, Rating.VERY_AMBITIOUS),
        (279.29, Rating.UNLIKELY),
        (279, Rating.UNLIKELY),
    ],
)
def test_rating_boundaries(goal, expected):
    assert rate_goal(goal, prediction(), summary()).rating == expected


def test_normal_confidence():
    result = rate_goal(290, prediction(hard_runs_used=3), summary(runs_used=10, runs_with_hr=5))
    assert result.confidence == Confidence.NORMAL
    assert result.confidence_reasons == ()


def test_low_confidence_with_few_hard_runs():
    result = rate_goal(290, prediction(hard_runs_used=2), summary())
    assert result.confidence == Confidence.LOW
    assert any("hard" in reason for reason in result.confidence_reasons)


def test_low_confidence_with_little_heart_rate():
    result = rate_goal(290, prediction(), summary(runs_used=10, runs_with_hr=4))
    assert result.confidence == Confidence.LOW
    assert any("heart rate" in reason for reason in result.confidence_reasons)


def test_low_confidence_with_fallback():
    result = rate_goal(290, prediction(hard_runs_used=0, used_fallback=True), summary())
    assert result.confidence == Confidence.LOW
    assert len(result.confidence_reasons) == 1
    assert "no hard runs" in result.confidence_reasons[0]


def test_both_reasons_are_listed():
    result = rate_goal(290, prediction(hard_runs_used=1), summary(runs_used=10, runs_with_hr=2))
    assert len(result.confidence_reasons) == 2
