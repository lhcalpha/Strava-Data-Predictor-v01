# Strava Data Predictor

A small web app for one runner. Upload your Strava activities CSV, enter your race, and get:

- **Today's predicted race pace and time**, from your recent hard runs (Riegel formula).
- **Safe, likely, and stretch paces** for race day: improvement that levels off over time, your own
  trend from recent hard runs blended with a typical rate, and the chance (80%, 50%, 20%) of running
  each time or faster, plus the chance of reaching your goal. See
  [specs/002-adaptive-pace-projection/spec.md](specs/002-adaptive-pace-projection/spec.md).
- **An honest rating of your goal**: Conservative, Realistic, Ambitious, Very ambitious, or
  Unlikely in this time, plus how much confidence the data supports.
- **A week-by-week 80/20 training plan** up to the race: phases, weekly distance and time,
  easy/hard split by running time, and every session with its distance and target pace.

You can change any input and regenerate without uploading the file again.

Results are estimates, not guarantees. This is training guidance, not medical advice.

## Privacy

- The app runs only on your computer and listens on `127.0.0.1`.
- Your CSV is read in memory. It is never written to disk and never logged.
- Nothing is sent to any other service. The pages load no external scripts, fonts, or analytics.
- Parsed runs are kept in memory for up to 2 hours so you can try scenarios. Restarting the app
  clears them.
- Never commit your real export. `New Data/`, `export_*.zip`, and `activities.csv` are git-ignored.

## Install (Windows)

You need Python 3.14. From the project folder in PowerShell:

```powershell
py -3.14 -m venv .venv          # skip if .venv already exists
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m playwright install chromium
```

## Run

```powershell
.venv\Scripts\python -m strava_predictor
```

Open http://127.0.0.1:8000. To get your data, in Strava go to Settings, My Account, Download or
delete your account, Request your archive. Unzip it and upload `activities.csv`.

The inputs are race distance (km), weeks to race, goal pace (min:sec per km), days per week, and
max heart rate (default 201 bpm). Average heart rate is read from the number after "Avg" in each
activity description, for example "Avg 152".

## Test

One command runs every quality gate: lint, format check, all tests with at least 90% coverage, and
the unit tests with at least 95% coverage of the domain code.

```powershell
.venv\Scripts\python scripts\check.py
```

Tests use synthetic CSV files in `tests/fixtures/` only. Regenerate them with
`.venv\Scripts\python -m tests.fixtures.generate`.

## Where the rules live

- `src/strava_predictor/config.py`: every threshold, rate, and limit, named and traced to the
  specification. Change values here, not in the code.
- `src/strava_predictor/domain/`: parsing, effort classification, prediction, rating, and plan
  generation, with no web framework imports.
- `src/strava_predictor/web/`: routes, form validation, templates, and CSS.
- `specs/001-race-pace-training-plan/`: the specification, plan, research, and task list.
