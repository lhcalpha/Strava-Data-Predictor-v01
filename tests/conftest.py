from datetime import date
from pathlib import Path

import pytest

from strava_predictor.domain.models import RunnerInputs

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def reference_date() -> date:
    return date(2026, 11, 5)


@pytest.fixture
def default_inputs() -> RunnerInputs:
    return RunnerInputs(
        race_distance_km=10.0,
        weeks_to_race=12,
        goal_pace_s_per_km=290,
        days_per_week=4,
        max_hr=201,
    )


@pytest.fixture
def load_fixture():
    def load(name: str) -> str:
        return (FIXTURES / name).read_text(encoding="utf-8")

    return load
