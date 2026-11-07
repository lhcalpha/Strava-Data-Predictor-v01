# Traceability: Requirements to Tests

**Feature**: [spec.md](./spec.md) | **Constitution I**: every functional requirement and acceptance
scenario maps to at least one automated test.

Paths are relative to `tests/`. `u/` = `unit/`, `i/` = `integration/`, `e/` = `e2e/`.

## Functional requirements

| Req | Tests |
|-----|-------|
| FR-001 | i/test_validation.py::test_missing_file_on_first_submit; i/test_app_shell.py::test_form_page_has_every_field |
| FR-002 | i/test_validation.py (race_distance_km cases); i/test_results_us1.py::test_input_warnings_do_not_block_results |
| FR-003 | i/test_validation.py (weeks_to_race cases); i/test_results_us1.py::test_input_warnings_do_not_block_results |
| FR-004 | u/test_numbers.py::test_parse_pace_valid, ::test_parse_pace_invalid; i/test_validation.py (goal_pace cases) |
| FR-005 | i/test_validation.py (days_per_week cases) |
| FR-006 | i/test_app_shell.py::test_form_page_has_every_field; i/test_validation.py (max_hr cases) |
| FR-007 | i/test_validation.py::test_invalid_field_shows_message_and_keeps_other_values, ::test_several_errors_at_once; e/test_journey_errors.py::test_field_error_is_shown_beside_the_field |
| FR-008 | i/test_regenerate.py (all); u/test_sessions.py (all); e/test_journey_scenario.py::test_try_another_scenario |
| FR-009 | u/test_window.py::test_window_is_84_days_including_reference_date, ::test_only_running_types_are_used; u/test_analysis_us1.py::test_reference_date_moves_the_window |
| FR-010 | u/test_parsing_columns.py::test_real_layout_reads_metre_column, ::test_missing_required_column_names_it; i/test_results_us1.py::test_data_errors_block_results |
| FR-011 | u/test_parsing_columns.py::test_real_layout_reads_metre_column, ::test_first_distance_used_when_metres_blank, ::test_miles_detected_from_ratio_and_converted, ::test_imperial_fixture_matches_metres, ::test_single_distance_column_is_km |
| FR-012 | u/test_parsing_hr.py (all) |
| FR-013 | u/test_window.py::test_runs_without_heart_rate_count_for_volume; u/test_effort.py::test_classify_at_201 (None → UNKNOWN) |
| FR-014 | u/test_window.py::test_unusable_distance_time_and_pace_are_excluded; i/test_data_summary.py::test_mixed_quality_counts |
| FR-015 | u/test_window.py::test_too_few_runs; i/test_results_us1.py::test_data_errors_block_results |
| FR-016 | u/test_window.py::test_stale_data_warning; i/test_data_summary.py::test_stale_data_warning |
| FR-017 | u/test_effort.py (all); u/test_numbers.py::test_round_half_up |
| FR-018 | u/test_parsing_columns.py::test_interval_flag; u/test_prediction_today.py::test_interval_only_basis |
| FR-019 | u/test_prediction_today.py::test_riegel_known_value, ::test_single_hard_run, ::test_three_fastest_of_five_hard_runs, ::test_two_hard_runs_are_both_averaged, ::test_hard_runs_under_3km_are_ignored |
| FR-020 | u/test_prediction_today.py::test_fallback_uses_three_fastest_runs_over_3km, ::test_no_run_of_3km_is_an_error; u/test_rating.py::test_low_confidence_with_fallback |
| FR-021 | u/test_prediction_today.py::test_interval_only_basis, ::test_mixed_basis_is_not_interval_only; i/test_results_us1.py::test_interval_only_note |
| FR-022 | Superseded by 002 FR-001 to FR-009; see [002 traceability](../002-adaptive-pace-projection/traceability.md) |
| FR-023 | Superseded by 002 FR-001; u/test_prediction_projection.py::test_multiplier_scales_rate_limit_and_rate_uncertainty |
| FR-024 | u/test_prediction_distance.py::test_long_run_target |
| FR-025 | u/test_prediction_distance.py::test_reachable_long_run_grows_over_pre_taper_weeks, ::test_two_full_steps_short_slow_paces_by_two_percent, ::test_full_steps_only, ::test_slowdown_is_applied_after_the_projection; u/test_taper.py::test_taper_weeks |
| FR-026 | u/test_rating.py::test_rating_boundaries |
| FR-027 | u/test_rating.py (confidence tests); i/test_results_us1.py::test_low_confidence_reason_shown; i/test_data_summary.py::test_mixed_quality_confidence |
| FR-028 | u/test_plan_paces.py::test_target_pace_is_clamped, ::test_target_never_faster_than_stretch_even_when_stretch_is_slower_than_today, ::test_targets_stretch_note; i/test_results_plan.py::test_stretch_target_note_for_unlikely_goal |
| FR-029 | u/test_taper.py::test_taper_weeks; u/test_plan_volume.py::test_taper_cuts_from_last_peak_week, ::test_marathon_taper_in_a_full_plan; u/test_plan_rules.py::test_wrong_taper_cut |
| FR-030 | u/test_plan_structure.py::test_phase_layout, ::test_base_never_longer_than_build |
| FR-031 | u/test_plan_volume.py::test_start_is_last_four_week_average, ::test_zero_recent_volume_falls_back_with_a_note; u/test_plan_rules.py::test_first_week_not_starting_distance |
| FR-032 | u/test_plan_volume.py::test_volumes_grow_lighten_and_taper, ::test_week_after_lighter_week_compares_with_last_normal_week, ::test_race_week_training_excludes_the_race; u/test_plan_rules.py::test_volume_rise_over_ten_percent, ::test_lighter_week_not_light_enough, ::test_missing_lighter_week |
| FR-033 | u/test_plan_sessions.py::test_session_counts_and_kinds, ::test_two_days_is_long_run_and_hard_session; u/test_plan_structure.py::test_one_week_plan_is_a_single_race_week; u/test_plan_rules.py::test_wrong_session_count, ::test_two_long_runs, ::test_race_not_last |
| FR-034 | u/test_plan_sessions.py::test_hard_session_parts, ::test_short_weeks_shrink_warm_ups_proportionally; u/test_plan_paces.py::test_hard_km_formula |
| FR-035 | u/test_plan_paces.py::test_weekly_hard_share_matches_phase; u/test_plan_grid.py (all); u/test_plan_rules.py::test_weekly_hard_share_over_twenty_percent, ::test_plan_total_too_low; i/test_results_plan.py::test_hard_total_note_for_one_week_marathon |
| FR-036 | u/test_plan_paces.py::test_easy_pace_range_from_ten_k_and_not_the_goal; u/test_prediction_today.py::test_ten_k_pace_uses_same_method; u/test_plan_rules.py::test_easy_pace_from_goal |
| FR-037 | u/test_plan_paces.py::test_hard_pace_moves_linearly_then_holds, ::test_hard_pace_never_faster_than_stretch; u/test_plan_rules.py::test_hard_pace_faster_than_stretch |
| FR-038 | i/test_results_us1.py::test_results_show_every_summary_value; e/test_journey_check_goal.py::test_check_a_race_goal |
| FR-039 | i/test_data_summary.py (all); e/test_journey_data.py::test_understand_the_data |
| FR-040 | i/test_results_plan.py::test_plan_tables; e/test_journey_plan.py::test_get_a_training_plan |
| FR-041 | i/test_results_us1.py::test_results_show_every_summary_value |
| FR-042 | i/test_privacy_security.py (all); i/test_app_shell.py::test_every_response_has_strict_csp, ::test_no_external_urls; u/test_main.py (all); u/test_sessions.py::test_stores_activities_not_text |
| FR-043 | u/test_config.py (all); u/test_architecture.py::test_domain_has_no_bare_numbers; u/test_analysis_us1.py::test_same_inputs_give_same_result |

