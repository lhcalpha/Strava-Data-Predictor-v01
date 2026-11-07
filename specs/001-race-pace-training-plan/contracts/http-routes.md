# Contract: HTTP Routes

Server-rendered HTML. All responses carry `Content-Security-Policy: default-src 'self'`.
The server binds to `127.0.0.1` by default.

## GET /

Shows the input form.

- **200**: Form with fields `csv_file`, `race_distance_km`, `weeks_to_race`, `goal_pace`
  (m:ss), `days_per_week`, `max_hr` (prefilled 201). If a valid session cookie exists, the form
  says a CSV is already loaded and the file field is optional.

## POST /results

`multipart/form-data` with the fields above.

| Case | Status | Response |
|------|--------|----------|
| Valid inputs + valid CSV | 200 | Results page: summary, data summary, plan, disclaimer. Sets or refreshes `session` cookie (HttpOnly, SameSite=Strict, Path=/). |
| Valid inputs, no file, valid session | 200 | Results from stored runs. |
| No file and no or expired session | 400 | Form with "Please upload your CSV again" beside the file field; other values kept. |
| Field errors | 400 | Form with one message beside each invalid field; valid values kept. |
| CSV data error (missing columns, empty, malformed, too few runs, no run ≥ 3 km) | 400 | Form with the error message; no prediction or plan. |
| Upload over 10 MB | 413 | Form with "File is larger than 10 MB"; values kept. |

Warnings (distance below 3 km or above 42.195 km, weeks below 4, stale data, low confidence,
trend and improvement curve (002), distance-fitness slowdown, interval-only basis, stretch-pace targeting, plan hard
total outside 15–20%) appear on the results page and never block results.

## GET /static/style.css

Hand-written stylesheet. No other static assets; no external URLs anywhere in the HTML.

## Guarantees checked by integration tests

- Activity names and descriptions containing `<script>` render escaped.
- No uploaded text or heart rate value appears in logs.
- No file is created while handling an upload.
