"""Taper length, shared by the prediction (distance fitness) and the plan (FR-029, R13)."""

from strava_predictor import config


def standard_taper_weeks(race_km: float) -> int:
    for up_to_km, weeks in config.TAPER_WEEKS_BY_DISTANCE:
        if race_km <= up_to_km:
            return weeks
    return config.TAPER_WEEKS_LONG_RACE


def taper_weeks(race_km: float, weeks_to_race: int) -> int:
    """Standard taper, shortened to leave one week before it; a 1-week plan is all taper."""
    return min(standard_taper_weeks(race_km), max(1, weeks_to_race - 1))
