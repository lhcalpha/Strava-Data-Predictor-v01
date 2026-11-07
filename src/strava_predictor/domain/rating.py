"""Goal rating and confidence (FR-026, FR-027, research R11)."""

from strava_predictor import config
from strava_predictor.domain.models import (
    Confidence,
    DataSummary,
    GoalRating,
    Prediction,
    Rating,
)


def _rating(goal: float, prediction: Prediction) -> Rating:
    tolerance = config.FLOAT_TOLERANCE
    safe = prediction.safe.pace_s_per_km
    likely = prediction.likely.pace_s_per_km
    stretch = prediction.stretch.pace_s_per_km
    if goal > safe + tolerance:
        return Rating.CONSERVATIVE
    if goal >= likely - tolerance:
        return Rating.REALISTIC
    if goal >= stretch - tolerance:
        return Rating.AMBITIOUS
    if goal >= stretch * (1 - config.VERY_AMBITIOUS_MARGIN) - tolerance:
        return Rating.VERY_AMBITIOUS
    return Rating.UNLIKELY


def _confidence_reasons(prediction: Prediction, summary: DataSummary) -> list[str]:
    reasons = []
    km = f"{config.MIN_PREDICTION_RUN_KM:g} km"
    if prediction.used_fallback:
        reasons.append(
            f"There were no hard runs of {km} or more, so the estimate uses your fastest runs."
        )
    elif prediction.hard_runs_used < config.MIN_HARD_RUNS_FOR_CONFIDENCE:
        reasons.append(
            f"Only {prediction.hard_runs_used} hard runs of {km} or more were found; "
            f"at least {config.MIN_HARD_RUNS_FOR_CONFIDENCE} are needed."
        )
    if summary.runs_with_hr < summary.runs_used * config.MIN_HR_SHARE:
        reasons.append(
            f"Only {summary.runs_with_hr} of {summary.runs_used} runs have a usable heart rate; "
            "at least half are needed."
        )
    return reasons


def rate_goal(
    goal_pace_s_per_km: float, prediction: Prediction, summary: DataSummary
) -> GoalRating:
    reasons = _confidence_reasons(prediction, summary)
    return GoalRating(
        rating=_rating(goal_pace_s_per_km, prediction),
        confidence=Confidence.LOW if reasons else Confidence.NORMAL,
        confidence_reasons=tuple(reasons),
    )
