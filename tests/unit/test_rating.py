import pytest

from strava_predictor.domain.models import Confidence, Rating, RunnerInputs
from strava_predictor.domain.prediction import predict
from strava_predictor.domain.rating import rate_goal
from tests.unit.domain_helpers import act, prediction, summary


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


# --- 002 FR-010: chance of reaching the goal ---------------------------------------------


def _scenario_1():
    """002 US1 scenario 1: 50:00 for 10 km today, 10 weeks to race."""
    runs = [act(3, 10.0, 50.0, avg=170)]
    return predict(runs, summary(), RunnerInputs(10.0, 10, 290, 4, 201))


@pytest.mark.parametrize(
    ("goal", "expected_rating", "chance_pct"),
    [
        (290, Rating.AMBITIOUS, 35),
        (285, Rating.VERY_AMBITIOUS, 12),
        (280, Rating.UNLIKELY, 3),
    ],
)
def test_scenario_2_rating_and_chance(goal, expected_rating, chance_pct):
    result = rate_goal(goal, _scenario_1(), summary())
    assert result.rating == expected_rating
    assert round(result.goal_chance * 100) == chance_pct


@pytest.mark.parametrize(("which", "chance"), [("safe", 0.8), ("likely", 0.5), ("stretch", 0.2)])
def test_scenario_3_chance_at_each_projection(which, chance):
    projected = _scenario_1()
    goal = getattr(projected, which).pace_s_per_km
    assert rate_goal(goal, projected, summary()).goal_chance == pytest.approx(chance)


def test_chance_uses_the_slowed_likely_time():
    projected = prediction(likely=300.0, sigma=0.05)
    assert rate_goal(300.0, projected, summary()).goal_chance == pytest.approx(0.5)
    faster = rate_goal(290.0, projected, summary()).goal_chance
    slower = rate_goal(310.0, projected, summary()).goal_chance
    assert faster < 0.5 < slower
