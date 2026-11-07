# Test fixtures

All files here are **synthetic**. None of them comes from a real Strava export; only the column
names in `builders.STRAVA_HEADER` copy the real export layout. Never add a real activity file here.

Reference date for every file: **2026-11-05**. Regenerate with:

```powershell
.venv\Scripts\python -m tests.fixtures.generate
```

| File | Contents |
|------|----------|
| `typical_runner.csv` | 30 runs over 12 weeks; 6 hard runs of 3 km or more (one is an interval run) |
| `strava_header.csv` | Real column layout, 5 runs |
| `no_hard_runs.csv` | 12 easy runs, no hard runs |
| `interval_only.csv` | 8 easy runs and 2 hard runs, both interval runs |
| `missing_columns.csv` | No `Moving Time` column |
| `empty.csv` | Empty file |
| `malformed.csv` | Header plus a row that is too short |
| `too_few_runs.csv` | 2 runs |
| `stale.csv` | Newest run 20 days before the reference date |
| `imperial.csv` | First `Distance` column in miles |
| `xss.csv` | A hard run named `<script>alert(1)</script>` |
| `mixed_quality.csv` | See below |

## `mixed_quality.csv` expected counts

- Runs used: 12 (5 with usable heart rate, 3 hard)
- Excluded: 8 — 2 not a run, 3 outside the 12-week window, 1 no distance, 1 no moving time,
  1 implausible pace (10 km in 15 minutes)
