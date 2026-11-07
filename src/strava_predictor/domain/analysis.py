"""Single entry point for the web layer: CSV or parsed runs in, full result out."""

from dataclasses import replace
from datetime import date

from strava_predictor.domain.models import Activity, AnalysisResult, RunnerInputs
from strava_predictor.domain.parsing import parse_activities
from strava_predictor.domain.plan import build_plan
from strava_predictor.domain.prediction import predict
from strava_predictor.domain.rating import rate_goal
from strava_predictor.domain.window import select_window


def analyse(
    source: str | list[Activity] | tuple[Activity, ...],
    inputs: RunnerInputs,
    reference_date: date,
) -> AnalysisResult:
    """Summary, prediction, and rating. Raises DataError when the data cannot support them."""
    activities = tuple(parse_activities(source) if isinstance(source, str) else source)
    runs, summary = select_window(activities, reference_date)
    prediction = predict(runs, summary, inputs)
    summary = replace(summary, hard_runs_used=prediction.hard_runs_used)
    rating = rate_goal(inputs.goal_pace_s_per_km, prediction, summary)
    plan = build_plan(prediction, rating, summary, inputs)
    return AnalysisResult(
        summary=summary, prediction=prediction, rating=rating, plan=plan, activities=activities
    )
