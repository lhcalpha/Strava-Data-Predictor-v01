"""Week-by-week 80/20 training plan (FR-028 to FR-037, research R13 to R16)."""

import math
import statistics
from collections.abc import Callable

from strava_predictor import config
from strava_predictor.domain.models import (
    DataSummary,
    GoalRating,
    Phase,
    PlanWeek,
    Prediction,
    Rating,
    RunnerInputs,
    Session,
    SessionKind,
    TrainingPlan,
)
from strava_predictor.domain.numbers import format_pace, round_half_up
from strava_predictor.domain.taper import taper_weeks

PHASE_ORDER = (Phase.BASE, Phase.BUILD, Phase.PEAK)
STRETCH_RATINGS = (Rating.VERY_AMBITIOUS, Rating.UNLIKELY)


# --- Structure -----------------------------------------------------------------------------


def phase_layout(race_km: float, weeks: int) -> tuple[Phase, ...]:
    """Phases in order. Peak takes 20% (at least one week), then build and base split the rest
    evenly with build rounded up, so short plans lose base weeks first (FR-030, R13)."""
    taper = taper_weeks(race_km, weeks)
    pre = weeks - taper
    peak = max(1, round_half_up(pre * config.PHASE_SHARE_PEAK)) if pre else 0
    rest = pre - peak
    build_share = config.PHASE_SHARE_BUILD / (config.PHASE_SHARE_BUILD + config.PHASE_SHARE_BASE)
    build = math.ceil(rest * build_share - config.FLOAT_TOLERANCE)
    base = rest - build
    return (
        (Phase.BASE,) * base
        + (Phase.BUILD,) * build
        + (Phase.PEAK,) * peak
        + (Phase.TAPER,) * taper
    )


# --- Volume --------------------------------------------------------------------------------


def start_volume(summary: DataSummary) -> tuple[float, list[str]]:
    """Average of the last 4 weeks (FR-031); the 12-week average if that is zero (R14)."""
    if summary.avg_weekly_km_4 > 0:
        return summary.avg_weekly_km_4, []
    return summary.avg_weekly_km_12, [
        f"You did not run in the last {config.START_VOLUME_WEEKS} weeks, so the plan starts "
        f"from your {config.WINDOW_WEEKS}-week weekly average."
    ]


def training_volumes(pre_taper_weeks: int, start_km: float) -> list[tuple[float, bool]]:
    """(training km, is lighter week) for each week before the taper (FR-032, R14)."""
    ceiling = start_km * config.PEAK_VOLUME_MULTIPLIER
    volumes: list[tuple[float, bool]] = []
    last_normal = None
    for number in range(1, pre_taper_weeks + 1):
        if number % config.LIGHTER_WEEK_EVERY == 0:
            volumes.append((volumes[-1][0] * (1 - config.LIGHTER_WEEK_CUT), True))
            continue
        km = (
            start_km
            if last_normal is None
            else min(last_normal * (1 + config.VOLUME_GROWTH_RATE), ceiling)
        )
        volumes.append((km, False))
        last_normal = km
    return volumes


def taper_volumes(reference_km: float, taper_length: int) -> list[float]:
    """Taper training km, each cut measured from the last normal pre-taper week (FR-029)."""
    return [reference_km * (1 - cut) for cut in config.TAPER_CUTS[taper_length]]


def last_normal_volume(volumes: list[tuple[float, bool]], start_km: float) -> float:
    normal = [km for km, lighter in volumes if not lighter]
    return normal[-1] if normal else start_km


# --- Paces ---------------------------------------------------------------------------------


def target_pace(goal_pace: float, prediction: Prediction) -> float:
    """Goal pace, never faster than stretch and never slower than today's pace (FR-028)."""
    stretch = prediction.stretch.pace_s_per_km
    return max(stretch, min(goal_pace, prediction.today_pace_s_per_km))


def hard_km_for_share(week_km: float, share: float, hard_pace: float, easy_pace: float) -> float:
    """Hard km so that hard time is `share` of the week, with the rest run at easy pace."""
    return share * week_km * easy_pace / (hard_pace * (1 - share) + share * easy_pace)


