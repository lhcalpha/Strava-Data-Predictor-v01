# Quickstart: Race Pace Prediction and 80/20 Training Plan

How to install, check, and try the feature on Windows. Commands run from the project root in
PowerShell.

## Prerequisites

- Python 3.14 with the project's `.venv` created
- Internet access once, to install packages and the Chromium browser for end-to-end tests

## Install

```powershell
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m playwright install chromium
```

## Run all quality gates

```powershell
.venv\Scripts\python scripts\check.py
```

This runs, in order, and stops at the first failure:

```text
ruff check .
ruff format --check .
pytest --cov=strava_predictor --cov-branch --cov-fail-under=90
pytest tests/unit --cov=strava_predictor.domain --cov-branch --cov-fail-under=95
```

Expected: all four pass.

## Run the app

```powershell
.venv\Scripts\python -m strava_predictor
```

Open http://127.0.0.1:8000.

## Validation scenarios

Use the synthetic files in `tests/fixtures/`; never commit a real export.

| # | Steps | Expected |
|---|-------|----------|
| 1 | Upload `typical_runner.csv`; 10 km, 12 weeks, 4:50, 4 days, max HR 201 | Summary, data summary, 12-week plan, disclaimer |
| 2 | On the results page change weeks to 20 and submit without a file | New results, no upload needed |
| 3 | Upload `no_hard_runs.csv` | Low confidence with reason |
| 4 | Upload `missing_columns.csv` | Error naming the missing columns; no plan |
| 5 | Enter weeks 60 | Message beside weeks; other values kept |
| 6 | Restart the server, then submit without a file | "Please upload your CSV again" |
| 7 | Upload `strava_header.csv` (real column layout) | Distances match the metre column |

Plan rules for every distance, week count, and day count are checked automatically by the plan
tests; see [contracts/domain-api.md](./contracts/domain-api.md).

## Validation run: 2026-11-06

Run against `python -m strava_predictor` on 127.0.0.1:8000 in Chromium, synthetic fixtures only.

| # | Result |
|---|--------|
| 1 | Pass. Results in 0.4 s from opening the form (SC-001: under 2 minutes); 12 week tables; rating Conservative; disclaimer shown |
| 2 | Pass. Regenerated without a file; 20 week tables |
| 3 | Pass. "Confidence: Low. There were no hard runs of 3 km or more, so the estimate uses your fastest runs." |
| 4 | Pass. "The file is missing required columns: Moving Time."; no plan shown |
| 5 | Pass. "Weeks to race must be from 1 to 52." beside the field; goal pace 4:50 kept |
| 6 | Pass. After a server restart: "Please upload your CSV again; the earlier upload has expired." |
| 7 | Pass. Basis-run distances 10.0, 8.0, 6.0 km, matching the metre column |
