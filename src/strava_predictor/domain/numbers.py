"""Rounding and pace/time conversion shared by the domain and the web layer."""

import re
from decimal import ROUND_HALF_UP, Decimal

from strava_predictor import config

_PACE_PATTERN = re.compile(r"^\s*(\d{1,2}):(\d{2})\s*$")


def round_half_up(value: float) -> int:
    """Round to the nearest whole number, halves away from zero (150.75 -> 151, 2.5 -> 3)."""
    return int(Decimal(str(value)).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def parse_pace(text: str) -> int:
    """Parse "m:ss" per km into seconds per km, within the accepted goal-pace range."""
    match = _PACE_PATTERN.match(text or "")
    if match is None:
        raise ValueError("Enter the pace as minutes:seconds, for example 4:50.")
    minutes, seconds = (int(part) for part in match.groups())
    if seconds >= config.SECONDS_PER_MINUTE:
        raise ValueError("Seconds must be from 00 to 59.")
    total = minutes * config.SECONDS_PER_MINUTE + seconds
    if not config.GOAL_PACE_MIN_S <= total <= config.GOAL_PACE_MAX_S:
        raise ValueError(
            f"Pace must be from {format_pace(config.GOAL_PACE_MIN_S)} "
            f"to {format_pace(config.GOAL_PACE_MAX_S)} per km."
        )
    return total


def format_pace(seconds_per_km: float) -> str:
    """Format seconds per km as m:ss, rounded to the nearest second."""
    total = round_half_up(seconds_per_km)
    minutes, seconds = divmod(total, config.SECONDS_PER_MINUTE)
    return f"{minutes}:{seconds:02d}"


def format_duration(seconds: float) -> str:
    """Format a duration as m:ss, or h:mm:ss from one hour, rounded to the nearest second."""
    total = round_half_up(seconds)
    hours, rest = divmod(total, config.SECONDS_PER_HOUR)
    minutes, secs = divmod(rest, config.SECONDS_PER_MINUTE)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"
