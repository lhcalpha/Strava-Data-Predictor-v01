import pytest

from strava_predictor.domain.models import Projection, RunnerInputs
from strava_predictor.domain.prediction import predict
from tests.unit.domain_helpers import act, summary

TODAY_RUN = [act(3, 10.0, 50.0, avg=170)]  # 3000 s for 10 km


def _predict(race_weeks=10, **summary_args):
    inputs = RunnerInputs(10.0, race_weeks, 290, 4, 201)
    return predict(TODAY_RUN, summary(**summary_args), inputs)


def test_normal_projection():
    result = _predict()
    assert result.today_time_s == pytest.approx(3000.0)
    assert result.safe.time_s == pytest.approx(2940.0)
    assert result.likely.time_s == pytest.approx(2910.0)
    assert result.stretch.time_s == pytest.approx(2850.0)
    assert result.safe.pace_s_per_km == pytest.approx(294.0)
    assert result.likely.pace_s_per_km == pytest.approx(291.0)
    assert result.stretch.pace_s_per_km == pytest.approx(285.0)
    assert result.rate_multiplier == 1.0
    assert result.caps_applied == frozenset()


@pytest.mark.parametrize(
    ("summary_args", "multiplier"),
    [
        ({"weeks": 7}, 1.25),
        ({"weeks": 8}, 1.0),
        ({"avg12": 14.9}, 1.25),
        ({"avg12": 15.0}, 1.0),
        ({"avg12": 60.0}, 1.0),
        ({"avg12": 60.1}, 0.75),
        ({"weeks": 7, "avg12": 61.0}, 0.9375),
    ],
)
def test_rate_multipliers(summary_args, multiplier):
    result = _predict(**summary_args)
    assert result.rate_multiplier == pytest.approx(multiplier)
    assert result.stretch.time_s == pytest.approx(3000.0 * (1 - 0.005 * multiplier * 10))


def test_caps_after_multipliers_on_long_plans():
    result = _predict(race_weeks=52)
    assert result.safe.time_s == pytest.approx(3000.0 * 0.96)
    assert result.likely.time_s == pytest.approx(3000.0 * 0.94)
    assert result.stretch.time_s == pytest.approx(3000.0 * 0.90)
    assert result.caps_applied == frozenset(Projection)


def test_cap_reached_exactly_is_not_reported():
    result = _predict(race_weeks=20)
    assert result.stretch.time_s == pytest.approx(2700.0)
    assert Projection.STRETCH not in result.caps_applied


def test_multiplier_can_trigger_cap():
    capped = predict(TODAY_RUN, summary(weeks=6), RunnerInputs(10.0, 17, 290, 4, 201))
    assert capped.caps_applied == frozenset(Projection)
    uncapped = predict(TODAY_RUN, summary(), RunnerInputs(10.0, 17, 290, 4, 201))
    assert uncapped.caps_applied == frozenset()
