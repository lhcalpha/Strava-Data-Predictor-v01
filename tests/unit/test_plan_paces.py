import pytest

from strava_predictor.domain.models import Phase, Rating, SessionKind
from strava_predictor.domain.plan import hard_km_for_share, target_pace
from tests.unit.domain_helpers import prediction
from tests.unit.plan_helpers import make_plan


def test_easy_pace_range_from_ten_k_and_not_the_goal():
    fast_goal, _ = make_plan(goal=250, ten_k=300.0)
    slow_goal, _ = make_plan(goal=320, ten_k=300.0)
    assert fast_goal.easy_pace_range == pytest.approx((354.0, 381.0))
    assert slow_goal.easy_pace_range == fast_goal.easy_pace_range
    for week in fast_goal.weeks:
        for session in week.sessions:
            if session.kind in (SessionKind.EASY, SessionKind.LONG):
                assert session.pace_s_per_km == pytest.approx(354.0)


@pytest.mark.parametrize(
    ("goal", "expected"),
    [(290, 290), (285, 285), (280, 285), (300, 300), (310, 300)],
)
def test_target_pace_is_clamped(goal, expected):
    assert target_pace(goal, prediction(stretch=285.0, today=300.0)) == expected


def test_target_never_faster_than_stretch_even_when_stretch_is_slower_than_today():
    assert target_pace(280, prediction(stretch=305.0, today=300.0)) == 305.0


@pytest.mark.parametrize(
    ("rating", "expected"),
    [
        (Rating.AMBITIOUS, False),
        (Rating.VERY_AMBITIOUS, True),
        (Rating.UNLIKELY, True),
    ],
)
def test_targets_stretch_note(rating, expected):
    plan, _ = make_plan(goal=270, rating=rating)
    assert plan.targets_stretch is expected
    assert any("stretch pace" in note for note in plan.notes) is expected


def test_hard_pace_moves_linearly_then_holds():
    plan, _ = make_plan(weeks=12, goal=290, today=300.0, stretch=285.0)
    pre = [w.hard_pace_s_per_km for w in plan.weeks if w.phase != Phase.TAPER]
    assert pre[0] == pytest.approx(300.0)
    assert pre[-1] == pytest.approx(290.0)
    steps = [b - a for a, b in zip(pre, pre[1:], strict=False)]
    assert steps == pytest.approx([steps[0]] * len(steps))
    taper = [w.hard_pace_s_per_km for w in plan.weeks if w.phase == Phase.TAPER]
    assert taper == pytest.approx([290.0] * len(taper))


def test_hard_pace_never_faster_than_stretch():
    plan, _ = make_plan(goal=200, rating=Rating.UNLIKELY, stretch=285.0)
    for week in plan.weeks:
        for session in week.sessions:
            if session.kind == SessionKind.HARD:
                assert session.pace_s_per_km >= 285.0 - 1e-9


def test_hard_km_formula():
    hard = hard_km_for_share(40.0, 0.18, 290.0, 354.0)
    expected = 0.18 * 40.0 * 354.0 / (290.0 * 0.82 + 0.18 * 354.0)
    assert hard == pytest.approx(expected, abs=0.01)
    time_hard = hard * 290.0
    time_total = time_hard + (40.0 - hard) * 354.0
    assert time_hard / time_total == pytest.approx(0.18)


def test_weekly_hard_share_matches_phase():
    plan, _ = make_plan(weeks=12, days=5)
    shares = {"BASE": 0.15, "BUILD": 0.18, "PEAK": 0.19, "TAPER": 0.15}
    for week in plan.weeks:
        if not week.is_race_week:
            assert week.hard_share == pytest.approx(shares[week.phase])
