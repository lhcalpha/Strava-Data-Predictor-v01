# Data Model: Race Pace Prediction and 80/20 Training Plan

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

All entities are immutable value objects (frozen dataclasses) in `strava_predictor.domain`. None are
stored on disk. Times are seconds, distances km, paces seconds per km, unless stated.

## Activity

One CSV row after parsing. Built by `parse_activities`.

| Field | Type | Rules |
|-------|------|-------|
| date | date | Date part of `Activity Date` (UTC) |
| name | str | Raw text; always escaped when shown |
| activity_type | str | Raw `Activity Type` |
| description | str | Raw text; never logged |
| distance_km | float or None | Metre column ÷ 1000, else first Distance converted; None if unusable |
| moving_time_s | float or None | `Moving Time`; None if blank, zero, or not a number |
| avg_hr | int or None | Per R5; None if missing or outside 30–250 |
| is_interval | bool | Name contains "interval" or "repeat", any case |
| exclusion | ExclusionReason or None | `NOT_A_RUN`, `OUTSIDE_WINDOW`, `NO_DISTANCE`, `NO_MOVING_TIME`, `IMPLAUSIBLE_PACE` |

Derived: `pace_s_per_km = moving_time_s / distance_km` for usable runs.

## EffortClass

Enum: `EASY`, `MODERATE`, `HARD`, `UNKNOWN` (no usable heart rate).
`easy_max = round_half_up(0.75 × max_hr)`, `hard_min = round_half_up(0.82 × max_hr)`.

## RunnerInputs

| Field | Type | Validation (web layer) |
|-------|------|------------------------|
| race_distance_km | float | > 0 and ≤ 100; warning < 3 or > 42.195 |
| weeks_to_race | int | 1–52; warning < 4 |
| goal_pace_s_per_km | int | m:ss, seconds 00–59, 2:00–15:00 |
| days_per_week | int | 2–7 |
| max_hr | int | 100–240, default 201 |

## DataSummary

| Field | Type |
|-------|------|
| runs_used | int |
| excluded | mapping ExclusionReason → int |
| runs_with_hr | int |
| hard_runs_used | int |
| date_range | (date, date) or None |
| weeks_with_runs | int (of 12) |
| avg_weekly_km_12 | float |
| avg_weekly_km_4 | float |
| longest_run_km | float |
| warnings | list of Warning (code + message) |

Errors that stop analysis (raised as `DataError` with a code): `MISSING_COLUMNS` (lists them),
`EMPTY_FILE`, `MALFORMED_CSV`, `TOO_FEW_RUNS`, `NO_RUN_OVER_3KM`.

## Prediction

| Field | Type | Notes |
|-------|------|-------|
| today_time_s | float | Mean of up to 3 fastest Riegel predictions |
| basis_runs | list of Activity | Runs behind the estimate |
| used_fallback | bool | No hard runs ≥ 3 km |
| interval_only | bool | Every basis run is an interval run |
| rate_multiplier | float | 1.0, 1.25, 0.75, or 0.9375 when both apply |
| caps_applied | set of Projection | Which projections hit the 4/6/10% cap |
| long_run_target_km | float | Interpolated, 8–35 |
| reachable_long_run_km | float | Longest run × 1.1^pre-taper weeks |
| distance_slowdown_pct | int | Full 10% shortfalls × 1 |
| safe / likely / stretch | ProjectedResult | time_s and pace_s_per_km each |
| today_10k_pace_s_per_km | float | Riegel to 10 km; base for easy pace |

## GoalRating

| Field | Type |
|-------|------|
| rating | `CONSERVATIVE`, `REALISTIC`, `AMBITIOUS`, `VERY_AMBITIOUS`, `UNLIKELY` |
| confidence | `NORMAL` or `LOW` |
| confidence_reasons | list of str |

## TrainingPlan

| Field | Type | Notes |
|-------|------|-------|
| target_pace_s_per_km | float | Goal clamped to [stretch, today] (R15) |
| targets_stretch | bool | Rating is Very ambitious or Unlikely |
| easy_pace_range | (float, float) | 1.18× and 1.27× today's 10 km pace |
| weeks | list of PlanWeek | One per week to race |
| total_hard_share | float | Race included |
| notes | list of str | e.g. total above 20% because of the race |

## PlanWeek

| Field | Type |
|-------|------|
| number | int (1-based) |
| phase | `BASE`, `BUILD`, `PEAK`, `TAPER` |
| is_lighter | bool |
| is_race_week | bool |
| training_km | float (excludes the race) |
| total_km | float |
| total_time_s | float |
| hard_time_s | float |
| hard_share / easy_share | float |
| sessions | list of Session (length = days_per_week) |

## Session

