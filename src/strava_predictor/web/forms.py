"""Validate the input form (FR-002 to FR-007). Messages appear beside each field."""

import math
from dataclasses import dataclass, field

from strava_predictor import config
from strava_predictor.domain.models import RunnerInputs
from strava_predictor.domain.numbers import parse_pace

FIELDS = ("race_distance_km", "weeks_to_race", "goal_pace", "days_per_week", "max_hr")


@dataclass
class FormResult:
    values: dict[str, str]
    errors: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    inputs: RunnerInputs | None = None


def _whole(text: str, low: int, high: int, label: str) -> int:
    if not text.strip().isdigit():
        raise ValueError(f"Enter {label} as a whole number from {low} to {high}.")
    value = int(text)
    if not low <= value <= high:
        raise ValueError(f"{label.capitalize()} must be from {low} to {high}.")
    return value


def _distance(text: str) -> float:
    message = f"Enter a race distance above 0 and up to {config.RACE_KM_MAX:g} km."
    try:
        value = float(text)
    except ValueError:
        raise ValueError(message) from None
    if not math.isfinite(value) or not 0 < value <= config.RACE_KM_MAX:
        raise ValueError(message)
    return value


def validate(raw: dict[str, str]) -> FormResult:
    values = {name: (raw.get(name) or "").strip() for name in FIELDS}
    result = FormResult(values=values)
    parsed: dict[str, float | int] = {}
    checks = {
        "race_distance_km": _distance,
        "weeks_to_race": lambda text: _whole(
            text, config.WEEKS_MIN, config.WEEKS_MAX, "weeks to race"
        ),
        "goal_pace": parse_pace,
        "days_per_week": lambda text: _whole(
            text, config.DAYS_MIN, config.DAYS_MAX, "days per week"
        ),
        "max_hr": lambda text: _whole(text, config.MAX_HR_MIN, config.MAX_HR_MAX, "max heart rate"),
    }
    for name, check in checks.items():
        try:
            parsed[name] = check(values[name])
        except ValueError as error:
            result.errors[name] = str(error)

    distance = parsed.get("race_distance_km")
    if distance is not None and not config.RACE_KM_WARN_MIN <= distance <= config.RACE_KM_WARN_MAX:
        result.warnings.append(
            f"Predictions are less reliable for races under {config.RACE_KM_WARN_MIN:g} km "
            f"or over {config.RACE_KM_WARN_MAX:g} km."
        )
    weeks = parsed.get("weeks_to_race")
    if weeks is not None and weeks < config.WEEKS_WARN_MIN:
        result.warnings.append(
            f"With fewer than {config.WEEKS_WARN_MIN} weeks to go, there is little time to "
            "train; the plan focuses on staying fresh."
        )

    if not result.errors:
        result.inputs = RunnerInputs(
            race_distance_km=float(parsed["race_distance_km"]),
            weeks_to_race=int(parsed["weeks_to_race"]),
            goal_pace_s_per_km=int(parsed["goal_pace"]),
            days_per_week=int(parsed["days_per_week"]),
            max_hr=int(parsed["max_hr"]),
        )
    return result
