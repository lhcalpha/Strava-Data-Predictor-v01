---

description: "Task list for Flexible Average Heart Rate Reading"
---

# Tasks: Flexible Average Heart Rate Reading

**Input**: [spec.md](./spec.md). Tests first (Constitution I); synthetic descriptions only; a task is
complete only when `.venv\Scripts\python scripts\check.py` passes.

- [X] T001 [US1] Add failing cases for every scenario (dash, "HR", colon, "bpm", link before "Avg", "5x1km" before "Avg", ranks, reps, "Max", "Average", pace) in tests/unit/test_parsing_hr.py
- [X] T002 [US1] Expect the new pattern in tests/unit/test_config.py
- [X] T003 [US1] Change `AVG_HR_PATTERN` in src/strava_predictor/config.py
- [X] T004 Amend 001 FR-012 in specs/001-race-pace-training-plan/spec.md and R5 in specs/001-race-pace-training-plan/research.md
- [X] T005 Run all quality gates

## Traceability

| Req / scenario | Tests |
|----------------|-------|
| FR-001, scenarios 1–4, 6 | u/test_parsing_hr.py::test_parse_avg_hr (dash, "HR", link, "5x1km", 001 forms); u/test_config.py::test_rule_value[AVG_HR_PATTERN] |
| FR-002 | u/test_parsing_hr.py::test_parse_avg_hr ("Avg HR - 29", "Avg - 251", "Avg - 1650", "Avg 29", "Avg 251") |
| FR-003, scenario 5 | u/test_parsing_hr.py::test_parse_avg_hr ("Overall Rank: 125", "19x400m Reps", "Max : 199", "Average pace", "Avg pace 4:50", "Avg - 15:30 pace") |
