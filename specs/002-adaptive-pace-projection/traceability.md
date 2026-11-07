# Traceability: Requirements to Tests

**Feature**: [spec.md](./spec.md). Paths are relative to `tests/`; `u/` = `unit/`,
`i/` = `integration/`.

## Functional requirements

| Req | Tests |
|-----|-------|
| FR-001 | u/test_prediction_projection.py::test_multiplier_scales_rate_limit_and_rate_uncertainty, ::test_scenario_1_ten_weeks_from_fifty_minutes |
| FR-002 | u/test_prediction_trend.py::test_scenario_4_trend_weight_and_rate, ::test_trend_is_limited, ::test_one_bad_run_does_not_move_the_trend, ::test_runs_on_the_same_date_are_skipped_in_pairs, ::test_only_hard_runs_of_3_km_or_more_count, ::test_trend_uses_every_hard_run_not_just_the_basis |
| FR-003 | u/test_prediction_trend.py::test_too_few_runs, ::test_runs_must_span_28_days, ::test_exactly_28_days_is_enough, ::test_no_trend_with_the_fallback; i/test_results_us1.py::test_trend_note_when_no_hard_runs |
| FR-004 | u/test_prediction_trend.py::test_scenario_4_trend_weight_and_rate, ::test_more_runs_give_the_trend_more_weight; u/test_prediction_projection.py::test_slowing_trend_floors_the_rate_at_zero; u/test_analysis_us1.py::test_typical_runner_matches_hand_calculation |
| FR-005 | u/test_prediction_projection.py::test_likely_follows_the_curve, ::test_improvement_levels_off_below_the_limit, ::test_short_plans_start_at_the_weekly_rate |
| FR-006 | u/test_prediction_uncertainty.py (all) |
| FR-007 | u/test_prediction_projection.py::test_multiplier_scales_rate_limit_and_rate_uncertainty, ::test_slowing_trend_floors_the_rate_at_zero |
| FR-008 | u/test_prediction_projection.py::test_safe_and_stretch_are_the_80_and_20_percentiles, ::test_order_and_chances_hold_for_every_distance_and_week |
| FR-009 | u/test_prediction_distance.py::test_two_full_steps_short_slow_paces_by_two_percent, ::test_slowdown_is_applied_after_the_projection; u/test_config.py::test_fixed_rates_and_caps_are_gone |
| FR-010 | u/test_rating.py::test_scenario_2_rating_and_chance, ::test_scenario_3_chance_at_each_projection, ::test_chance_uses_the_slowed_likely_time |
| FR-011 | i/test_results_us1.py::test_results_show_chances_and_method |
| FR-012 | u/test_config.py::test_rule_value; u/test_architecture.py::test_domain_has_no_bare_numbers; u/test_analysis_us1.py::test_same_inputs_give_same_result |

## Acceptance scenarios

| Scenario | Tests |
|----------|-------|
| US1-1 48:45 / 49:41 / 47:50 | u/test_prediction_projection.py::test_scenario_1_ten_weeks_from_fifty_minutes |
| US1-2 35% / 12% / 3% | u/test_rating.py::test_scenario_2_rating_and_chance |
| US1-3 80% / 50% / 20% | u/test_rating.py::test_scenario_3_chance_at_each_projection |
| US1-4 trend 0.5%, weight 5/13 | u/test_prediction_trend.py::test_scenario_4_trend_weight_and_rate |
| US1-5 no trend, with reason | u/test_prediction_trend.py::test_too_few_runs, ::test_runs_must_span_28_days |
| US1-6 slowing trend → rate 0 | u/test_prediction_projection.py::test_slowing_trend_floors_the_rate_at_zero |
| US1-7 52 weeks levels off | u/test_prediction_projection.py::test_improvement_levels_off_below_the_limit |

## Success criteria

| SC | Tests |
|----|-------|
| SC-001 | FR-001 to FR-010 rows above |
| SC-002 | u/test_prediction_projection.py::test_order_and_chances_hold_for_every_distance_and_week; u/test_plan_grid.py (all) |
| SC-003 | u/test_rating.py::test_rating_boundaries |
| SC-004 | `scripts/check.py` |
