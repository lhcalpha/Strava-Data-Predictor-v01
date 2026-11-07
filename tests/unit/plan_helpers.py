"""Build plans from fixed synthetic predictions for plan tests."""

from strava_predictor.domain.models import (
    Confidence,
    GoalRating,
    Rating,
    RunnerInputs,
)
from strava_predictor.domain.plan import build_plan
from tests.unit.domain_helpers import prediction, summary


def make_plan(
    km=10.0,
    weeks=12,
    days=4,
    goal=290,
    rating=Rating.REALISTIC,
    avg4=30.0,
    avg12=30.0,
    longest=14.0,
    today=300.0,
    stretch=285.0,
    ten_k=300.0,
):
    inputs = RunnerInputs(km, weeks, goal, days, 201)
    pred = prediction(
        safe=today * 0.98,
        likely=today * 0.97,
        stretch=stretch,
        today=today,
        km=km,
        ten_k=ten_k,
    )
    data = summary(avg4=avg4, avg12=avg12, longest=longest)
    plan = build_plan(pred, GoalRating(rating, Confidence.NORMAL), data, inputs)
    return plan, inputs
