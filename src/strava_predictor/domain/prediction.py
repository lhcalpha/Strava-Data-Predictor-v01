"""Today's race estimate and race-day projections.

001 FR-019 to FR-021 and FR-024 to FR-025 give today's estimate and the distance-fitness slowdown;
002 FR-001 to FR-009 give the improvement curve, the personal trend, and safe/likely/stretch.
"""

import math
import statistics
from statistics import NormalDist

from strava_predictor import config
from strava_predictor.domain.effort import classify_effort
from strava_predictor.domain.models import (
    Activity,
    DataError,
    DataErrorCode,
    DataSummary,
    EffortClass,
    NoTrendReason,
    Prediction,
    ProjectedResult,
    RunnerInputs,
)
from strava_predictor.domain.taper import taper_weeks


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


def _trend(
    candidates: list[Activity], used_fallback: bool, race_km: float
) -> tuple[float | None, int, NoTrendReason | None]:
    """Weekly trend from the Theil-Sen slope of log race time against weeks (002 FR-002, FR-003).

    Returns the limited trend (positive means getting faster) or None, the runs considered, and
    why no trend was used.
    """
    if used_fallback:
        return None, 0, NoTrendReason.FALLBACK
    count = len(candidates)
    if count < config.TREND_MIN_RUNS:
        return None, count, NoTrendReason.TOO_FEW_RUNS
    dates = [run.date for run in candidates]
    if (max(dates) - min(dates)).days < config.TREND_MIN_SPAN_DAYS:
        return None, count, NoTrendReason.TOO_SHORT_SPAN
    points = sorted(
        (
            run.date.toordinal() / config.DAYS_PER_WEEK,
            math.log(riegel(run.moving_time_s, run.distance_km, race_km)),
        )
        for run in candidates
    )
    slopes = [
        (later_y - y) / (later_x - x)
        for index, (x, y) in enumerate(points)
        for later_x, later_y in points[index + 1 :]
        if later_x != x
    ]
    weekly = 1 - math.exp(statistics.median(slopes))
    return min(max(weekly, config.TREND_RATE_MIN), config.TREND_RATE_MAX), count, None


def _sigma_today(basis: list[Activity], race_km: float) -> float:
    """Uncertainty of today's estimate as a share of time (002 FR-006)."""
    doublings = sum(abs(math.log2(race_km / run.distance_km)) for run in basis) / len(basis)
    formula = config.RIEGEL_SIGMA_BASE + config.RIEGEL_SIGMA_PER_DOUBLING * doublings
    logs = [math.log(riegel(run.moving_time_s, run.distance_km, race_km)) for run in basis]
    spread = statistics.stdev(logs) if len(logs) > 1 else 0.0
    return math.hypot(formula, spread)


def predict(runs: list[Activity], summary: DataSummary, inputs: RunnerInputs) -> Prediction:
    race_km = inputs.race_distance_km
    weeks = inputs.weeks_to_race
    candidates, hard_count, used_fallback = _basis(runs, inputs.max_hr)
    today_time, basis = _estimate(candidates, race_km)
    ten_k_time, _ = _estimate(candidates, config.TEN_K_KM)

    # 002 FR-001 to FR-004: typical rate blended with the runner's own trend.
    multiplier = rate_multiplier(summary)
    typical = config.TYPICAL_WEEKLY_RATE * multiplier
    trend, trend_runs, no_trend_reason = _trend(candidates, used_fallback, race_km)
    weight = 0.0 if trend is None else trend_runs / (trend_runs + config.TREND_PRIOR_RUNS)
    measured = typical if trend is None else trend
    rate = max(0.0, weight * measured + (1 - weight) * typical)

    # 002 FR-005: improvement starts at the weekly rate and levels off at the limit.
    limit = config.MAX_IMPROVEMENT * multiplier
    decay = math.exp(-rate * weeks / limit)
    improvement = limit * (1 - decay)

    # 002 FR-006 to FR-008: log-normal spread; safe and stretch are its 80th and 20th percentiles.
    sigma_today = _sigma_today(basis, race_km)
    sigma_improvement = config.RATE_SIGMA * multiplier * math.sqrt(1 - weight) * weeks * decay
    sigma = math.hypot(sigma_today, sigma_improvement)
    spread = math.exp(NormalDist().inv_cdf(config.SAFE_PROBABILITY) * sigma)
    likely_time = today_time * (1 - improvement)

    # 001 FR-024 and FR-025, applied after the projection (002 FR-009).
    target = long_run_target_km(race_km)
    pre_taper = weeks - taper_weeks(race_km, weeks)
    reachable = summary.longest_run_km * (1 + config.LONG_RUN_GROWTH) ** pre_taper
    shortfall = max(0.0, (target - reachable) / target)
    steps = math.floor(shortfall / config.SHORTFALL_STEP + config.FLOAT_TOLERANCE)
    slowdown = steps * config.SLOWDOWN_PER_STEP

    def result(time_s: float) -> ProjectedResult:
        slowed = time_s * (1 + slowdown)
        return ProjectedResult(time_s=slowed, pace_s_per_km=slowed / race_km)

    return Prediction(
        race_distance_km=race_km,
        today_time_s=today_time,
        basis_runs=tuple(basis),
        hard_runs_used=hard_count,
        used_fallback=used_fallback,
        interval_only=all(run.is_interval for run in basis),
        rate_multiplier=multiplier,
        typical_rate=typical,
        trend_rate=trend,
        trend_runs=trend_runs,
        trend_weight=weight,
        no_trend_reason=no_trend_reason,
        weekly_rate=rate,
        max_improvement=limit,
        improvement=improvement,
        sigma_today=sigma_today,
        sigma_improvement=sigma_improvement,
        sigma=sigma,
        long_run_target_km=target,
        reachable_long_run_km=reachable,
        distance_slowdown_pct=steps,
        safe=result(likely_time * spread),
        likely=result(likely_time),
        stretch=result(likely_time / spread),
        today_10k_pace_s_per_km=ten_k_time / config.TEN_K_KM,
    )
