"""Today's race estimate and race-day projections (FR-019 to FR-025)."""

import math

from strava_predictor import config
from strava_predictor.domain.effort import classify_effort
from strava_predictor.domain.models import (
    Activity,
    DataError,
    DataErrorCode,
    DataSummary,
    EffortClass,
    Prediction,
    ProjectedResult,
    Projection,
    RunnerInputs,
)
from strava_predictor.domain.taper import taper_weeks

RATES = {
    Projection.SAFE: (config.WEEKLY_RATE_SAFE, config.IMPROVEMENT_CAP_SAFE),
    Projection.LIKELY: (config.WEEKLY_RATE_LIKELY, config.IMPROVEMENT_CAP_LIKELY),
    Projection.STRETCH: (config.WEEKLY_RATE_STRETCH, config.IMPROVEMENT_CAP_STRETCH),
}


def riegel(time_s: float, run_km: float, race_km: float) -> float:
    """Riegel formula: race time = run time x (race distance / run distance) ^ 1.06."""
    return time_s * (race_km / run_km) ** config.RIEGEL_EXPONENT


def _basis(runs: list[Activity], max_hr: int) -> tuple[list[Activity], int, bool]:
    """Runs behind today's estimate, the number of hard runs of 3 km+, and the fallback flag."""
    long_enough = [run for run in runs if run.distance_km >= config.MIN_PREDICTION_RUN_KM]
    hard = [run for run in long_enough if classify_effort(run.avg_hr, max_hr) == EffortClass.HARD]
    if hard:
        return hard, len(hard), False
    if not long_enough:
        raise DataError(
            DataErrorCode.NO_RUN_OVER_3KM,
            f"No run of at least {config.MIN_PREDICTION_RUN_KM:g} km was found, "
            "so no prediction can be made.",
        )
    return long_enough, 0, True


def _estimate(candidates: list[Activity], race_km: float) -> tuple[float, list[Activity]]:
    ranked = sorted(
        candidates, key=lambda run: riegel(run.moving_time_s, run.distance_km, race_km)
    )[: config.TOP_PREDICTIONS]
    times = [riegel(run.moving_time_s, run.distance_km, race_km) for run in ranked]
    return sum(times) / len(times), ranked


def rate_multiplier(summary: DataSummary) -> float:
    multiplier = 1.0
    if (
        summary.weeks_with_runs < config.MIN_ACTIVE_WEEKS
        or summary.avg_weekly_km_12 < config.LOW_VOLUME_KM
    ):
        multiplier *= config.LOW_VOLUME_MULTIPLIER
    if summary.avg_weekly_km_12 > config.HIGH_VOLUME_KM:
        multiplier *= config.HIGH_VOLUME_MULTIPLIER
    return multiplier


def long_run_target_km(race_km: float) -> float:
    """Target long run, interpolated linearly between the anchors and held to 8-35 km."""
    anchors = config.LONG_RUN_TARGETS
    segments = list(zip(anchors, anchors[1:], strict=False))
    (x0, y0), (x1, y1) = segments[0]
    for left, right in segments:
        if race_km >= left[0]:
            (x0, y0), (x1, y1) = left, right
    value = y0 + (race_km - x0) * (y1 - y0) / (x1 - x0)
    return min(max(value, config.LONG_RUN_MIN_KM), config.LONG_RUN_MAX_KM)


def predict(runs: list[Activity], summary: DataSummary, inputs: RunnerInputs) -> Prediction:
    race_km = inputs.race_distance_km
    candidates, hard_count, used_fallback = _basis(runs, inputs.max_hr)
    today_time, basis = _estimate(candidates, race_km)
    ten_k_time, _ = _estimate(candidates, config.TEN_K_KM)

    multiplier = rate_multiplier(summary)
    caps_applied = set()
    projected = {}
    for projection, (rate, cap) in RATES.items():
        improvement = rate * multiplier * inputs.weeks_to_race
        if improvement > cap + config.FLOAT_TOLERANCE:
            caps_applied.add(projection)
            improvement = cap
        projected[projection] = today_time * (1 - improvement)

    target = long_run_target_km(race_km)
    pre_taper = inputs.weeks_to_race - taper_weeks(race_km, inputs.weeks_to_race)
    reachable = summary.longest_run_km * (1 + config.LONG_RUN_GROWTH) ** pre_taper
    shortfall = max(0.0, (target - reachable) / target)
    steps = math.floor(shortfall / config.SHORTFALL_STEP + config.FLOAT_TOLERANCE)
    slowdown = steps * config.SLOWDOWN_PER_STEP

    def result(projection: Projection) -> ProjectedResult:
        time_s = projected[projection] * (1 + slowdown)
        return ProjectedResult(time_s=time_s, pace_s_per_km=time_s / race_km)

    return Prediction(
        race_distance_km=race_km,
        today_time_s=today_time,
        basis_runs=tuple(basis),
        hard_runs_used=hard_count,
        used_fallback=used_fallback,
        interval_only=all(run.is_interval for run in basis),
        rate_multiplier=multiplier,
        caps_applied=frozenset(caps_applied),
        long_run_target_km=target,
        reachable_long_run_km=reachable,
        distance_slowdown_pct=steps,
        safe=result(Projection.SAFE),
        likely=result(Projection.LIKELY),
        stretch=result(Projection.STRETCH),
        today_10k_pace_s_per_km=ten_k_time / config.TEN_K_KM,
    )
