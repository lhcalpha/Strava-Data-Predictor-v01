"""SC-003: every plan across distances, weeks, and days obeys the rules (1,872 plans per runner)."""

import pytest

from strava_predictor import config
from strava_predictor.domain.models import Rating
from strava_predictor.domain.plan_rules import check_plan_rules
from tests.unit.plan_helpers import make_plan

DISTANCES = (3.0, 5.0, 10.0, 21.1, 42.195, 100.0)
RUNNERS = {
    "typical": {"avg4": 35.0, "avg12": 32.0, "longest": 16.0, "today": 300.0, "stretch": 285.0},
    "beginner": {"avg4": 8.0, "avg12": 9.0, "longest": 5.0, "today": 420.0, "stretch": 400.0},
    "high_volume": {"avg4": 80.0, "avg12": 75.0, "longest": 32.0, "today": 240.0, "stretch": 230.0},
}


@pytest.mark.parametrize("runner", sorted(RUNNERS))
@pytest.mark.parametrize("days", range(config.DAYS_MIN, config.DAYS_MAX + 1))
@pytest.mark.parametrize("km", DISTANCES)
def test_every_plan_obeys_the_rules(km, days, runner):
    failures = []
    for weeks in range(config.WEEKS_MIN, config.WEEKS_MAX + 1):
        values = RUNNERS[runner]
        plan, inputs = make_plan(
            km=km,
            weeks=weeks,
            days=days,
            goal=int(values["stretch"]) - 10,
            rating=Rating.UNLIKELY,
            ten_k=values["today"],
            **values,
        )
        violations = check_plan_rules(plan, inputs)
        if violations:
            failures.append(f"{weeks} weeks: {violations}")
    assert failures == []


def test_short_plan_explains_hard_total():
    plan, inputs = make_plan(km=42.195, weeks=1, days=2)
    assert not config.PLAN_HARD_SHARE_MIN <= plan.total_hard_share <= config.PLAN_HARD_SHARE_MAX
    assert plan.hard_total_note
    assert check_plan_rules(plan, inputs) == []


def test_long_race_scales_hard_sessions_to_keep_total_in_range():
    plan, _ = make_plan(km=100.0, weeks=52, days=4)
    assert plan.total_hard_share <= config.PLAN_HARD_SHARE_MAX + 1e-9
    assert plan.hard_total_note is None
