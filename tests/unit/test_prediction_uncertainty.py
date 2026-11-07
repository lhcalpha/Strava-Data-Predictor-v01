"""002 FR-006: uncertainty of today's estimate."""

import math
import statistics

import pytest

from strava_predictor.domain.models import RunnerInputs
from strava_predictor.domain.prediction import predict
from tests.unit.domain_helpers import act, summary


def _sigma_today(runs, race_km=10.0):
    return predict(runs, summary(), RunnerInputs(race_km, 10, 290, 4, 201)).sigma_today


def test_same_distance_single_run_is_the_base():
    assert _sigma_today([act(3, 10.0, 50.0, avg=170)]) == pytest.approx(0.02)


def test_one_doubling_adds_one_percent():
    assert _sigma_today([act(3, 5.0, 25.0, avg=170)]) == pytest.approx(0.03)


def test_shorter_race_counts_the_same_as_longer():
    assert _sigma_today([act(3, 10.0, 50.0, avg=170)], race_km=5.0) == pytest.approx(0.03)


def test_marathon_from_5_km():
    expected = 0.02 + 0.01 * math.log2(42.195 / 5.0)
    assert _sigma_today([act(3, 5.0, 25.0, avg=170)], race_km=42.195) == pytest.approx(expected)


def test_spread_between_basis_runs_adds_in_quadrature():
    runs = [act(3, 10.0, 50.0, avg=170), act(10, 10.0, 51.5, avg=170)]
    spread = statistics.stdev([math.log(3000.0), math.log(3090.0)])
    assert _sigma_today(runs) == pytest.approx(math.hypot(0.02, spread))


def test_mixed_distances_average_the_doublings():
    runs = [act(3, 10.0, 50.0, avg=170), act(10, 5.0, 23.0, avg=170)]
    times = [3000.0, 23 * 60 * 2**1.06]
    formula = 0.02 + 0.01 * (0 + 1) / 2
    spread = statistics.stdev([math.log(t) for t in times])
    assert _sigma_today(runs) == pytest.approx(math.hypot(formula, spread))
