---

description: "Task list for Adaptive Race-Day Pace Projection"
---

# Tasks: Adaptive Race-Day Pace Projection

**Input**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md),
[data-model.md](./data-model.md)

**Tests**: Required (Constitution I). Each test task comes before the code it covers and is run and
seen to fail first. A task is complete only when `.venv\Scripts\python scripts\check.py` passes.
Synthetic data only; never read `New Data/`.

## Phase 1: Tests first [US1]

- [X] T001 [US1] Update expected settings (add P5 values, remove 001 rates and caps) in tests/unit/test_config.py
- [X] T002 [P] [US1] Rewrite projection tests for FR-001, FR-005, FR-007, FR-008, FR-009 (scenarios 1, 6, 7; multipliers) in tests/unit/test_prediction_projection.py
- [X] T003 [P] [US1] Add trend tests for FR-002 to FR-004 (scenario 4, too few runs, short span, fallback, same-date pairs, limits, outlier robustness) in tests/unit/test_prediction_trend.py
- [X] T004 [P] [US1] Add uncertainty tests for FR-006 (formula term per doubling, spread of basis runs) in tests/unit/test_prediction_uncertainty.py
- [X] T005 [US1] Update slowdown tests to the new likely time in tests/unit/test_prediction_distance.py and the Prediction builder in tests/unit/domain_helpers.py
- [X] T006 [P] [US1] Add goal-chance tests for FR-010 (scenarios 2 and 3) in tests/unit/test_rating.py
- [X] T007 [P] [US1] Add grid invariant (safe ≥ likely ≥ stretch; 80/50/20 chances) over 6 distances × 52 weeks × 3 runners in tests/unit/test_prediction_projection.py
- [X] T008 [P] [US1] Add results-page tests for FR-011 (chance column, method text, trend note) in tests/integration/test_results_us1.py

## Phase 2: Implementation [US1]

- [X] T009 [US1] Add P5 settings and remove the old rates and caps in src/strava_predictor/config.py
- [X] T010 [US1] Update Prediction and GoalRating, add NoTrendReason in src/strava_predictor/domain/models.py
- [X] T011 [US1] Implement trend, curve, and uncertainty in src/strava_predictor/domain/prediction.py
- [X] T012 [US1] Implement goal chance in src/strava_predictor/domain/rating.py
- [X] T013 [US1] Replace cap note with trend and curve notes, add rate formatting in src/strava_predictor/web/formatting.py
- [X] T014 [US1] Add chance column and method text in src/strava_predictor/web/templates/results.html

## Phase 3: Polish

- [X] T015 Mark 001 FR-022/FR-023 as superseded in specs/001-race-pace-training-plan/spec.md and update traceability in specs/002-adaptive-pace-projection/traceability.md
- [X] T016 Run all quality gates and the end-to-end journeys; update README.md's description of the prediction