## Success criteria

| SC | Tests |
|----|-------|
| SC-001 | e/test_journey_check_goal.py::test_check_a_race_goal (under 120 s); quickstart scenario 1 timed |
| SC-002 | i/test_performance.py (both) |
| SC-003 | u/test_plan_grid.py::test_every_plan_obeys_the_rules (6 distances × 52 weeks × 6 day counts × 3 runners) |
| SC-004 | u/test_rating.py::test_rating_boundaries; u/test_effort.py (all) |
| SC-005 | e/ (all four journeys plus the error journey); this table |
| SC-006 | i/test_data_summary.py::test_mixed_quality_counts; u/test_window.py::test_unusable_distance_time_and_pace_are_excluded |

## Acceptance scenarios

| Scenario | Tests |
|----------|-------|
| US1-1 summary shown | i/test_results_us1.py::test_results_show_every_summary_value; e/test_journey_check_goal.py |
| US1-2 52:07 from 5 km in 25:00 | u/test_prediction_today.py::test_riegel_known_value, ::test_single_hard_run |
| US1-3 49:00 / 48:30 / 47:30 | Superseded by 002 US1-1 |
| US1-4 Ambitious / Very ambitious / Unlikely | u/test_rating.py::test_rating_boundaries (290, 280, 279) |
| US1-5 no hard runs → low confidence | u/test_prediction_today.py::test_fallback_uses_three_fastest_runs_over_3km; i/test_results_us1.py::test_low_confidence_reason_shown |
| US1-6 interval-only message | i/test_results_us1.py::test_interval_only_note |
| US1-7 missing columns / too few runs | i/test_results_us1.py::test_data_errors_block_results; e/test_journey_errors.py::test_error_then_recover |
| US1-8 field error, values kept | i/test_validation.py::test_invalid_field_shows_message_and_keeps_other_values |
| US2-1 one table per week, race last | i/test_results_plan.py::test_plan_tables; e/test_journey_plan.py |
| US2-2 sessions and one long run | u/test_plan_sessions.py::test_session_counts_and_kinds |
| US2-3 hard share limits | u/test_plan_grid.py; u/test_plan_paces.py::test_weekly_hard_share_matches_phase |
| US2-4 10% rise and lighter weeks | u/test_plan_volume.py::test_volumes_grow_lighten_and_taper; u/test_plan_grid.py |
| US2-5 40 / 32.5 / 22.5 km taper | u/test_plan_volume.py::test_taper_cuts_from_last_peak_week |
| US2-6 stretch-pace note | u/test_plan_paces.py::test_targets_stretch_note; i/test_results_plan.py::test_stretch_target_note_for_unlikely_goal |
| US2-7 easy pace from 10 km pace | u/test_plan_paces.py::test_easy_pace_range_from_ten_k_and_not_the_goal |
| US3-1 regenerate without upload | i/test_regenerate.py::test_regenerate_without_upload; e/test_journey_scenario.py |
| US3-2 invalid value keeps data | i/test_regenerate.py::test_invalid_field_keeps_the_session |
| US4-1 data summary counts | i/test_data_summary.py::test_mixed_quality_counts; e/test_journey_data.py |
| US4-2 stale data warning | i/test_data_summary.py::test_stale_data_warning |
| US4-3 low confidence with reason | i/test_data_summary.py::test_mixed_quality_confidence |
