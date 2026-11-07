"""Effort classes from average heart rate (FR-017)."""

from strava_predictor import config
from strava_predictor.domain.models import EffortClass
from strava_predictor.domain.numbers import round_half_up


def effort_thresholds(max_hr: int) -> tuple[int, int]:
    """(highest easy bpm, lowest hard bpm), each rounded to the nearest whole bpm."""
    return (
        round_half_up(config.EASY_HR_FRACTION * max_hr),
        round_half_up(config.HARD_HR_FRACTION * max_hr),
    )


def classify_effort(avg_hr: int | None, max_hr: int) -> EffortClass:
    if avg_hr is None:
        return EffortClass.UNKNOWN
    easy_max, hard_min = effort_thresholds(max_hr)
    if avg_hr <= easy_max:
        return EffortClass.EASY
    if avg_hr >= hard_min:
        return EffortClass.HARD
    return EffortClass.MODERATE
