# Research: Race Pace Prediction and 80/20 Training Plan

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-11-05

Each entry records a decision, why it was chosen, and what else was considered. Entries R13 to R16
add rule values the spec does not state; every one becomes a named setting in `config.py`
(Constitution II) and is listed in [data-model.md](./data-model.md#rule-settings).

## R1. Stack and versions

- **Decision**: Python 3.14 in the existing `.venv`; FastAPI, Uvicorn, Jinja2, python-multipart;
  pytest, pytest-cov, httpx, pytest-playwright (Chromium); Ruff. Versions pinned in `pyproject.toml`
  at install time, using the newest releases that support Python 3.14.
- **Rationale**: Given by the project owner. All are pure Python or ship wheels for 3.14.
- **Alternatives considered**: Flask (no built-in test client parity with typed form handling);
  plain `http.server` (more hand-written request handling, against Constitution VII's intent of a
  *small set* of dependencies rather than none).

## R2. Reading the Strava CSV

- **Decision**: Use `csv.reader` (not `DictReader`) and build a header index that keeps every
  position of a repeated name. Required columns are found by name: `Activity Date`,
  `Activity Name`, `Activity Type`, `Activity Description`, `Moving Time`, and `Distance`. In the
  standard export the first `Distance` (column 7) is in the athlete's display unit (km or miles)
  and the second (column 18) is in metres. The metre column is authoritative; the first column is
  used only when the metre value is blank. Unit of the first column is identified by its ratio to
  the metre column (≈1000 → km, ≈1609 → miles), and every run is cross-checked against moving
  time: a pace faster than 2:00/km or slower than 20:00/km marks the distance unusable.
- **Rationale**: `DictReader` silently keeps only the last of repeated names. Position plus
  cross-checking survives exports with imperial units.
- **Fixture**: `tests/fixtures/strava_header.csv` copies the real 100+ column header row (column
  names only, not personal) with synthetic values.
- **Alternatives considered**: Pandas (heavy dependency, renames duplicates to `Distance.1`).

## R3. Activity dates and the window

- **Decision**: Parse `Activity Date` with format `%b %d, %Y, %I:%M:%S %p` (Strava's English
  export), falling back to ISO 8601. Use the date part only. The window is the 84 days ending on
  and including the reference date; 12 weeks are seven-day blocks counted back from it.
- **Rationale**: Strava writes dates in UTC. Using the date part keeps results deterministic; a
  late-evening run may fall on the next UTC day, which is documented, not corrected.
- **Alternatives considered**: Time zone conversion (no reliable time zone in the export).

## R4. Running activity types

- **Decision**: `Run`, `Trail Run`, and `Virtual Run` (set in `config.RUN_ACTIVITY_TYPES`).
  Other activities are counted as excluded with reason "not a run".

## R5. Average heart rate

- **Decision**: First match of `\bavg\s*:?\s*(\d{2,3})\b` (case-insensitive) in the description;
  valid only from 30 to 250. "Average 150" and "Max 190" are not matched.
- **Rationale**: Given by the project owner; matches the spec's examples.
- **Amended by [003](../003-flexible-hr-parsing/spec.md)** (2026-11-07): the pattern is now
  `\bavg(?:\s*hr)?\s*[:\-]?\s*(\d{2,3})(?!\d)`, which also reads "Avg - 187" and "Avg HR - 176".

## R6. Keeping uploads off disk

- **Decision**: Starlette's multipart parser spools file parts over 1 MB to a temporary file on
  disk. The app raises `MultiPartParser.spool_max_size` above the 10 MB upload limit, so uploads
  stay in memory, and rejects requests whose `Content-Length` exceeds the limit before parsing.
  A privacy test patches `tempfile` and the file system to prove nothing is written.
- **Rationale**: Constitution V forbids writing uploaded data to disk; the framework default
  would break this silently for real exports, which are often over 1 MB.
- **Verify during implementation**: confirm the attribute name in the installed Starlette version;
  if it is unavailable, read the request stream directly with python-multipart's in-memory parser.
- **Alternatives considered**: Asking users to trim the CSV (bad UX).

## R7. Regenerating without re-uploading

- **Decision**: An in-process store maps a random token (`secrets.token_urlsafe(32)`) to the parsed
  runs only, never the raw CSV text. The token goes in a cookie with `HttpOnly` and
  `SameSite=Strict`. Entries expire after 2 hours idle; at most 10 entries are kept, oldest
  evicted first. Expired or unknown tokens show the form with "Please upload your CSV again".
- **Rationale**: Spec FR-008 plus Constitution V and VII (no database, no disk).

## R8. Routes and form handling

- **Decision**: Two pages and one form. `GET /` shows the form. `POST /results` accepts the form;
  the file is required on the first submission and optional afterwards (the stored runs are used).
  Errors re-render the form with messages beside fields and all valid values kept.
- **Rationale**: One form for both first run and regeneration keeps the UI and tests small.
- **Alternatives considered**: Separate `/upload` and `/regenerate` routes (more routes and
  duplicated validation).

## R9. Security of displayed text

- **Decision**: Jinja2 autoescaping on for all templates; no `|safe` on user data. Uvicorn binds
  to `127.0.0.1`. A strict `Content-Security-Policy: default-src 'self'` header blocks any external
  script, font, or style. App logging records routes and status codes only.

## R10. Determinism and numbers

- **Decision**: Domain functions take `reference_date` as a parameter. Times are kept in seconds
  as floats inside the domain and rounded only for display (nearest second for times and paces,
  0.1 km for distances). Rounding of thresholds uses round-half-up, not Python's banker's rounding.
- **Rationale**: Constitution II; spec example 150.75 → 151.

## R11. Goal rating comparisons

- **Decision**: Compare paces in seconds per km. "Faster than stretch by up to 2%" means
  goal pace ≥ stretch pace × 0.98. Boundaries are inclusive as written in FR-026.

## R12. Testing approach

- **Decision**: Unit tests on the domain package only; integration tests through FastAPI
  `TestClient`; end-to-end tests with pytest-playwright against a Uvicorn server started in a
  background thread by a session fixture on a free local port. Plan rules are checked by a single
  invariant checker run over the parametrized grid (6 distances × 52 weeks × 6 day counts = 1,872
  plans), which also keeps the test suite fast.
- **Gate runner**: `python scripts/check.py` runs the four quality-gate commands in order and stops
  at the first failure.

## R13. Plan length, taper, and phases

- **Decision**:
  - Taper length = min(standard taper, max(1, weeks − 1)); the final taper week is the race week.
    A 1-week plan is a single race week.
  - Taper cuts are measured from the last pre-taper week, or from the starting weekly distance
    when there is none.
  - Pre-taper weeks R = weeks − taper. Peak = round(0.2R), at least 1 when R ≥ 1; build =
    round(0.4R), at least 1 when R ≥ 2; base gets the rest. This fills peak, then build, so short
    plans lose base weeks first.

## R14. Weekly volume

- **Decision**:
  - Start = average of the last 4 weeks. If that is 0 km, use the 12-week weekly average and warn.
  - Normal weeks grow by `VOLUME_GROWTH_RATE` = 8% over the previous normal week (below the 10%
    limit), up to `PEAK_VOLUME_MULTIPLIER` = 1.5 × the starting distance.
  - Every 4th pre-taper week is a lighter week, `LIGHTER_WEEK_CUT` = 22.5% below the week before.
  - The 10% limit and the taper cuts apply to training distance excluding the race itself.
- **Rationale**: The spec sets only an upper limit; without a growth rate and a ceiling, a 52-week
  plan would grow over 50-fold. 22.5% sits in the middle of the spec's 20–25% range so rounding
  cannot push it outside.
- **Accepted by the owner (2026-11-06)**: the 8% growth rate, the 1.5× ceiling, and measuring
  training distance without the race; recorded in spec FR-029, FR-032, and Assumptions.

## R15. Sessions and paces

- **Decision**:
  - Each week: one long run, `HARD_SESSIONS_PER_WEEK` hard sessions (1 when days ≤ 3, otherwise
    2 in build and peak and 1 in base and taper), and easy runs for the rest. In the race week the
    race takes the long-run slot and the other sessions are easy.
  - A hard session is a 2 km warm-up and 1.5 km cool-down at easy pace around a hard portion at
    the week's hard pace.
  - Long run starts at the longest run in the window and grows by up to 10% a week toward the
    target long run, never above 50% of the week's distance.
  - Easy pace is shown as the range 1.18–1.27 × today's 10 km pace. Weekly time and the hard share
    are computed at the fast end (1.18), so the hard share shown is the highest it can be.
  - Hard pace moves linearly from today's race pace to the training target pace over the
    pre-taper weeks, and stays at the target in the taper.
- **Accepted by the owner (2026-11-06)**: the training target pace is never slower than today's
  predicted race pace, so a Conservative goal never makes hard paces slower; recorded in FR-028.

## R16. Hard-time shares

- **Decision**: Hard share of each non-race week by phase: base 15%, build 18%, peak 19%, taper
  15%. The hard distance for a week with distance V, hard share f, hard pace h and easy pace e is
  H = f·V·e / (h(1 − f) + f·e). Because every non-race week is between 15% and 19%, the plan total
  stays within 15–20% except where the race week pushes it over; then the results show the actual
  total and the reason (FR-035).
- **Rationale**: Fixed shares inside the allowed band make the weekly and total limits hold by
  construction, which the invariant tests then confirm.
- **Added during implementation**: for long races the race alone can push the plan total over 20%
  (for example 100 km over 52 weeks). The plan then scales every training week's hard share down
  by one factor, found by bisection, until the total is at most 20%. A note appears only when even
  no training hard time would keep the total in range (very short plans).
- **Added during implementation**: with 2 days a week there are no easy runs, so the distance left
  after the long run and the hard portion is added to the hard session's warm-up and cool-down in
  the 2 : 1.5 ratio. When a week is too short for full 2 km and 1.5 km, both shrink in that ratio.
- **Added during implementation**: the long run starts at the longest recent run even when that
  is above the target, so high-volume runners are not cut back; it only grows while below target.
