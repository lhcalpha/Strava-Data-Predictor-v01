"""Every rule value from data-model.md's Rule settings table exists with its exact value."""

import pytest

from strava_predictor import config

EXPECTED = {
    "WINDOW_WEEKS": 12,
    "STALE_DATA_DAYS": 14,
    "MIN_USABLE_RUNS": 3,
    "HR_VALID_MIN": 30,
    "HR_VALID_MAX": 250,
    "EASY_HR_FRACTION": 0.75,
    "HARD_HR_FRACTION": 0.82,
    "INTERVAL_KEYWORDS": ("interval", "repeat"),
    "RIEGEL_EXPONENT": 1.06,
    "MIN_PREDICTION_RUN_KM": 3.0,
    "TOP_PREDICTIONS": 3,
    "WEEKLY_RATE_SAFE": 0.002,
    "WEEKLY_RATE_LIKELY": 0.003,
    "WEEKLY_RATE_STRETCH": 0.005,
    "IMPROVEMENT_CAP_SAFE": 0.04,
    "IMPROVEMENT_CAP_LIKELY": 0.06,
    "IMPROVEMENT_CAP_STRETCH": 0.10,
    "LOW_VOLUME_MULTIPLIER": 1.25,
    "MIN_ACTIVE_WEEKS": 8,
    "LOW_VOLUME_KM": 15.0,
    "HIGH_VOLUME_MULTIPLIER": 0.75,
    "HIGH_VOLUME_KM": 60.0,
    "LONG_RUN_TARGETS": ((5.0, 8.0), (10.0, 12.0), (21.0975, 18.0), (42.195, 30.0)),
    "LONG_RUN_MIN_KM": 8.0,
    "LONG_RUN_MAX_KM": 35.0,
    "LONG_RUN_GROWTH": 0.10,
    "SHORTFALL_STEP": 0.10,
    "SLOWDOWN_PER_STEP": 0.01,
    "VERY_AMBITIOUS_MARGIN": 0.02,
    "MIN_HARD_RUNS_FOR_CONFIDENCE": 3,
    "MIN_HR_SHARE": 0.5,
    "TAPER_WEEKS_BY_DISTANCE": ((10.0, 1), (21.1, 2)),
    "TAPER_WEEKS_LONG_RACE": 3,
    "TAPER_CUTS": {1: (0.40,), 2: (0.25, 0.50), 3: (0.20, 0.35, 0.55)},
    "PHASE_SHARE_BASE": 0.4,
    "PHASE_SHARE_BUILD": 0.4,
    "PHASE_SHARE_PEAK": 0.2,
    "START_VOLUME_WEEKS": 4,
    "MAX_WEEKLY_INCREASE": 0.10,
    "LIGHTER_WEEK_EVERY": 4,
    "LIGHTER_WEEK_CUT_MIN": 0.20,
    "LIGHTER_WEEK_CUT_MAX": 0.25,
    "MAX_WEEKLY_HARD_SHARE": 0.20,
    "PLAN_HARD_SHARE_MIN": 0.15,
    "PLAN_HARD_SHARE_MAX": 0.20,
    "EASY_PACE_FACTOR_MIN": 1.18,
    "EASY_PACE_FACTOR_MAX": 1.27,
    "RUN_ACTIVITY_TYPES": frozenset({"Run", "Trail Run", "Virtual Run"}),
    "PACE_PLAUSIBLE_MIN": 120,
    "PACE_PLAUSIBLE_MAX": 1200,
    "SESSION_TTL_S": 7200,
    "MAX_SESSIONS": 10,
    "MAX_UPLOAD_BYTES": 10 * 1024 * 1024,
    "VOLUME_GROWTH_RATE": 0.08,
    "PEAK_VOLUME_MULTIPLIER": 1.5,
    "LIGHTER_WEEK_CUT": 0.225,
    "HARD_SHARE_BY_PHASE": {"BASE": 0.15, "BUILD": 0.18, "PEAK": 0.19, "TAPER": 0.15},
    "WARMUP_KM": 2.0,
    "COOLDOWN_KM": 1.5,
    "LONG_RUN_MAX_SHARE": 0.5,
    "METRES_PER_KM": 1000,
    "METRES_PER_MILE": 1609.344,
    "SECONDS_PER_MINUTE": 60,
    "DAYS_PER_WEEK": 7,
    "RACE_KM_MAX": 100.0,
    "RACE_KM_WARN_MIN": 3.0,
    "RACE_KM_WARN_MAX": 42.195,
    "WEEKS_MIN": 1,
    "WEEKS_MAX": 52,
    "WEEKS_WARN_MIN": 4,
    "GOAL_PACE_MIN_S": 120,
    "GOAL_PACE_MAX_S": 900,
    "DAYS_MIN": 2,
    "DAYS_MAX": 7,
    "MAX_HR_DEFAULT": 201,
    "MAX_HR_MIN": 100,
    "MAX_HR_MAX": 240,
    "HOST": "127.0.0.1",
    "PORT": 8000,
}


@pytest.mark.parametrize(("name", "value"), sorted(EXPECTED.items()))
def test_rule_value(name, value):
    assert getattr(config, name) == value


def test_lighter_week_cut_inside_spec_range():
    assert config.LIGHTER_WEEK_CUT_MIN <= config.LIGHTER_WEEK_CUT <= config.LIGHTER_WEEK_CUT_MAX


def test_hard_shares_inside_spec_limits():
    for share in config.HARD_SHARE_BY_PHASE.values():
        assert config.PLAN_HARD_SHARE_MIN <= share <= config.MAX_WEEKLY_HARD_SHARE


def test_growth_rate_below_weekly_limit():
    assert config.VOLUME_GROWTH_RATE <= config.MAX_WEEKLY_INCREASE


def test_phase_shares_add_up():
    total = config.PHASE_SHARE_BASE + config.PHASE_SHARE_BUILD + config.PHASE_SHARE_PEAK
    assert total == pytest.approx(1.0)
