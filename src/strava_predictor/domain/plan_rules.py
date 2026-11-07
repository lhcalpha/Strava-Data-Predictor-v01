"""Check a plan against every plan rule (FR-028 to FR-037). Used by the plan tests (SC-003).

Each violation is "CODE: detail". An empty list means the plan obeys every rule.
"""

from strava_predictor import config
from strava_predictor.domain.models import (
    Phase,
    PlanWeek,
    RunnerInputs,
    SessionKind,
    TrainingPlan,
)
from strava_predictor.domain.plan import total_hard_share
from strava_predictor.domain.taper import taper_weeks

TOL = config.FLOAT_TOLERANCE
RELATIVE_TOL = config.RELATIVE_TOLERANCE


def _close(a: float, b: float) -> bool:
    return abs(a - b) <= RELATIVE_TOL * max(1.0, abs(a), abs(b))


def _structure(plan: TrainingPlan, inputs: RunnerInputs) -> list[str]:
    problems = []
    if len(plan.weeks) != inputs.weeks_to_race:
        problems.append(f"WEEK_COUNT: {len(plan.weeks)} weeks, expected {inputs.weeks_to_race}")
    order = [Phase.BASE, Phase.BUILD, Phase.PEAK, Phase.TAPER]
    phases = [week.phase for week in plan.weeks]
    if phases != sorted(phases, key=order.index):
        problems.append("TAPER: phases are out of order")
    expected_taper = taper_weeks(inputs.race_distance_km, inputs.weeks_to_race)
    if phases.count(Phase.TAPER) != expected_taper:
        problems.append(
            f"TAPER: {phases.count(Phase.TAPER)} taper weeks, expected {expected_taper}"
        )
    return problems


def _sessions(week: PlanWeek, inputs: RunnerInputs, last: bool) -> list[str]:
    problems = []
    kinds = [session.kind for session in week.sessions]
    if len(kinds) != inputs.days_per_week:
        problems.append(f"SESSION_COUNT: week {week.number} has {len(kinds)} sessions")
    long_expected = 0 if last else 1
    if kinds.count(SessionKind.LONG) != long_expected:
        problems.append(f"LONG_RUN_COUNT: week {week.number} has {kinds.count('LONG')} long runs")
    if last:
        race_ok = kinds and kinds[-1] == SessionKind.RACE and kinds.count(SessionKind.RACE) == 1
        if not race_ok or not _close(week.sessions[-1].distance_km, inputs.race_distance_km):
            problems.append("RACE_NOT_LAST: the final week must end with the race")
    elif SessionKind.RACE in kinds:
        problems.append(f"RACE_NOT_LAST: week {week.number} contains a race")
    if any(session.distance_km <= 0 for session in week.sessions):
        problems.append(f"DISTANCE_SUM: week {week.number} has an empty session")
    if not _close(sum(s.distance_km for s in week.sessions), week.total_km):
        problems.append(f"DISTANCE_SUM: week {week.number} sessions do not add up")
    race = inputs.race_distance_km if last else 0.0
    if not _close(week.total_km - race, week.training_km):
        problems.append(f"DISTANCE_SUM: week {week.number} training km is wrong")
    if not last and week.long_run_km > week.training_km * config.LONG_RUN_MAX_SHARE + TOL:
        problems.append(f"LONG_RUN_SHARE: week {week.number} long run is over half the week")
    return problems


def _volume(plan: TrainingPlan) -> list[str]:
    problems = []
    pre = [week for week in plan.weeks if week.phase != Phase.TAPER]
    if pre and not _close(pre[0].training_km, plan.start_km):
        problems.append("FIRST_WEEK: the first week must use the starting weekly distance")
    last_normal = None
    previous = None
    for index, week in enumerate(pre, start=1):
        should_be_lighter = index % config.LIGHTER_WEEK_EVERY == 0
        if week.is_lighter != should_be_lighter:
            problems.append(f"LIGHTER_WEEK: week {week.number} lighter flag is wrong")
        if should_be_lighter and previous is not None:
            low = previous * (1 - config.LIGHTER_WEEK_CUT_MAX) - TOL
            high = previous * (1 - config.LIGHTER_WEEK_CUT_MIN) + TOL
            if not low <= week.training_km <= high:
                problems.append(f"LIGHTER_WEEK: week {week.number} is not 20-25% lighter")
        elif last_normal is not None and (
            week.training_km > last_normal * (1 + config.MAX_WEEKLY_INCREASE) + TOL
        ):
            problems.append(f"VOLUME_RISE: week {week.number} rises over 10%")
        if not week.is_lighter:
            last_normal = week.training_km
        previous = week.training_km

    reference = last_normal if last_normal is not None else plan.start_km
    taper = [week for week in plan.weeks if week.phase == Phase.TAPER]
    cuts = config.TAPER_CUTS.get(len(taper), ())
    for week, cut in zip(taper, cuts, strict=False):
        if not _close(week.training_km, reference * (1 - cut)):
            problems.append(f"TAPER: week {week.number} does not follow the taper cut")
    return problems


def _effort(plan: TrainingPlan) -> list[str]:
    problems = []
    for week in plan.weeks:
        if not week.is_race_week and week.hard_share > config.MAX_WEEKLY_HARD_SHARE + TOL:
            problems.append(f"WEEKLY_HARD_SHARE: week {week.number} is over 20% hard")
        hard_paces = [week.hard_pace_s_per_km] + [
            s.pace_s_per_km for s in week.sessions if s.kind == SessionKind.HARD
        ]
        if min(hard_paces) < plan.stretch_pace_s_per_km - TOL:
            problems.append(f"HARD_PACE_TOO_FAST: week {week.number} beats the stretch pace")
        for session in week.sessions:
            if session.kind in (SessionKind.EASY, SessionKind.LONG) and not _close(
                session.pace_s_per_km, plan.easy_pace_range[0]
            ):
                problems.append(f"EASY_PACE: week {week.number} easy pace is wrong")

    ten_k = plan.today_10k_pace_s_per_km
    expected = (config.EASY_PACE_FACTOR_MIN * ten_k, config.EASY_PACE_FACTOR_MAX * ten_k)
    if not all(_close(a, b) for a, b in zip(plan.easy_pace_range, expected, strict=True)):
        problems.append("EASY_PACE: easy pace must come from today's 10 km pace")
    if plan.target_pace_s_per_km < plan.stretch_pace_s_per_km - TOL:
        problems.append("HARD_PACE_TOO_FAST: the training target beats the stretch pace")

    total = plan.total_hard_share
    if plan.weeks and not _close(total, total_hard_share(plan.weeks)):
        problems.append("PLAN_HARD_SHARE: the stated total does not match the weeks")
    in_range = config.PLAN_HARD_SHARE_MIN - TOL <= total <= config.PLAN_HARD_SHARE_MAX + TOL
    if not in_range and not plan.hard_total_note:
        problems.append(f"PLAN_HARD_SHARE: total {total:.3f} is outside 15-20% without a note")
    return problems


def check_plan_rules(plan: TrainingPlan, inputs: RunnerInputs) -> list[str]:
    problems = _structure(plan, inputs)
    for index, week in enumerate(plan.weeks):
        problems += _sessions(week, inputs, last=index == len(plan.weeks) - 1)
    problems += _volume(plan)
    problems += _effort(plan)
    return problems
