---

description: "Task list for Race Pace Prediction and 80/20 Training Plan"
---

# Tasks: Race Pace Prediction and 80/20 Training Plan

**Input**: Design documents from `specs/001-race-pace-training-plan/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: Required. Constitution I makes TDD non-negotiable: every test task comes before the code
it covers, and each test MUST be run and seen to fail before that code is written.

**Organization**: Tasks are grouped by user story so each story can be built and tested on its own.

**Plan rules**: The plan's rule values (R14–R16) are accepted and recorded in spec.md: FR-028
(target never slower than today's pace), FR-029/FR-032 (training distance excludes the race), and
the Assumptions section (growth, ceiling, hard shares, sessions). Each is a named value in
`config.py`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on unfinished tasks)
- **[Story]**: User story the task belongs to (US1–US4)
- Paths are relative to the repository root

## Quality gates (every task)

A task is complete only when `.venv\Scripts\python scripts\check.py` passes (from T006 onward).
Tests MUST NOT be skipped, weakened, or deleted to make it pass. Only synthetic data may be used in
tests and fixtures; never read or copy files from `New Data/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project skeleton, dependencies, tooling, and the gate runner

- [X] T001 Create the package and test folders from plan.md: `src/strava_predictor/__init__.py`, `src/strava_predictor/domain/__init__.py`, `src/strava_predictor/web/__init__.py`, `src/strava_predictor/web/templates/`, `src/strava_predictor/web/static/`, `tests/unit/`, `tests/integration/`, `tests/e2e/`, `tests/fixtures/`, `scripts/`
- [X] T002 Create `pyproject.toml` with project name `strava-predictor`, `requires-python = ">=3.14"`, src layout, runtime dependencies (fastapi, uvicorn, jinja2, python-multipart) and a `dev` extra (pytest, pytest-cov, httpx, pytest-playwright, ruff), each pinned to the newest release that installs on Python 3.14; install with `.venv\Scripts\python -m pip install -e ".[dev]"` and `.venv\Scripts\python -m playwright install chromium`
- [X] T003 [P] Add Ruff settings to `pyproject.toml` (`line-length = 100`, `target-version = "py314"`, rule sets E, F, I, B, UP, SIM) and run `ruff format` on the empty package
- [X] T004 [P] Add pytest settings to `pyproject.toml`: `testpaths = ["tests"]`, `pythonpath = ["src"]`, marker `e2e`, and `[tool.coverage.run] branch = true, source = ["strava_predictor"]`
- [X] T005 [P] Confirm `.gitignore` still ignores `New Data/`, `export_*.zip`, and `activities.csv`, and add `.coverage.*` and `test-results/`
- [X] T006 Create `scripts/check.py` that runs, in order, `ruff check .`, `ruff format --check .`, `pytest --cov=strava_predictor --cov-branch --cov-fail-under=90`, and `pytest tests/unit --cov=strava_predictor.domain --cov-branch --cov-fail-under=95` with the venv's interpreter, prints each command, and exits with the first non-zero code

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Settings, value objects, shared helpers, test data builders, and the app shell that every story needs

**⚠️ CRITICAL**: No user story work starts until this phase is complete

