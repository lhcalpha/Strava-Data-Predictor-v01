"""Choose the runs inside the 12-week window and summarise the data (FR-009, FR-013 to FR-016)."""

from dataclasses import replace
from datetime import date

from strava_predictor import config
from strava_predictor.domain.models import (
    Activity,
    DataError,
    DataErrorCode,
    DataSummary,
    DataWarning,
    ExclusionReason,
)

WINDOW_DAYS = config.WINDOW_WEEKS * config.DAYS_PER_WEEK


def _exclusion(activity: Activity, reference_date: date) -> ExclusionReason | None:
    if activity.activity_type not in config.RUN_ACTIVITY_TYPES:
        return ExclusionReason.NOT_A_RUN
    age = (reference_date - activity.date).days
    if age < 0 or age >= WINDOW_DAYS:
        return ExclusionReason.OUTSIDE_WINDOW
    if activity.distance_km is None:
        return ExclusionReason.NO_DISTANCE
    if activity.moving_time_s is None:
        return ExclusionReason.NO_MOVING_TIME
    pace = activity.moving_time_s / activity.distance_km
    if not config.PACE_PLAUSIBLE_MIN <= pace <= config.PACE_PLAUSIBLE_MAX:
        return ExclusionReason.IMPLAUSIBLE_PACE
    return None


def select_window(
    activities: list[Activity] | tuple[Activity, ...], reference_date: date
) -> tuple[list[Activity], DataSummary]:
    """Return the usable runs and a summary. Raises DataError when fewer than 3 are usable."""
    used: list[Activity] = []
    excluded: dict[ExclusionReason, int] = {}
    for activity in activities:
        reason = _exclusion(activity, reference_date)
        if reason is None:
            used.append(activity)
        else:
            excluded[reason] = excluded.get(reason, 0) + 1

    if len(used) < config.MIN_USABLE_RUNS:
        raise DataError(
            DataErrorCode.TOO_FEW_RUNS,
            f"Only {len(used)} usable runs were found in the last {config.WINDOW_WEEKS} weeks; "
            f"at least {config.MIN_USABLE_RUNS} are needed.",
        )

    def week_of(run: Activity) -> int:
        return (reference_date - run.date).days // config.DAYS_PER_WEEK

    total_km = sum(run.distance_km for run in used)
    recent_km = sum(run.distance_km for run in used if week_of(run) < config.START_VOLUME_WEEKS)
    newest = max(run.date for run in used)
    warnings = []
    if (reference_date - newest).days > config.STALE_DATA_DAYS:
        warnings.append(
            DataWarning(
                "STALE_DATA",
                f"Your newest run is {(reference_date - newest).days} days old, so the data "
                "may be out of date.",
            )
        )

    summary = DataSummary(
        runs_used=len(used),
        excluded=excluded,
        runs_with_hr=sum(1 for run in used if run.avg_hr is not None),
        hard_runs_used=0,
        date_range=(min(run.date for run in used), newest),
        weeks_with_runs=len({week_of(run) for run in used}),
        avg_weekly_km_12=total_km / config.WINDOW_WEEKS,
        avg_weekly_km_4=recent_km / config.START_VOLUME_WEEKS,
        longest_run_km=max(run.distance_km for run in used),
        warnings=tuple(warnings),
    )
    return [replace(run, exclusion=None) for run in used], summary
