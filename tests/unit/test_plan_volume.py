import pytest

from strava_predictor.domain.plan import taper_volumes, training_volumes
from tests.unit.plan_helpers import make_plan


def test_volumes_grow_lighten_and_taper():
    plan, _ = make_plan(km=10.0, weeks=12, avg4=30.0)
    km = [week.training_km for week in plan.weeks]
    expected = [30.0, 32.4, 34.992, 34.992 * 0.775, 37.79136, 40.8146688]
    assert km[:6] == pytest.approx(expected)
    assert km[6] == pytest.approx(44.07984230)
    assert km[7] == pytest.approx(44.07984230 * 0.775)
    assert km[8:11] == pytest.approx([45.0, 45.0, 45.0])  # ceiling: 1.5 x 30
    assert km[11] == pytest.approx(45.0 * 0.6)
    assert [week.is_lighter for week in plan.weeks] == [
        False, False, False, True, False, False, False, True, False, False, False, False,
    ]  # fmt: skip


def test_start_is_last_four_week_average():
    plan, _ = make_plan(avg4=22.0, avg12=40.0)
    assert plan.start_km == 22.0
    assert plan.weeks[0].training_km == 22.0


def test_zero_recent_volume_falls_back_with_a_note():
    plan, _ = make_plan(avg4=0.0, avg12=12.0)
    assert plan.start_km == 12.0
    assert any("last 4 weeks" in note for note in plan.notes)


def test_week_after_lighter_week_compares_with_last_normal_week():
    volumes = training_volumes(8, 30.0)
    assert volumes[4][0] <= volumes[2][0] * 1.1
    assert volumes[4][0] == pytest.approx(volumes[2][0] * 1.08)


@pytest.mark.parametrize(
    ("taper", "expected"),
    [(1, [30.0]), (2, [37.5, 25.0]), (3, [40.0, 32.5, 22.5])],
)
def test_taper_cuts_from_last_peak_week(taper, expected):
    assert taper_volumes(50.0, taper) == pytest.approx(expected)


def test_marathon_taper_in_a_full_plan():
    plan, _ = make_plan(km=42.195, weeks=16, avg4=40.0, longest=25.0)
    pre_taper = [w for w in plan.weeks if w.phase != "TAPER"]
    last_normal = [w for w in pre_taper if not w.is_lighter][-1].training_km
    taper = [w.training_km for w in plan.weeks if w.phase == "TAPER"]
    assert taper == pytest.approx([last_normal * 0.8, last_normal * 0.65, last_normal * 0.45])


def test_race_week_training_excludes_the_race():
    plan, _ = make_plan(km=21.0975, weeks=10)
    race_week = plan.weeks[-1]
    assert race_week.total_km == pytest.approx(race_week.training_km + 21.0975)