| Field | Type |
|-------|------|
| day | int 1–7 |
| kind | `EASY`, `LONG`, `HARD`, `RACE` |
| distance_km | float |
| target_pace | float or (float, float) for easy ranges |
| hard_km / hard_pace | float, for `HARD` only |
| warmup_km / cooldown_km | float, for `HARD` only |

Days are spread evenly across the week; the race is always the last session of the final week.

## Rule settings

Every value below lives in `src/strava_predictor/config.py` under this name. Spec values come from
the requirement shown; plan values come from [research.md](./research.md).

| Name | Value | Source |
|------|-------|--------|
| WINDOW_WEEKS | 12 | FR-009 |
| STALE_DATA_DAYS | 14 | FR-016 |
| MIN_USABLE_RUNS | 3 | FR-015 |
| HR_VALID_MIN / HR_VALID_MAX | 30 / 250 | FR-012 |
| EASY_HR_FRACTION / HARD_HR_FRACTION | 0.75 / 0.82 | FR-017 |
| INTERVAL_KEYWORDS | ("interval", "repeat") | FR-018 |
| RIEGEL_EXPONENT | 1.06 | FR-019 |
| MIN_PREDICTION_RUN_KM | 3.0 | FR-019 |
| TOP_PREDICTIONS | 3 | FR-019 |
| WEEKLY_RATE_SAFE / LIKELY / STRETCH | 0.002 / 0.003 / 0.005 | FR-022 |
| IMPROVEMENT_CAP_SAFE / LIKELY / STRETCH | 0.04 / 0.06 / 0.10 | FR-022 (clarified) |
| LOW_VOLUME_MULTIPLIER, MIN_ACTIVE_WEEKS, LOW_VOLUME_KM | 1.25, 8, 15 | FR-023 |
| HIGH_VOLUME_MULTIPLIER, HIGH_VOLUME_KM | 0.75, 60 | FR-023 |
| LONG_RUN_TARGETS | (5, 8), (10, 12), (21.0975, 18), (42.195, 30) | FR-024 |
| LONG_RUN_MIN_KM / LONG_RUN_MAX_KM | 8 / 35 | FR-024 |
| LONG_RUN_GROWTH | 0.10 | FR-025 |
| SHORTFALL_STEP / SLOWDOWN_PER_STEP | 0.10 / 0.01 | FR-025 |
| VERY_AMBITIOUS_MARGIN | 0.02 | FR-026 |
| MIN_HARD_RUNS_FOR_CONFIDENCE, MIN_HR_SHARE | 3, 0.5 | FR-027 |
| TAPER_WEEKS_BY_DISTANCE / TAPER_WEEKS_LONG_RACE | ≤10 km: 1, ≤21.1 km: 2, else 3 | FR-029 |
| TAPER_CUTS | 1: (0.40); 2: (0.25, 0.50); 3: (0.20, 0.35, 0.55) | FR-029 (clarified) |
| PHASE_SHARE_BASE / BUILD / PEAK | 0.4 / 0.4 / 0.2 | FR-030 |
| START_VOLUME_WEEKS | 4 | FR-031 |
| MAX_WEEKLY_INCREASE | 0.10 | FR-032 |
| LIGHTER_WEEK_EVERY | 4 | FR-032 |
| MAX_WEEKLY_HARD_SHARE | 0.20 | FR-035 |
| PLAN_HARD_SHARE_MIN / MAX | 0.15 / 0.20 | FR-035 |
| EASY_PACE_FACTOR_MIN / MAX | 1.18 / 1.27 | FR-036 |
| RUN_ACTIVITY_TYPES | Run, Trail Run, Virtual Run | R4 |
| PACE_PLAUSIBLE_MIN / MAX | 120 / 1200 s per km | R2 |
| SESSION_TTL_S / MAX_SESSIONS | 7200 / 10 | R7 |
| MAX_UPLOAD_BYTES | 10 MB | plan input |
| VOLUME_GROWTH_RATE | 0.08 | R14 |
| PEAK_VOLUME_MULTIPLIER | 1.5 | R14 |
| LIGHTER_WEEK_CUT | 0.225 | R14 |
| HARD_SHARE_BY_PHASE | base 0.15, build 0.18, peak 0.19, taper 0.15 | R16 |
| WARMUP_KM / COOLDOWN_KM | 2.0 / 1.5 | R15 |
| LONG_RUN_MAX_SHARE | 0.5 | R15 |
| FEW_DAYS_PER_WEEK, HARD_SESSIONS_FEW_DAYS, HARD_SESSIONS_BY_PHASE | 3, 1, base 1 / build 2 / peak 2 / taper 1 | R15 |
| HARD_SHARE_SEARCH_STEPS | 40 | R16 |

## State transitions

Only the session store has state: `absent → stored (on valid upload) → refreshed (each use) →
expired (2 h idle, eviction, or restart)`. An expired session returns the form with a re-upload
message.
