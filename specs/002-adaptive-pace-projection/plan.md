# Implementation Plan: Adaptive Race-Day Pace Projection

**Branch**: `002-adaptive-pace-projection` | **Date**: 2026-11-07 | **Spec**: [spec.md](./spec.md)

## Summary

Replace the fixed-rate projection in `domain/prediction.py` with a saturating improvement curve, a
Theil–Sen personal trend blended with a typical rate, and log-normal percentiles for safe, likely,
and stretch. Add the goal's chance of success to `GoalRating` and show the chances and the method
on the results page. Everything else from feature 001 is reused unchanged.

## Technical Context

Same as [001 plan](../001-race-pace-training-plan/plan.md): Python 3.14, FastAPI, Jinja2, pytest,
Ruff. No new dependencies: `math` and `statistics` (`NormalDist`, `median`, `stdev`) from the
standard library cover the maths and are deterministic.

## Constitution Check

| Principle | How this feature complies |
|-----------|---------------------------|
| I. Testing | Tests for every formula are written first and seen to fail (tasks T002–T006). |
| II. Explainable numbers | Each value is a named setting in `config.py`; the page shows the trend, its weight, the rate, the limit, and the chances. Standard-library maths only; no randomness. |
| III. Honest uncertainty | Safe and stretch become explicit 80% and 20% chances, the goal gets a chance, and the page says when no trend could be measured. |
| IV. Athlete safety | The plan still never targets faster than stretch (001 FR-028). |
| V. Privacy | No change to data handling. |
| VI. Separation | Maths in `domain/`; wording in `web/formatting.py` and templates. |
| VII. Simplicity | One module changes; caps and three rate constants are removed. |

## Files touched

```text
src/strava_predictor/config.py            new projection settings; old rates and caps removed
src/strava_predictor/domain/models.py     Prediction and GoalRating fields
src/strava_predictor/domain/prediction.py trend, curve, uncertainty
src/strava_predictor/domain/rating.py     goal chance
src/strava_predictor/web/formatting.py    notes and rate formatting
src/strava_predictor/web/templates/results.html  chance column and method text
tests/unit/...                            projection, trend, uncertainty, rating, config
tests/integration/test_results_us1.py     chance column and method text
```

## Design notes

See [research.md](./research.md) for why each method and value was chosen.
