# Data Model Changes: Adaptive Race-Day Pace Projection

**Feature**: [spec.md](./spec.md). Only changes from
[001 data-model.md](../001-race-pace-training-plan/data-model.md) are listed.

## Prediction

| Field | Change | Type | Notes |
|-------|--------|------|-------|
| caps_applied | removed | | Caps no longer exist (FR-009) |
| typical_rate | added | float | 0.3% × rate multiplier (FR-001) |
| trend_rate | added | float or None | Limited weekly trend; None when not used (FR-002, FR-003) |
| trend_runs | added | int | Hard runs of 3 km+ considered for the trend |
| trend_weight | added | float | n / (n + 8), 0 when no trend (FR-004) |
| no_trend_reason | added | NoTrendReason or None | `FALLBACK`, `TOO_FEW_RUNS`, `TOO_SHORT_SPAN` |
| weekly_rate | added | float | Blended rate, at least 0 (FR-004) |
| max_improvement | added | float | 8% × rate multiplier (FR-005) |
| improvement | added | float | Likely improvement G (FR-005) |
| sigma_today | added | float | FR-006 |
| sigma_improvement | added | float | FR-007 |
| sigma | added | float | Total log standard deviation (FR-008) |

## GoalRating

| Field | Change | Type | Notes |
|-------|--------|------|-------|
| goal_chance | added | float 0–1 | FR-010 |

## Rule settings

See [research.md P5](./research.md#p5-settings).
