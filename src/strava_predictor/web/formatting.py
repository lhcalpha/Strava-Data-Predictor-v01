"""Jinja2 filters and plain-word labels that turn domain values into display text."""

from jinja2 import Environment

from strava_predictor import config
from strava_predictor.domain.effort import effort_thresholds
from strava_predictor.domain.models import (
    Confidence,
    ExclusionReason,
    NoTrendReason,
    Phase,
    Prediction,
    Rating,
    SessionKind,
)
from strava_predictor.domain.numbers import format_duration, format_pace

RATING_LABELS = {
    Rating.CONSERVATIVE: "Conservative",
    Rating.REALISTIC: "Realistic",
    Rating.AMBITIOUS: "Ambitious",
    Rating.VERY_AMBITIOUS: "Very ambitious",
    Rating.UNLIKELY: "Unlikely in this time",
}

RATING_EXPLANATIONS = {
    Rating.CONSERVATIVE: "Your goal is slower than the safe pace.",
    Rating.REALISTIC: "Your goal is between the safe and likely paces.",
    Rating.AMBITIOUS: "Your goal is faster than the likely pace, up to the stretch pace.",
    Rating.VERY_AMBITIOUS: "Your goal is up to 2% faster than the stretch pace.",
    Rating.UNLIKELY: "Your goal is more than 2% faster than the stretch pace.",
}

CONFIDENCE_LABELS = {Confidence.NORMAL: "Normal", Confidence.LOW: "Low"}

EXCLUSION_LABELS = {
    ExclusionReason.NOT_A_RUN: "Not a run (other activity types)",
    ExclusionReason.OUTSIDE_WINDOW: f"Outside the {config.WINDOW_WEEKS} weeks before today",
    ExclusionReason.NO_DISTANCE: "No usable distance",
    ExclusionReason.NO_MOVING_TIME: "No moving time",
    ExclusionReason.IMPLAUSIBLE_PACE: (
        f"Pace faster than {format_pace(config.PACE_PLAUSIBLE_MIN)} or slower than "
        f"{format_pace(config.PACE_PLAUSIBLE_MAX)} per km"
    ),
}

PHASE_LABELS = {
    Phase.BASE: "Base",
    Phase.BUILD: "Build",
    Phase.PEAK: "Peak",
    Phase.TAPER: "Taper",
}

SESSION_LABELS = {
    SessionKind.EASY: "Easy",
    SessionKind.LONG: "Long run",
    SessionKind.HARD: "Hard",
    SessionKind.RACE: "Race",
}


def km(value: float) -> str:
    return f"{value:.1f}"


def percent(value: float) -> str:
    return f"{value * config.PERCENT:.0f}%"


def rate_percent(value: float) -> str:
    """Weekly rates such as 0.003 shown as 0.30%."""
    return f"{value * config.PERCENT:.2f}%"


def percent1(value: float) -> str:
    return f"{value * config.PERCENT:.1f}%"


def _trend_note(prediction: Prediction) -> str:
    """How the weekly rate was found (002 FR-003, FR-004)."""
    typical = f"the typical rate of {rate_percent(prediction.typical_rate)} a week was used"
    reason = prediction.no_trend_reason
    if reason == NoTrendReason.FALLBACK:
        return f"No improvement trend was measured, because there were no hard runs; {typical}."
    if reason == NoTrendReason.TOO_FEW_RUNS:
        return (
            f"Measuring your own improvement trend needs at least {config.TREND_MIN_RUNS} hard "
            f"runs of {config.MIN_PREDICTION_RUN_KM:g} km or more; you have "
            f"{prediction.trend_runs}, so {typical}."
        )
    if reason == NoTrendReason.TOO_SHORT_SPAN:
        return (
            f"Your hard runs cover less than {config.TREND_MIN_SPAN_DAYS} days, too short to "
            f"measure your own trend, so {typical}."
        )
    trend = prediction.trend_rate
    direction = "faster" if trend >= 0 else "slower"
    weight = percent(prediction.trend_weight)
    typical_rate = rate_percent(prediction.typical_rate)
    note = (
        f"Your {prediction.trend_runs} hard runs show you getting {direction} by "
        f"{rate_percent(abs(trend))} a week. That trend was given {weight} of the weight against "
        f"the typical rate of {typical_rate}, giving {rate_percent(prediction.weekly_rate)} a week."
    )
    if prediction.weekly_rate == 0:
        note += " Because your recent trend is flat or slower, no improvement is projected."
    return note


def prediction_notes(prediction: Prediction) -> list[str]:
    """Plain-language notes on how the projections were adjusted (Constitution III)."""
    notes = []
    if prediction.interval_only:
        notes.append(
            "Every run behind today's estimate is an interval run. Whole-run pace includes the "
            "slow jogs, so the prediction is probably slower than your true fitness."
        )
    if prediction.rate_multiplier != 1.0:
        notes.append(
            f"The typical improvement rate and the improvement limit were multiplied by "
            f"{prediction.rate_multiplier:g} because of how much and how often you ran in the "
            "last 12 weeks."
        )
    notes.append(_trend_note(prediction))
    notes.append(
        f"Improvement starts at {rate_percent(prediction.weekly_rate)} a week and levels off as "
        f"gains get harder, up to at most {percent1(prediction.max_improvement)}; the likely "
        f"improvement by race day is {percent1(prediction.improvement)}."
    )
    if prediction.distance_slowdown_pct:
        notes.append(
            f"Your long run is expected to reach {km(prediction.reachable_long_run_km)} km, "
            f"short of the {km(prediction.long_run_target_km)} km target for this distance, "
            f"so all projected paces were slowed by {prediction.distance_slowdown_pct}%."
        )
    return notes


def register(env: Environment) -> None:
    env.filters["pace"] = format_pace
    env.filters["duration"] = format_duration
    env.filters["km"] = km
    env.filters["percent"] = percent
    env.filters["rate_percent"] = rate_percent
    env.globals["safe_chance"] = config.SAFE_PROBABILITY
    env.globals["RATING_LABELS"] = RATING_LABELS
    env.globals["RATING_EXPLANATIONS"] = RATING_EXPLANATIONS
    env.globals["CONFIDENCE_LABELS"] = CONFIDENCE_LABELS
    env.globals["PHASE_LABELS"] = PHASE_LABELS
    env.globals["EXCLUSION_LABELS"] = EXCLUSION_LABELS
    env.globals["effort_thresholds"] = effort_thresholds
    env.globals["SESSION_LABELS"] = SESSION_LABELS
    env.globals["prediction_notes"] = prediction_notes
