"""Taper length itself is covered by tests/unit/test_taper.py."""

import pytest

from strava_predictor.domain.models import Phase, SessionKind
from strava_predictor.domain.plan import phase_layout
from tests.unit.plan_helpers import make_plan

B, U, P, T = Phase.BASE, Phase.BUILD, Phase.PEAK, Phase.TAPER


@pytest.mark.parametrize(
    ("race_km", "weeks", "expected"),
    [
        (10.0, 1, (T,)),
        (5.0, 2, (P, T)),
        (10.0, 3, (U, P, T)),
        (10.0, 4, (B, U, P, T)),
        (42.195, 3, (P, T, T)),
        (42.195, 5, (U, P, T, T, T)),
        (10.0, 11, (B,) * 4 + (U,) * 4 + (P,) * 2 + (T,)),
        (10.0, 12, (B,) * 4 + (U,) * 5 + (P,) * 2 + (T,)),
        (21.0975, 7, (B,) * 2 + (U,) * 2 + (P,) + (T,) * 2),
    ],
)
def test_phase_layout(race_km, weeks, expected):
    assert phase_layout(race_km, weeks) == expected


@pytest.mark.parametrize("weeks", range(1, 53))
def test_base_never_longer_than_build(weeks):
    phases = phase_layout(10.0, weeks)
    assert phases.count(B) <= phases.count(U)
    assert list(phases) == sorted(phases, key=list(Phase).index)


def test_one_week_plan_is_a_single_race_week():
    plan, _ = make_plan(weeks=1)
    assert len(plan.weeks) == 1
    week = plan.weeks[0]
    assert week.is_race_week and week.phase == T
    assert week.sessions[-1].kind == SessionKind.RACE