- [X] T007 Write `tests/unit/test_architecture.py`: importing every module under `strava_predictor.domain` MUST NOT import `fastapi`, `starlette`, or `jinja2` (check `sys.modules` in a subprocess); and no module under `src/strava_predictor/domain/` contains a numeric literal other than 0 and 1 outside `config.py` (scan with `ast`) — confirm it fails
- [X] T008 Write `tests/unit/test_config.py` asserting every value in the [Rule settings table](./data-model.md#rule-settings) exists in `strava_predictor.config` with exactly that value (e.g. `RIEGEL_EXPONENT == 1.06`, `IMPROVEMENT_CAP_STRETCH == 0.10`, `TAPER_CUTS[3] == (0.20, 0.35, 0.55)`, `LIGHTER_WEEK_CUT == 0.225`) and that `0.20 <= LIGHTER_WEEK_CUT <= 0.25` and every `HARD_SHARE_BY_PHASE` value is within `PLAN_HARD_SHARE_MIN` and `MAX_WEEKLY_HARD_SHARE` — confirm it fails
- [X] T009 Create `src/strava_predictor/config.py` with every rule value from the data-model Rule settings table as a named, commented constant, each comment citing its FR or research id, plus unit constants (`METRES_PER_KM = 1000`, `METRES_PER_MILE = 1609.344`, `SECONDS_PER_MINUTE = 60`, `DAYS_PER_WEEK = 7`) so domain code needs no bare numbers
- [X] T010 [P] Write `tests/unit/test_numbers.py` for `round_half_up` (150.75 → 151, 164.82 → 165, 2.5 → 3), `parse_pace("4:50") == 290`, rejection of "4:60", "450", "", "1:59", "15:01", and `format_pace(290.4) == "4:50"`, `format_duration(3127.4) == "52:07"`, `format_duration(5400) == "1:30:00"` — confirm it fails
- [X] T011 [P] Implement `round_half_up`, `parse_pace`, `format_pace`, and `format_duration` in `src/strava_predictor/domain/numbers.py` (pace accepted from 2:00 to 15:00 per km, seconds 00–59)
- [X] T012 Create value objects and enums in `src/strava_predictor/domain/models.py` exactly as in data-model.md: `Activity`, `ExclusionReason` (`NOT_A_RUN`, `OUTSIDE_WINDOW`, `NO_DISTANCE`, `NO_MOVING_TIME`, `IMPLAUSIBLE_PACE`), `EffortClass` (`EASY`, `MODERATE`, `HARD`, `UNKNOWN`), `RunnerInputs`, `DataSummary`, `Warning`, `DataError` with codes `MISSING_COLUMNS`, `EMPTY_FILE`, `MALFORMED_CSV`, `TOO_FEW_RUNS`, `NO_RUN_OVER_3KM`, `Prediction`, `ProjectedResult`, `GoalRating` (`CONSERVATIVE`, `REALISTIC`, `AMBITIOUS`, `VERY_AMBITIOUS`, `UNLIKELY`; confidence `NORMAL` or `LOW`), `TrainingPlan`, `PlanWeek` (phase `BASE`, `BUILD`, `PEAK`, `TAPER`), `Session` (kind `EASY`, `LONG`, `HARD`, `RACE`, day 1–7), and `AnalysisResult`; all frozen dataclasses
- [X] T013 [P] Create the synthetic CSV builder `tests/fixtures/builders.py`: `make_csv(runs, header="strava")` that writes the full real Strava header layout (column names copied from the 100+ column export header, including repeated `Distance`, `Elapsed Time`, `Max Heart Rate`, `Relative Effort`, `Commute`) with `Activity Date` in `%b %d, %Y, %I:%M:%S %p`, the first `Distance` in km (or miles when asked), the second in metres, and `Moving Time` in seconds; plus helpers `run(days_ago, km, minutes, avg=None, name="Morning Run", type="Run")`
- [X] T014 [P] Create static fixture files in `tests/fixtures/` using the builder, all synthetic, with reference date 2026-11-05 noted at the top of a `README.md` there: `typical_runner.csv` (30 runs over 12 weeks, 6 hard ≥ 3 km), `strava_header.csv` (real header layout, 5 runs), `no_hard_runs.csv`, `interval_only.csv`, `missing_columns.csv` (no `Moving Time`), `empty.csv`, `malformed.csv`, `too_few_runs.csv` (2 runs), `stale.csv` (newest run 20 days old), `imperial.csv` (first Distance in miles), `xss.csv` (name `<script>alert(1)</script>`)
- [X] T015 [P] Create shared pytest fixtures in `tests/conftest.py`: `reference_date` (2026-11-05), `default_inputs` (10 km, 12 weeks, 4:50, 4 days, max HR 201), and `load_fixture(name)`
- [X] T016 Write `tests/integration/test_app_shell.py`: `GET /` returns 200 with a form containing `csv_file`, `race_distance_km`, `weeks_to_race`, `goal_pace`, `days_per_week`, and `max_hr` prefilled `201`; every response has `Content-Security-Policy: default-src 'self'`; `GET /static/style.css` returns 200; the HTML contains no `http://` or `https://` URLs — confirm it fails
- [X] T017 Implement the app shell: `src/strava_predictor/web/app.py` (FastAPI app factory `create_app(clock=date.today)`, CSP middleware, static mount, Jinja2 environment with autoescape on), `src/strava_predictor/web/templates/base.html`, `src/strava_predictor/web/templates/form.html`, `src/strava_predictor/web/static/style.css` (hand-written, system fonts only), and `GET /` in `src/strava_predictor/web/routes.py`
- [X] T018 [P] Write `tests/unit/test_main.py` asserting `strava_predictor.__main__.server_config()` returns host `127.0.0.1` and port 8000 by default and disables access-log bodies, then implement `src/strava_predictor/__main__.py` starting Uvicorn with that config
- [X] T019 Create the e2e server fixture in `tests/e2e/conftest.py`: start Uvicorn with `create_app(clock=lambda: date(2026, 11, 5))` in a background thread on a free 127.0.0.1 port for the session, yield the base URL, and stop it afterwards; mark all e2e tests with `e2e`

**Checkpoint**: `scripts/check.py` passes; the form page renders; domain isolation is enforced

---

## Phase 3: User Story 1 - Check a race goal (Priority: P1) 🎯 MVP

**Goal**: Upload a CSV and inputs; see today's pace and time, safe/likely/stretch paces and times, goal rating, and confidence

**Independent Test**: Upload `typical_runner.csv` with known inputs and compare every number to hand-calculated values (spec US1 scenarios 1–8)

### Tests for User Story 1 ⚠️ Write first and confirm they fail

- [X] T020 [P] [US1] Write `tests/unit/test_parsing_columns.py`: repeated `Distance` columns read by position (metre column authoritative, first column used only when metres are blank); first column in miles detected by ratio ≈ 1609 (`imperial.csv`); `strava_header.csv` distances equal metres ÷ 1000; missing required column raises `DataError(MISSING_COLUMNS)` listing the names; empty file raises `EMPTY_FILE`; ragged/undecodable rows raise `MALFORMED_CSV`; dates parsed from `%b %d, %Y, %I:%M:%S %p` and ISO 8601
- [X] T021 [P] [US1] Write `tests/unit/test_parsing_hr.py`: "Avg 165", "Avg: 165", "avg165", "AVG 165" → 165; "Average 150", "Max 190 only", "12 laps" → None; "Avg 165 Max 190, 12 laps" → 165; "Avg 29" and "Avg 251" → None; "Avg 30" and "Avg 250" → valid; missing description → None
- [X] T022 [P] [US1] Write `tests/unit/test_window.py`: only `Run`, `Trail Run`, `Virtual Run` used (others counted `NOT_A_RUN`); runs on the reference date and 83 days before are in, 84 days before is `OUTSIDE_WINDOW`; blank or zero distance → `NO_DISTANCE`; blank or zero moving time → `NO_MOVING_TIME`; pace faster than 2:00/km or slower than 20:00/km → `IMPLAUSIBLE_PACE`; runs without usable heart rate still count toward volume; fewer than 3 usable runs raises `DataError(TOO_FEW_RUNS)`; `weeks_with_runs`, `avg_weekly_km_12` (total ÷ 12), `avg_weekly_km_4` (total of last 4 seven-day weeks ÷ 4), `longest_run_km`, and `date_range` are correct; newest run 15 days old adds a stale-data warning and 14 days old does not
- [X] T023 [P] [US1] Write `tests/unit/test_effort.py`: at max HR 201, thresholds are 151 and 165; 151 → EASY, 152 → MODERATE, 164 → MODERATE, 165 → HARD, None → UNKNOWN; at max HR 180 thresholds are 135 and 148; name "Track Intervals" and "6x400 REPEATS" set `is_interval`, "Morning Run" does not
- [X] T024 [P] [US1] Write `tests/unit/test_prediction_today.py`: one hard 5 km run in 25:00 for a 10 km race predicts 3127.4 s (52:07) within 0.1 s; with 5 hard runs only the 3 fastest predictions are averaged; with 2 hard runs both are averaged; hard runs under 3 km are ignored; no hard runs → 3 fastest runs ≥ 3 km used and `used_fallback` true; no run ≥ 3 km raises `DataError(NO_RUN_OVER_3KM)`; all basis runs interval → `interval_only` true; `today_10k_pace_s_per_km` uses the same method with 10 km
- [X] T025 [P] [US1] Write `tests/unit/test_prediction_projection.py`: today 3000 s, 10 weeks, multiplier 1.0 → safe 2940, likely 2910, stretch 2850; fewer than 8 active weeks → rates × 1.25; average under 15 km/week → × 1.25; over 60 km/week → × 0.75; fewer than 8 weeks and over 60 km → × 0.9375; 52 weeks → improvements capped at 4%, 6%, 10% after multipliers and `caps_applied` lists them; 20 weeks stretch exactly 10% is reported as capped only when the uncapped value exceeds 10%
- [X] T026 [P] [US1] Write `tests/unit/test_prediction_distance.py`: long-run target 8 km at 5 km and below, 12 at 10, 18 at 21.0975, 30 at 42.195, 14.70 at 15 km (±0.01), 35 at 100 km; reachable long run = longest × 1.1^(pre-taper weeks); target 18 and reachable 14 → shortfall 22.2% → all three paces slowed by exactly 2% and a note added; shortfall 9.9% → no slowdown; reachable ≥ target → no slowdown; with a 52-week plan and a 2% slowdown, the slowdown is applied after the cap (stretch = today × 0.90 × 1.02); also write `tests/unit/test_taper.py` for `taper_weeks(race_km, weeks)`: 1 for ≤ 10 km, 2 for ≤ 21.1 km, 3 above, shortened to `max(1, weeks − 1)`, so pre-taper weeks = weeks − taper
- [X] T027 [P] [US1] Write `tests/unit/test_rating.py` using safe 294, likely 291, stretch 285 s/km: 295 → CONSERVATIVE; 294 and 291 → REALISTIC; 290 and 285 → AMBITIOUS; 284 and 279.3 → VERY_AMBITIOUS; 279 → UNLIKELY; confidence LOW with reason when hard runs used < 3, LOW with reason when runs with HR / runs used < 0.5, LOW when `used_fallback`; NORMAL otherwise; exactly half with HR → NORMAL
- [X] T028 [P] [US1] Write `tests/unit/test_analysis_us1.py`: `analyse(csv_text, inputs, reference_date)` on `typical_runner.csv` returns a summary, prediction, and rating matching values hand-computed in the test; the same call twice returns equal results (determinism); a different `reference_date` changes the window
- [X] T029 [P] [US1] Write `tests/integration/test_results_us1.py`: `POST /results` with `typical_runner.csv` and default inputs returns 200 showing today's pace and time, safe/likely/stretch paces and times, goal pace and time, rating, confidence, and the "estimates, not guarantees, not medical advice" note; distance 2 km and 50 km and weeks 3 show warnings but still return results; `missing_columns.csv`, `empty.csv`, `malformed.csv`, `too_few_runs.csv` return 400 with the error and no results section
- [X] T030 [P] [US1] Write `tests/integration/test_validation.py`: for each field, each invalid value (distance 0, -1, 101, "abc"; weeks 0, 53, 4.5; goal "4:60", "abc", "1:59"; days 1, 8; max HR 99, 241; missing file on first submit) returns 400 with a message beside that field and every other valid value kept in the re-rendered form
- [X] T031 [P] [US1] Write `tests/integration/test_privacy_security.py`: an upload of 10 MB + 1 byte returns 413 with values kept; during a valid upload of a 3 MB synthetic CSV no file is created (patch `tempfile.SpooledTemporaryFile.rollover`, `tempfile.NamedTemporaryFile`, `tempfile.mkstemp`, and `builtins.open` in write modes to fail the test if called); captured logs at DEBUG contain no activity name, description text, or heart rate value from the upload; `xss.csv` renders `&lt;script&gt;` and never `<script>alert(1)</script>`
- [X] T032 [P] [US1] Write `tests/e2e/test_journey_check_goal.py` (Chromium): open the form, upload `typical_runner.csv`, fill the inputs, submit, and see the summary values, rating, and confidence; assert the time from opening the form to the results being shown is under 2 minutes (SC-001)

### Implementation for User Story 1

- [X] T033 [US1] Implement `parse_activities(csv_text)` in `src/strava_predictor/domain/parsing.py`: header index keeping every position of repeated names, required columns per research R2, unit detection and cross-check, date parsing per R3, `is_interval` per `config.INTERVAL_KEYWORDS`, and `avg_hr` per R5 using `re.compile(r"\bavg\s*:?\s*(\d{2,3})\b", re.IGNORECASE)` then `HR_VALID_MIN`–`HR_VALID_MAX`
- [X] T034 [US1] Implement `select_window(activities, reference_date)` in `src/strava_predictor/domain/window.py` building `DataSummary` with exclusion counts, 12 seven-day weeks counted back from the reference date, `weeks_with_runs`, weekly averages, longest run, date range, and the stale-data warning (`STALE_DATA_DAYS`)
- [X] T035 [P] [US1] Implement `effort_thresholds(max_hr)` and `classify_effort(avg_hr, max_hr)` in `src/strava_predictor/domain/effort.py` using `round_half_up` and `EASY_HR_FRACTION` / `HARD_HR_FRACTION`
- [X] T036 [US1] Implement `taper_weeks(race_km, weeks)` in `src/strava_predictor/domain/taper.py`, then `predict(runs, summary, inputs)` in `src/strava_predictor/domain/prediction.py`: Riegel per FR-019/FR-020, interval-only flag, rate multipliers per FR-023 (both may apply), caps per FR-022, then long-run target interpolation and slowdown per FR-024/FR-025 (applied after the caps) using pre-taper weeks from `taper_weeks`, and `today_10k_pace_s_per_km`
- [X] T037 [US1] Implement `rate_goal(goal_pace_s_per_km, prediction, summary)` in `src/strava_predictor/domain/rating.py` with inclusive boundaries per research R11 and confidence reasons per FR-027
- [X] T038 [US1] Implement `analyse(source, inputs, reference_date)` in `src/strava_predictor/domain/analysis.py` returning `AnalysisResult` (summary, prediction, rating; plan added in US2); `source` is CSV text or already-parsed activities
- [X] T039 [US1] Implement form validation in `src/strava_predictor/web/forms.py`: parse and check each field per data-model `RunnerInputs` ("> 0 and ≤ 100; warning < 3 or > 42.195", "1–52; warning < 4", "m:ss, seconds 00–59, 2:00–15:00", "2–7", "100–240, default 201"), returning inputs, per-field errors, warnings, and the raw values to keep
- [X] T040 [US1] Implement upload handling in `src/strava_predictor/web/app.py`: reject `Content-Length` over `config.MAX_UPLOAD_BYTES` with 413 before parsing, set Starlette `MultiPartParser.spool_max_size` above the limit (verify the attribute in the installed version; if missing, parse the body with python-multipart in memory), decode as UTF-8 with BOM handling, and never log the body
- [X] T041 [US1] Implement `POST /results` in `src/strava_predictor/web/routes.py`: validate, read the upload, call `analyse` with `clock()`, render `results.html` or `form.html` with 400/413 per contracts/http-routes.md
- [X] T042 [US1] Create `src/strava_predictor/web/formatting.py` (template filters for pace, duration, km, rating and confidence labels) and `src/strava_predictor/web/templates/results.html` with the summary section, warnings, notes (caps, slowdown, interval-only), the input form prefilled for editing, and the estimates/not-medical-advice note
- [X] T043 [US1] Run `scripts/check.py`; all US1 tests pass and both coverage gates hold

**Checkpoint**: US1 works end to end and is a usable MVP

---

## Phase 4: User Story 2 - Get a training plan (Priority: P2)

**Goal**: The results page shows a rule-abiding week-by-week plan up to the race

**Independent Test**: Build plans across the whole grid of distances, weeks, and days and check every rule with `check_plan_rules` (spec US2 scenarios 1–6)

### Tests for User Story 2 ⚠️ Write first and confirm they fail

- [X] T044 [P] [US2] Write `tests/unit/test_plan_structure.py` (taper length is already covered by `tests/unit/test_taper.py` from T026): 1-week plan is a single race week; phase split for R pre-taper weeks per research R13 (R = 1 → peak 1; R = 2 → build 1, peak 1; R = 10 → base 4, build 4, peak 2) with base weeks lost first; phases in order BASE, BUILD, PEAK, TAPER
- [X] T045 [P] [US2] Write `tests/unit/test_plan_volume.py`: start = last-4-week average; 0 km falls back to the 12-week average with a warning; normal weeks grow by `VOLUME_GROWTH_RATE` up to `PEAK_VOLUME_MULTIPLIER` × start; every 4th pre-taper week is 22.5% below the week before; the week after a lighter week is ≤ 1.1 × the last normal week; marathon 3-week taper from a 50 km last peak week gives 40, 32.5, 22.5 km of training distance; race-week training distance excludes the race
- [X] T046 [P] [US2] Write `tests/unit/test_plan_sessions.py`: each week has exactly `days_per_week` sessions with one `LONG` (the `RACE` replaces it in the race week); the race is the last session of the final week; hard sessions per research R15; each `HARD` session = 2 km warm-up + hard portion + 1.5 km cool-down; long run grows ≤ 10% a week and never exceeds 50% of the week; days numbered 1–7 and spread evenly
- [X] T047 [P] [US2] Write `tests/unit/test_plan_paces.py`: easy pace range is 1.18–1.27 × today's 10 km pace and does not change with the goal; hard pace moves linearly from today's race pace to the target by the last pre-taper week and stays there in the taper; target = goal clamped to [stretch, today's pace]; `targets_stretch` true and a note added for VERY_AMBITIOUS and UNLIKELY; hard distance per week matches `H = f·V·e / (h(1 − f) + f·e)` within 0.01 km
- [X] T048 [P] [US2] Write `tests/unit/test_plan_rules.py`: `check_plan_rules` returns an empty list for a valid plan and a named violation for each hand-broken plan (week rise 11%, lighter week only 15% lower, wrong session count, two long runs, weekly hard 21% in a non-race week, total 14%, hard pace faster than stretch, easy pace from goal, race not last)
- [X] T049 [US2] Write `tests/unit/test_plan_grid.py`: parametrize distances (3, 5, 10, 21.1, 42.195, 100 km) × weeks (1–52) × days (2–7) with a fixed synthetic prediction; for each plan assert `check_plan_rules(plan, inputs) == []`, where a plan total outside 15–20% is allowed only when the plan carries the "too short" note (FR-035); keep the whole grid under 30 s
- [X] T050 [P] [US2] Write `tests/integration/test_results_plan.py`: `POST /results` shows one table per week with phase, weekly distance, weekly time, easy/hard percentages, and each session's day, type, distance, and target pace; the page says weekly time and hard share are calculated at the fast end of the easy pace range; the stretch-pace note appears for an Unlikely goal; the "hard total outside 15–20%" note appears for a 1-week marathon
- [X] T051 [P] [US2] Write `tests/e2e/test_journey_plan.py` (Chromium): submit valid inputs and see a plan with as many week tables as weeks to race, the final row of the last week being the race

### Implementation for User Story 2

- [X] T052 [US2] Implement `check_plan_rules(plan, inputs)` in `src/strava_predictor/domain/plan_rules.py` covering FR-028 to FR-037 and the clarified FR-029/FR-035 rules
- [X] T053 [US2] Implement `phase_layout` in `src/strava_predictor/domain/plan.py` per research R13, using `taper_weeks` from `src/strava_predictor/domain/taper.py`
- [X] T054 [US2] Implement weekly training distance (start, growth, ceiling, lighter weeks, taper cuts, race excluded) in `src/strava_predictor/domain/plan.py` per research R14
- [X] T055 [US2] Implement paces (easy range, hard-pace progression, clamped target) and session building (long run, hard sessions with warm-up and cool-down, easy runs, race) in `src/strava_predictor/domain/plan.py` per research R15 and R16, computing weekly time and hard share at the fast end of the easy range
- [X] T056 [US2] Implement `build_plan(prediction, rating, summary, inputs)` in `src/strava_predictor/domain/plan.py` assembling `TrainingPlan` with total hard share and notes, and add the plan to `analyse` in `src/strava_predictor/domain/analysis.py`
- [X] T057 [US2] Add the plan section to `src/strava_predictor/web/templates/results.html` (one table per week, phase, lighter/race marks, distances, times, percentages, sessions with hard-session breakdown, and a line saying weekly time and hard share are calculated at the fast end of the easy pace range) and styles in `src/strava_predictor/web/static/style.css`
- [X] T058 [US2] Run `scripts/check.py`; all tests including the full grid pass and both coverage gates hold

**Checkpoint**: US1 and US2 both work; every generated plan obeys the rules

---

## Phase 5: User Story 3 - Try another scenario (Priority: P3)

**Goal**: Change inputs and regenerate without uploading the CSV again

**Independent Test**: Upload once, then resubmit with each input changed and no file (spec US3 scenarios 1–2)

### Tests for User Story 3 ⚠️ Write first and confirm they fail

- [X] T059 [P] [US3] Write `tests/unit/test_sessions.py` for `SessionStore(clock)`: `put(runs)` returns a token from `secrets.token_urlsafe(32)`; `get(token)` returns the runs and refreshes expiry; entries expire after `SESSION_TTL_S` (7200 s) idle using an injected clock; at most `MAX_SESSIONS` (10), oldest evicted; unknown token → None; stored value holds parsed activities only, never raw CSV text
- [X] T060 [P] [US3] Write `tests/integration/test_regenerate.py`: first `POST /results` sets a `session` cookie with `HttpOnly`, `SameSite=Strict`, `Path=/`; a second POST with changed distance and no file returns new results; a POST with no file after the session expires (advance the injected clock) or with a bogus cookie returns 400 with "Please upload your CSV again" and keeps other values; an invalid field on regeneration shows the error and the session still works on the next valid submit; a new file replaces the stored runs
- [X] T061 [P] [US3] Write `tests/e2e/test_journey_scenario.py` (Chromium): upload once, change weeks to race from 12 to 20, submit without choosing a file, and see 20 week tables

### Implementation for User Story 3

- [X] T062 [US3] Implement `SessionStore` in `src/strava_predictor/web/sessions.py` per research R7 with an injectable clock and a lock for thread safety
- [X] T063 [US3] Wire the store into `src/strava_predictor/web/app.py` and `src/strava_predictor/web/routes.py`: file optional when a valid session exists, cookie set or refreshed on success, re-upload message otherwise; form and results pages say when a CSV is already loaded
- [X] T064 [US3] Run `scripts/check.py`; all tests pass and both coverage gates hold

**Checkpoint**: Scenarios can be compared without re-uploading

---

## Phase 6: User Story 4 - Understand the data (Priority: P4)

**Goal**: Show what data was used, what was excluded and why, and how much confidence the result deserves

**Independent Test**: Upload a fixture with known exclusions and missing heart rates and check every count, date, and warning (spec US4 scenarios 1–3)

### Tests for User Story 4 ⚠️ Write first and confirm they fail

- [X] T065 [P] [US4] Create `tests/fixtures/mixed_quality.csv` with the builder: 12 usable runs (5 with HR, 3 hard), 2 rides, 3 runs older than 84 days, 1 run with blank distance, 1 with zero moving time, 1 with a 1:30/km pace; record expected counts in `tests/fixtures/README.md`
- [X] T066 [P] [US4] Write `tests/integration/test_data_summary.py`: results for `mixed_quality.csv` show runs used 12, excluded 8 with each reason and count, runs with usable HR 5, hard runs used 3, the date range, low confidence with both reasons, and the basis runs behind today's estimate (escaped names); `stale.csv` shows the out-of-date warning
- [X] T067 [P] [US4] Write `tests/e2e/test_journey_data.py` (Chromium) for the data summary, and `tests/e2e/test_journey_errors.py` for the error journey: upload `missing_columns.csv`, see the error naming `Moving Time` and no plan, then fix by uploading `typical_runner.csv` with the kept values

### Implementation for User Story 4

- [X] T068 [US4] Add the data summary section to `src/strava_predictor/web/templates/results.html`: counts, exclusion reasons in plain words, HR coverage, hard runs used, date range, basis runs table, confidence with reasons, and all warnings; plain-word labels for `ExclusionReason` in `src/strava_predictor/web/formatting.py`
- [X] T069 [US4] Run `scripts/check.py`; all tests pass and both coverage gates hold

**Checkpoint**: All four journeys work and are covered by e2e tests

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Performance, documentation, traceability, and final validation

- [X] T070 [P] Write `tests/integration/test_performance.py`: build a synthetic CSV of 5,000 activities with the builder; after one upload, a regeneration `POST /results` completes in under 2 s (SC-002); fix any slowness found
- [X] T071 [P] Write `README.md`: what the app does, privacy promises, Windows install (`.venv`, `pip install -e ".[dev]"`, `playwright install chromium`), running (`.venv\Scripts\python -m strava_predictor`, http://127.0.0.1:8000), testing (`.venv\Scripts\python scripts\check.py`), where rule values live (`config.py`), and the not-medical-advice note
- [X] T072 [P] Create `specs/001-race-pace-training-plan/traceability.md` mapping every FR-001–FR-043, SC-001–SC-006, and every acceptance scenario to the test(s) that cover it; add any missing test before marking this task complete
- [X] T073 Run every validation scenario in [quickstart.md](./quickstart.md) manually against the running app, timing scenario 1 from opening the form to seeing results (SC-001: under 2 minutes), and record results in `specs/001-race-pace-training-plan/quickstart.md`
- [X] T074 Run `scripts/check.py` one final time; confirm all four gates pass with no skipped or expected-failure tests

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: none
- **Foundational (Phase 2)**: after Setup; blocks all stories
- **US1 (Phase 3)**: after Foundational
- **US2 (Phase 4)**: after US1 domain tasks T033–T038 (the plan needs a prediction, rating, and `taper_weeks`) and T042 (results page)
- **US3 (Phase 5)**: after US1 (needs `POST /results`); independent of US2
- **US4 (Phase 6)**: after US1 (data summary is built in T034); independent of US2 and US3
- **Polish (Phase 7)**: after all stories

### Within Each Story

- Tests first, run, and seen to fail
- Domain before web
- Story checkpoint (`scripts/check.py`) before the next story

### Parallel Opportunities

- T003, T004, T005 in Setup
- T010/T011, T013, T014, T015, T018 in Foundational
- All US1 test tasks T020–T032; then T035 alongside T033/T034
- All US2 test tasks T044–T048, T050, T051
- After US1, US3 and US4 can proceed in parallel with US2
- T070, T071, T072 in Polish

---

## Parallel Example: User Story 1

```text
# Write all US1 tests together:
Task: "T020 Parsing columns tests in tests/unit/test_parsing_columns.py"
Task: "T021 Heart rate parsing tests in tests/unit/test_parsing_hr.py"
Task: "T022 Window and summary tests in tests/unit/test_window.py"
Task: "T023 Effort tests in tests/unit/test_effort.py"
Task: "T024–T026 Prediction tests in tests/unit/test_prediction_*.py"
Task: "T027 Rating tests in tests/unit/test_rating.py"
Task: "T029–T031 Integration tests in tests/integration/"

# Then, in parallel where files differ:
Task: "T035 Effort classification in src/strava_predictor/domain/effort.py"
Task: "T033 Parsing in src/strava_predictor/domain/parsing.py"
```

## Parallel Example: User Story 2

```text
Task: "T044 Plan structure tests in tests/unit/test_plan_structure.py"
Task: "T045 Plan volume tests in tests/unit/test_plan_volume.py"
Task: "T046 Plan sessions tests in tests/unit/test_plan_sessions.py"
Task: "T047 Plan paces tests in tests/unit/test_plan_paces.py"
Task: "T048 Plan rules checker tests in tests/unit/test_plan_rules.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 Setup → Phase 2 Foundational
2. Phase 3 US1
3. **Stop and validate**: upload a synthetic CSV and check the prediction and rating

### Incremental Delivery

1. Setup + Foundational → app shell and gates
2. US1 → goal check (MVP)
3. US2 → training plan
4. US3 → scenario comparison without re-upload
5. US4 → full data transparency
6. Polish → performance, README, traceability

---

## Notes

- [P] tasks touch different files and have no unfinished dependencies
- Every test task ends with "confirm it fails" before its implementation task starts
- Commit after each task or logical group
- Never use or copy the real export in `New Data/`
