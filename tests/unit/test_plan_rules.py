from dataclasses import replace

from strava_predictor.domain.models import SessionKind
from strava_predictor.domain.plan_rules import check_plan_rules
from tests.unit.plan_helpers import make_plan


def _codes(plan, inputs):
    return {violation.split(":")[0] for violation in check_plan_rules(plan, inputs)}


def _replace_week(plan, index, **changes):
    weeks = list(plan.weeks)
    weeks[index] = replace(weeks[index], **changes)
    return replace(plan, weeks=tuple(weeks))


def test_valid_plan_has_no_violations():
    plan, inputs = make_plan(weeks=16, days=5)
    assert check_plan_rules(plan, inputs) == []


def test_volume_rise_over_ten_percent():
    plan, inputs = make_plan(weeks=12)
    first = plan.weeks[0].training_km
    broken = _replace_week(plan, 1, training_km=first * 1.11)
    assert "VOLUME_RISE" in _codes(broken, inputs)


def test_lighter_week_not_light_enough():
    plan, inputs = make_plan(weeks=12)
    before = plan.weeks[2].training_km
    broken = _replace_week(plan, 3, training_km=before * 0.85)
    assert "LIGHTER_WEEK" in _codes(broken, inputs)


def test_missing_lighter_week():
    plan, inputs = make_plan(weeks=12)
    broken = _replace_week(plan, 3, is_lighter=False)
    assert "LIGHTER_WEEK" in _codes(broken, inputs)


def test_wrong_session_count():
    plan, inputs = make_plan(weeks=12, days=4)
    broken = _replace_week(plan, 0, sessions=plan.weeks[0].sessions[:3])
    assert "SESSION_COUNT" in _codes(broken, inputs)


def test_two_long_runs():
    plan, inputs = make_plan(weeks=12, days=4)
    sessions = list(plan.weeks[0].sessions)
    sessions[0] = replace(sessions[0], kind=SessionKind.LONG)
    broken = _replace_week(plan, 0, sessions=tuple(sessions))
    assert "LONG_RUN_COUNT" in _codes(broken, inputs)


def test_weekly_hard_share_over_twenty_percent():
    plan, inputs = make_plan(weeks=12)
    week = plan.weeks[0]
    broken = _replace_week(plan, 0, hard_time_s=week.total_time_s * 0.21)
    assert "WEEKLY_HARD_SHARE" in _codes(broken, inputs)


def test_plan_total_too_low():
    plan, inputs = make_plan(weeks=12)
    broken = replace(plan, total_hard_share=0.14)
    assert "PLAN_HARD_SHARE" in _codes(broken, inputs)


def test_hard_pace_faster_than_stretch():
    plan, inputs = make_plan(weeks=12)
    broken = _replace_week(plan, 2, hard_pace_s_per_km=plan.stretch_pace_s_per_km - 1)
    assert "HARD_PACE_TOO_FAST" in _codes(broken, inputs)


def test_easy_pace_from_goal():
    plan, inputs = make_plan(weeks=12)
    broken = replace(plan, easy_pace_range=(250.0, 260.0))
    assert "EASY_PACE" in _codes(broken, inputs)


def test_race_not_last():
    plan, inputs = make_plan(weeks=12, days=4)
    sessions = list(plan.weeks[-1].sessions)
    sessions[0], sessions[-1] = sessions[-1], sessions[0]
    broken = _replace_week(plan, len(plan.weeks) - 1, sessions=tuple(sessions))
    assert "RACE_NOT_LAST" in _codes(broken, inputs)


def test_wrong_number_of_weeks():
    plan, inputs = make_plan(weeks=12)
    broken = replace(plan, weeks=plan.weeks[:-1])
    assert "WEEK_COUNT" in _codes(broken, inputs)


def test_wrong_taper_cut():
    plan, inputs = make_plan(weeks=12)
    broken = _replace_week(plan, 11, training_km=plan.weeks[11].training_km * 1.2)
    assert "TAPER" in _codes(broken, inputs)


def test_long_run_over_half_the_week():
    plan, inputs = make_plan(weeks=12)
    broken = _replace_week(plan, 0, long_run_km=plan.weeks[0].training_km * 0.6)
    assert "LONG_RUN_SHARE" in _codes(broken, inputs)


def test_session_distances_do_not_add_up():
    plan, inputs = make_plan(weeks=12)
    broken = _replace_week(plan, 0, total_km=plan.weeks[0].total_km + 5)
    assert "DISTANCE_SUM" in _codes(broken, inputs)


def test_first_week_not_starting_distance():
    plan, inputs = make_plan(weeks=12)
    broken = replace(plan, start_km=plan.start_km + 3)
    assert "FIRST_WEEK" in _codes(broken, inputs)
