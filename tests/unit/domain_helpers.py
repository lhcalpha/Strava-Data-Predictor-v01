"""Small builders for domain value objects used across unit tests."""

from datetime import date, timedelta

from strava_predictor.domain.models import (
    Activity,
    DataSummary,
    NoTrendReason,
    Prediction,
    ProjectedResult,
)

REFERENCE = date(2026, 11, 5)


def act(days_ago, km, minutes, avg=None, type="Run", name="Morning Run"):  # noqa: A002
    return Activity(
        date=REFERENCE - timedelta(days=days_ago),
        name=name,
        activity_type=type,
        description="",
        distance_km=km,
        moving_time_s=None if minutes is None else minutes * 60,
        avg_hr=avg,
        is_interval=any(word in name.lower() for word in ("interval", "repeat")),
    )


def summary(
    weeks=12,
    avg12=30.0,
    avg4=30.0,
    longest=20.0,
    runs_used=20,
    runs_with_hr=20,
    hard=5,
):
    return DataSummary(
        runs_used=runs_used,
        excluded={},
        runs_with_hr=runs_with_hr,
        hard_runs_used=hard,
        date_range=(REFERENCE - timedelta(days=80), REFERENCE),
        weeks_with_runs=weeks,
        avg_weekly_km_12=avg12,
        avg_weekly_km_4=avg4,
        longest_run_km=longest,
    )


def prediction(
    safe=294.0,
    likely=291.0,
    stretch=285.0,
    today=300.0,
    km=10.0,
    hard_runs_used=5,
    used_fallback=False,
    ten_k=300.0,
    sigma=0.02,
):
    def result(pace):
        return ProjectedResult(time_s=pace * km, pace_s_per_km=pace)

    return Prediction(
        race_distance_km=km,
        today_time_s=today * km,
        basis_runs=(),
        hard_runs_used=hard_runs_used,
        used_fallback=used_fallback,
        interval_only=False,
        rate_multiplier=1.0,
        typical_rate=0.003,
        trend_rate=None,
        trend_runs=0,
        trend_weight=0.0,
        no_trend_reason=NoTrendReason.TOO_FEW_RUNS,
        weekly_rate=0.003,
        max_improvement=0.08,
        improvement=0.03,
        sigma_today=0.02,
        sigma_improvement=0.01,
        sigma=sigma,
        long_run_target_km=12.0,
        reachable_long_run_km=20.0,
        distance_slowdown_pct=0,
        safe=result(safe),
        likely=result(likely),
        stretch=result(stretch),
        today_10k_pace_s_per_km=ten_k,
    )
