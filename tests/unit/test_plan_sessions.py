import pytest

from strava_predictor.domain.models import Phase, SessionKind
from tests.unit.plan_helpers import make_plan

HARD_BY_PHASE = {Phase.BASE: 1, Phase.BUILD: 2, Phase.PEAK: 2, Phase.TAPER: 1}


@pytest.mark.parametrize("days", range(2, 8))
def test_session_counts_and_kinds(days):
    plan, _ = make_plan(weeks=12, days=days)
    for week in plan.weeks:
        kinds = [session.kind for session in week.sessions]
        assert len(kinds) == days
        if week.is_race_week:
            assert kinds[-1] == SessionKind.RACE
            assert kinds.count(SessionKind.RACE) == 1
            assert SessionKind.LONG not in kinds and SessionKind.HARD not in kinds
        else:
            assert kinds.count(SessionKind.LONG) == 1
            expected_hard = 1 if days <= 3 else HARD_BY_PHASE[week.phase]
            assert kinds.count(SessionKind.HARD) == expected_hard
            assert SessionKind.RACE not in kinds


def test_two_days_is_long_run_and_hard_session():
    plan, _ = make_plan(days=2)
    assert {s.kind for s in plan.weeks[0].sessions} == {SessionKind.LONG, SessionKind.HARD}


def test_hard_session_parts():
    plan, _ = make_plan(days=5, avg4=40.0)
    for week in plan.weeks:
        for session in week.sessions:
            if session.kind == SessionKind.HARD:
                parts = session.warmup_km + session.hard_km + session.cooldown_km
                assert session.distance_km == pytest.approx(parts)
                assert session.warmup_km == pytest.approx(2.0)
                assert session.cooldown_km == pytest.approx(1.5)


def test_short_weeks_shrink_warm_ups_proportionally():
    plan, _ = make_plan(days=7, avg4=8.0, longest=4.0)
    hard = [s for s in plan.weeks[0].sessions if s.kind == SessionKind.HARD]
    assert hard
    for session in hard:
        assert 0 < session.warmup_km < 2.0
        assert session.warmup_km / session.cooldown_km == pytest.approx(2.0 / 1.5)


def test_long_run_growth_and_share():
    plan, _ = make_plan(km=42.195, weeks=20, days=5, avg4=40.0, longest=14.0)
    previous_normal = None
    for week in plan.weeks:
        assert week.long_run_km <= 0.5 * week.training_km + 1e-9
        if week.phase == Phase.TAPER or week.is_lighter:
            continue
        if previous_normal is not None:
            assert week.long_run_km <= previous_normal * 1.1 + 1e-9
        previous_normal = week.long_run_km


def test_long_run_stops_at_target():
    plan, _ = make_plan(km=10.0, weeks=20, avg4=60.0, longest=10.0)
    assert max(week.long_run_km for week in plan.weeks) == pytest.approx(12.0)


@pytest.mark.parametrize(
    ("days", "expected"),
    [(2, [1, 4]), (3, [1, 3, 5]), (4, [1, 2, 4, 6]), (7, [1, 2, 3, 4, 5, 6, 7])],
)
def test_days_are_spread_over_the_week(days, expected):
    plan, _ = make_plan(days=days)
    assert [s.day for s in plan.weeks[0].sessions] == expected


def test_week_totals_add_up():
    plan, _ = make_plan(days=6, km=21.0975, weeks=14)
    for week in plan.weeks:
        assert sum(s.distance_km for s in week.sessions) == pytest.approx(week.total_km)