def _hard_paces(pre_taper: int, taper: int, start: float, target: float) -> list[float]:
    """Linear from today's pace to the target by the end of the peak, then held (FR-037)."""
    if pre_taper <= 1:
        return [target] * (pre_taper + taper)
    step = (target - start) / (pre_taper - 1)
    return [start + step * index for index in range(pre_taper)] + [target] * taper


# --- Sessions ------------------------------------------------------------------------------


def _days(count: int) -> list[int]:
    return [1 + index * config.DAYS_PER_WEEK // count for index in range(count)]


def _hard_sessions(phase: Phase, days: int) -> int:
    if days <= config.FEW_DAYS_PER_WEEK:
        return config.HARD_SESSIONS_FEW_DAYS
    return config.HARD_SESSIONS_BY_PHASE[phase]


def _order(hard: int, easy: int) -> list[SessionKind]:
    kinds: list[SessionKind] = []
    for _ in range(hard + easy):
        place_hard = hard and (not kinds or kinds[-1] != SessionKind.HARD or not easy)
        if place_hard:
            kinds.append(SessionKind.HARD)
            hard -= 1
        else:
            kinds.append(SessionKind.EASY)
            easy -= 1
    return kinds + [SessionKind.LONG]


def _training_week(
    number: int,
    phase: Phase,
    lighter: bool,
    km: float,
    long_km: float,
    hard_pace: float,
    easy_pace: float,
    share: float,
    days: int,
) -> PlanWeek:
    hard_count = _hard_sessions(phase, days)
    easy_count = days - 1 - hard_count
    hard_km = hard_km_for_share(km, share, hard_pace, easy_pace)
    pool = km - long_km - hard_km
    full = config.WARMUP_KM + config.COOLDOWN_KM
    if easy_count:
        extra = min(full, pool / (hard_count + easy_count))
        easy_km = (pool - hard_count * extra) / easy_count
    else:
        extra, easy_km = pool / hard_count, 0.0
    warmup = extra * config.WARMUP_KM / full
    cooldown = extra * config.COOLDOWN_KM / full
    each_hard = hard_km / hard_count

    sessions = []
    for day, kind in zip(_days(days), _order(hard_count, easy_count), strict=True):
        if kind == SessionKind.HARD:
            sessions.append(
                Session(day, kind, extra + each_hard, hard_pace, each_hard, warmup, cooldown)
            )
        elif kind == SessionKind.LONG:
            sessions.append(Session(day, kind, long_km, easy_pace))
        else:
            sessions.append(Session(day, kind, easy_km, easy_pace))

    hard_time = hard_km * hard_pace
    total_time = hard_time + (km - hard_km) * easy_pace
    return PlanWeek(
        number=number,
        phase=phase,
        is_lighter=lighter,
        is_race_week=False,
        training_km=km,
        total_km=km,
        total_time_s=total_time,
        hard_time_s=hard_time,
        hard_pace_s_per_km=hard_pace,
        long_run_km=long_km,
        sessions=tuple(sessions),
    )


def _race_week(
    number: int, km: float, race_km: float, target: float, easy_pace: float, days: int
) -> PlanWeek:
    easy_count = days - 1
    kinds = [SessionKind.EASY] * easy_count + [SessionKind.RACE]
    sessions = tuple(
        Session(day, kind, race_km if kind == SessionKind.RACE else km / easy_count,
                target if kind == SessionKind.RACE else easy_pace)
        for day, kind in zip(_days(days), kinds, strict=True)
    )  # fmt: skip
    race_time = race_km * target
    return PlanWeek(
        number=number,
        phase=Phase.TAPER,
        is_lighter=False,
        is_race_week=True,
        training_km=km,
        total_km=km + race_km,
        total_time_s=km * easy_pace + race_time,
        hard_time_s=race_time,
        hard_pace_s_per_km=target,
        long_run_km=0.0,
        sessions=sessions,
    )


def _long_runs(volumes: list[tuple[float, bool]], longest: float, target: float) -> list[float]:
    """Long run starts at the longest recent run and grows up to 10% a normal week toward the
    target; it never exceeds half the week's training distance (R15)."""
    progress = longest
    runs = []
    for index, (km, lighter) in enumerate(volumes):
        if index and not lighter and progress < target:
            progress = min(progress * (1 + config.LONG_RUN_GROWTH), target)
        runs.append(min(progress, km * config.LONG_RUN_MAX_SHARE))
    return runs


def total_hard_share(weeks: tuple[PlanWeek, ...]) -> float:
    return sum(week.hard_time_s for week in weeks) / sum(week.total_time_s for week in weeks)


def _fit_total(build: Callable[[float], tuple[PlanWeek, ...]]) -> tuple[PlanWeek, ...]:
    """Scale training hard shares down when the race pushes the plan total over the maximum."""
    weeks = build(1.0)
    limit = config.PLAN_HARD_SHARE_MAX
    if total_hard_share(weeks) <= limit or total_hard_share(build(0.0)) > limit:
        return weeks
    low, high = 0.0, 1.0
    for _ in range(config.HARD_SHARE_SEARCH_STEPS):
        middle = statistics.fmean((low, high))
        if total_hard_share(build(middle)) <= limit:
            low = middle
        else:
            high = middle
    return build(low)


def build_plan(
    prediction: Prediction, rating: GoalRating, summary: DataSummary, inputs: RunnerInputs
) -> TrainingPlan:
    race_km, days = inputs.race_distance_km, inputs.days_per_week
    phases = phase_layout(race_km, inputs.weeks_to_race)
    taper = phases.count(Phase.TAPER)
    pre = len(phases) - taper

    start_km, notes = start_volume(summary)
    pre_volumes = training_volumes(pre, start_km)
    tapers = taper_volumes(last_normal_volume(pre_volumes, start_km), taper)
    volumes = pre_volumes + [(km, False) for km in tapers]
    long_runs = _long_runs(volumes, summary.longest_run_km, prediction.long_run_target_km)

    stretch = prediction.stretch.pace_s_per_km
    target = target_pace(inputs.goal_pace_s_per_km, prediction)
    start_hard = max(prediction.today_pace_s_per_km, stretch)
    hard_paces = _hard_paces(pre, taper, start_hard, target)
    ten_k = prediction.today_10k_pace_s_per_km
    easy_range = (config.EASY_PACE_FACTOR_MIN * ten_k, config.EASY_PACE_FACTOR_MAX * ten_k)
    easy = easy_range[0]

    def build(scale: float) -> tuple[PlanWeek, ...]:
        weeks = []
        for index, phase in enumerate(phases):
            km, lighter = volumes[index]
            if index == len(phases) - 1:
                weeks.append(_race_week(index + 1, km, race_km, target, easy, days))
            else:
                share = config.HARD_SHARE_BY_PHASE[phase] * scale
                weeks.append(
                    _training_week(
                        index + 1, phase, lighter, km, long_runs[index],
                        hard_paces[index], easy, share, days,
                    )
                )  # fmt: skip
        return tuple(weeks)

    weeks = _fit_total(build)
    total = total_hard_share(weeks)

    targets_stretch = rating.rating in STRETCH_RATINGS
    if targets_stretch:
        notes.append(
            "Your goal is faster than the projections support, so training targets the stretch "
            f"pace ({format_pace(target)} per km)."
        )
    hard_total_note = None
    if not (
        config.PLAN_HARD_SHARE_MIN - config.FLOAT_TOLERANCE
        <= total
        <= config.PLAN_HARD_SHARE_MAX + config.FLOAT_TOLERANCE
    ):
        band = f"{config.PLAN_HARD_SHARE_MIN * config.PERCENT:g}–"
        band += f"{config.PLAN_HARD_SHARE_MAX * config.PERCENT:g}%"
        hard_total_note = (
            f"Hard time is {total * config.PERCENT:.0f}% of this plan, outside the {band} range, "
            "because the race counts as hard time and the plan is too short to balance it."
        )

    return TrainingPlan(
        target_pace_s_per_km=target,
        targets_stretch=targets_stretch,
        stretch_pace_s_per_km=stretch,
        today_10k_pace_s_per_km=ten_k,
        easy_pace_range=easy_range,
        start_km=start_km,
        weeks=weeks,
        total_hard_share=total,
        notes=tuple(notes),
        hard_total_note=hard_total_note,
    )
