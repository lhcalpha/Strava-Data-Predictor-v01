# Contract: Domain API

Public functions of `strava_predictor.domain`. They do not import FastAPI or Jinja2, take the
reference date explicitly, and return the value objects in [data-model.md](../data-model.md).
Same inputs always give the same outputs.

```text
parse_activities(csv_text: str) -> list[Activity]
    Raises DataError(EMPTY_FILE | MALFORMED_CSV | MISSING_COLUMNS).

select_window(activities, reference_date) -> (list[Activity] usable, DataSummary)
    Applies type, window, and usability rules. Raises DataError(TOO_FEW_RUNS).

classify_effort(avg_hr: int | None, max_hr: int) -> EffortClass

predict(runs, summary, inputs: RunnerInputs) -> Prediction
    Raises DataError(NO_RUN_OVER_3KM).

rate_goal(goal_pace_s_per_km, prediction, summary) -> GoalRating

build_plan(prediction, rating, summary, inputs) -> TrainingPlan

analyse(csv_text_or_runs, inputs, reference_date) -> AnalysisResult
    Convenience wrapper used by the web layer: summary, prediction, rating, plan.
```

`check_plan_rules(plan, inputs) -> list[str]` returns every broken plan rule (empty when valid).
The plan tests use it across the whole parametrized grid.
