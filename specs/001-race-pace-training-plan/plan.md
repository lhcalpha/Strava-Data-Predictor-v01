# Implementation Plan: Race Pace Prediction and 80/20 Training Plan

**Branch**: `001-race-pace-training-plan` | **Date**: 2026-11-05 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-race-pace-training-plan/spec.md`

## Summary

A local, server-rendered web app for one runner. It reads a Strava activities CSV in memory,
classifies effort from the "Avg" heart rate in each description, predicts today's race time with
the Riegel formula, projects safe, likely, and stretch paces with capped improvement, rates the goal,
and builds a week-by-week 80/20 plan. All rules live in a framework-free domain package with every
value in `config.py`; a thin FastAPI and Jinja2 layer validates the form and renders results.
Parsed runs are kept in server memory under a session cookie so scenarios can be regenerated
without re-uploading.

## Technical Context

**Language/Version**: Python 3.14 (project `.venv`)

**Primary Dependencies**: FastAPI, Uvicorn, Jinja2, python-multipart. Dev: pytest, pytest-cov,
httpx, pytest-playwright (Chromium), Ruff

**Storage**: None. Parsed runs in process memory only (R7)

**Testing**: pytest unit, FastAPI TestClient integration, pytest-playwright end-to-end; coverage
gates 95% domain and 90% overall, branch coverage on

**Target Platform**: Windows 11, local browser, server on 127.0.0.1

**Project Type**: Single-project web app (server-rendered)

**Performance Goals**: Regenerate in under 2 s for a CSV of up to 5,000 activities (SC-002)

**Constraints**: No disk writes or logs of uploaded data, no external scripts or fonts, upload limit
10 MB, deterministic domain with an explicit reference date

**Scale/Scope**: One user, 2 pages, 1 form, about 7 domain modules

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
|-----------|-------|--------|
| I. Testing | TDD order in tasks; unit, integration, and e2e levels; FR and scenario → test mapping; coverage gates 95/90 in `scripts/check.py` | Pass |
| II. Explainable numbers | Every value in `config.py` ([rule settings](./data-model.md#rule-settings)); reference date passed in; results show basis runs and confidence | Pass |
| III. Uncertainty | Confidence, caps, slowdown, stale data, interval-only, and exclusions all shown; no value invented when data is missing | Pass |
| IV. Athlete safety | Easy pace from today's 10 km pace; hard pace clamped to stretch; volume, lighter-week, taper, and 80/20 limits checked by `check_plan_rules` over 1,872 plans | Pass |
| V. Privacy | Uploads kept in memory (R6), no logging of content, 127.0.0.1, CSP `default-src 'self'`, synthetic fixtures only, real exports git-ignored | Pass |
| VI. Separation | `domain/` imports neither FastAPI nor Jinja2 (enforced by a test); routes only validate, call `analyse`, render | Pass |
| VII. Simplicity | No database, accounts, workers, or JS framework; one form and one results route | Pass, with one justified item below |

**Post-design re-check (after Phase 1)**: Pass. The design added rule values the spec does not
state (R13–R16); they are documented, named, and accepted into the spec, which satisfies II.

## Project Structure

### Documentation (this feature)

```text
specs/001-race-pace-training-plan/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── http-routes.md
│   └── domain-api.md
├── checklists/requirements.md
└── tasks.md             # created by /speckit-tasks
```

### Source Code (repository root)

```text
pyproject.toml           # dependencies, Ruff and pytest settings
README.md                # install, test, and run on Windows
scripts/
└── check.py             # runs all four quality gates
src/strava_predictor/
├── __main__.py          # starts Uvicorn on 127.0.0.1
├── config.py            # every rule value, named
├── domain/
│   ├── models.py        # value objects and enums
│   ├── numbers.py       # rounding and pace/time parsing and formatting
│   ├── taper.py         # taper length, shared by prediction and plan
│   ├── parsing.py       # CSV, columns, units, dates, Avg heart rate
│   ├── window.py        # run selection, exclusions, data summary
│   ├── effort.py        # thresholds and classification
│   ├── prediction.py    # Riegel, projection, caps, distance fitness
│   ├── rating.py        # goal rating and confidence
│   ├── plan.py          # phases, volume, sessions, paces
│   ├── plan_rules.py    # check_plan_rules invariant checker
│   └── analysis.py      # analyse() entry point
└── web/
    ├── app.py           # FastAPI app, CSP header, upload limit
    ├── routes.py        # GET /, POST /results
    ├── forms.py         # field validation and kept values
    ├── sessions.py      # in-memory token store
    ├── formatting.py    # m:ss, h:mm:ss, km display
    ├── templates/       # base, form, results
    └── static/style.css
tests/
├── fixtures/            # synthetic CSVs only
├── unit/                # domain tests
├── integration/         # TestClient route tests, privacy and escaping tests
└── e2e/                 # Playwright journeys
```

**Structure Decision**: One Python package under `src/` with `domain/` and `web/` subpackages,
matching the project owner's layout and Constitution VI.

## Complexity Tracking

| Item | Why Needed | Simpler Alternative Rejected Because |
|------|------------|-------------------------------------|
| In-memory session store with expiry | FR-008 regenerate without re-upload | Re-sending the CSV each time breaks FR-008; storing on disk or in a database breaks Constitution V and VII |

## Resolved Planning Decisions

Accepted by the project owner on 2026-11-06 and recorded in spec.md:

1. **Weekly growth and ceiling** (R14): normal weeks grow 8%, up to 1.5× the starting distance
   (spec Assumptions).
2. **Race-week volume** (R14): the 10% rise limit and taper cuts measure training distance without
   the race (FR-029, FR-032).
3. **Conservative goals** (R15): the training target pace is never slower than today's predicted
   pace (FR-028).
