# Feature Specification: Adaptive Race-Day Pace Projection

**Feature Branch**: `002-adaptive-pace-projection`

**Created**: 2026-11-07

**Status**: Draft

**Builds on**: [001 Race Pace Prediction and 80/20 Training Plan](../001-race-pace-training-plan/spec.md)

**Input**: "There can be more mathematical and logical ways to predict the race day pace value
instead of the 0.2%, 0.3% and 0.5%." The owner accepted the recommendation to combine (1) a
saturating improvement curve, (2) the runner's own improvement trend blended with a typical rate,
and (3) safe, likely, and stretch as probabilities instead of three fixed rates.

## Summary of the change

Feature 001 projects race day as `today × (1 − rate × weeks)` with fixed rates of 0.2%, 0.3%, and
0.5% and caps of 4%, 6%, and 10%. That treats every runner alike, grows without limit until an
arbitrary cap, and gives no probability. This feature replaces that one step:

1. **Improvement levels off.** Expected improvement follows `G = Gmax × (1 − e^(−r·t / Gmax))`. It
   starts at the weekly rate `r` and approaches the limit `Gmax`, so no separate caps are needed.
2. **The runner's own trend counts.** The weekly rate `r` blends the trend measured from the
   runner's hard runs with a typical rate, weighted by how many hard runs there are.
3. **Safe, likely, and stretch are probabilities.** Likely is the middle estimate; safe and stretch
   are the times the runner has an 80% and a 20% chance of beating, from the combined uncertainty of
   today's estimate and of the improvement. The goal gets a chance of success.

Today's estimate (001 FR-019 to FR-021), the distance-fitness slowdown (001 FR-024, FR-025), the
rating categories (001 FR-026), confidence (001 FR-027), and the plan (001 FR-028 onwards) are
unchanged.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See an honest race-day projection (Priority: P1)

The runner submits the same inputs as before and sees safe, likely, and stretch paces that reflect
their own recent progress, level off for long plans, and come with the chance of beating each one.
They also see the chance of reaching their goal.

**Why this priority**: It is the whole change; the rest of the app consumes these three numbers.

**Independent Test**: Feed known synthetic runs into the prediction and compare the projected times,
the rate, the trend, and the chances with hand-calculated values.

**Acceptance Scenarios**:

1. **Given** today's 10 km estimate of 50:00 from one hard 10 km run, 10 weeks to race, no rate
   multiplier, no personal trend, and no distance-fitness adjustment, **When** paces are projected,
   **Then** likely is 48:45 (4:52/km), safe is 49:41 (4:58/km), and stretch is 47:50 (4:47/km).
2. **Given** the projection in scenario 1, **When** the goal pace is 4:50/km, **Then** the rating
   is Ambitious and the chance of reaching the goal is 35%; at 4:45/km it is Very ambitious (12%);
   at 4:40/km it is Unlikely in this time (3%).
3. **Given** any projection, **When** the goal equals the safe, likely, or stretch time, **Then**
   the chance of reaching it is 80%, 50%, or 20%.
4. **Given** 5 hard 10 km runs, two weeks apart, each 0.5% a week faster than the one before,
   **When** the rate is calculated, **Then** the measured trend is 0.5% a week, its weight is 5/13,
   and the weekly rate is 0.3769%.
5. **Given** fewer than 4 hard runs, or hard runs spread over less than 28 days, **When** the rate is
   calculated, **Then** no personal trend is used and the results say why.
6. **Given** hard runs that are getting slower, **When** the blended rate would be below zero,
   **Then** the rate is zero, the likely time equals today's time (before any distance-fitness
   slowdown), and the results say the trend is flat or slower.
7. **Given** 52 weeks to race, **When** paces are projected, **Then** the likely improvement is
   below the 8% limit and the results describe how improvement levels off.

### Edge Cases

- A single basis run: the spread of today's estimate is zero, so only the formula uncertainty
  counts.
- Runs on the same date have no time between them and are skipped when measuring the trend.
- A measured trend outside −0.5% to +1.0% a week is limited to that range before blending.
- With 1 week to race the safe time can be slower than today's estimate; this is honest, because
  today's estimate is itself uncertain.
- With the fallback (no hard runs), no trend is measured; easy runs say little about race fitness.

## Requirements *(mandatory)*

### Functional Requirements

This list **replaces 001 FR-022 and FR-023** and amends 001 FR-025 and FR-038.

- **FR-001 (typical rate)**: The typical weekly improvement rate MUST be 0.3% multiplied by the rate
  multiplier: ×1.25 if the runner ran in fewer than 8 of the 12 weeks or averaged under 15 km per
  week, and ×0.75 if they averaged over 60 km per week (both can apply).
- **FR-002 (personal trend)**: The trend MUST be measured from every hard run of at least 3 km in the
  window, as the Theil–Sen slope (median of the slopes between every pair of runs on different
  dates) of the natural log of each run's Riegel-predicted race time against time in weeks. The
  weekly trend is `1 − e^slope` (positive means getting faster), limited to −0.5% to +1.0% a week.
- **FR-003 (trend needs data)**: The trend MUST be used only with at least 4 such runs spread over at
  least 28 days, and never with the fallback of 001 FR-020. Otherwise the results MUST say why it
  was not used.
- **FR-004 (blending)**: The trend's weight MUST be `n / (n + 8)` for `n` trend runs. The weekly rate
  MUST be `weight × trend + (1 − weight) × typical rate`, and never below zero. The results MUST show
  the trend, its weight, and the resulting rate.
- **FR-005 (levelling off)**: The improvement limit `Gmax` MUST be 8% multiplied by the rate
  multiplier. The likely improvement MUST be `G = Gmax × (1 − e^(−r × weeks / Gmax))`, and the
  likely time (before 001 FR-025) MUST be `today × (1 − G)`. The results MUST state the starting rate
  and the limit.
- **FR-006 (uncertainty of today)**: The uncertainty of today's estimate, as a share of time, MUST
  be `sqrt(formula² + spread²)`, where `formula = 2% + 1% × the average over basis runs of
  |log2(race distance / run distance)|` and `spread` is the sample standard deviation of the natural
  log of the basis runs' predicted times (zero for one run).
- **FR-007 (uncertainty of improvement)**: The rate's uncertainty MUST be `0.15% × rate multiplier ×
  sqrt(1 − weight)`. The improvement's uncertainty MUST be that times `weeks × e^(−r × weeks / Gmax)`.
- **FR-008 (safe and stretch)**: The total uncertainty `σ` MUST be the square root of the sum of the
  squares of FR-006 and FR-007. Safe MUST be `likely × e^(z·σ)` and stretch `likely × e^(−z·σ)`,
  where `z` is the standard normal value with 80% below it (about 0.8416). Safe is the time with an
  80% chance of being beaten and stretch the time with a 20% chance.
- **FR-009 (distance fitness)**: The 001 FR-025 slowdown MUST be applied to all three times after
  FR-005 to FR-008. 001's improvement caps no longer exist.
- **FR-010 (goal chance)**: The chance of reaching the goal MUST be the probability that a
  log-normal race time with median equal to the likely time and log standard deviation `σ` is at or
  below the goal time. It MUST be shown as a whole percentage.
- **FR-011 (output)**: The results summary MUST show, beside each of safe, likely, stretch, and the
  goal, the chance of running that time or faster, and MUST describe the method in plain words
  instead of the fixed 0.2%, 0.3%, and 0.5% rates.
- **FR-012 (rules)**: Every value above MUST be a named setting in `config.py`, and the same inputs
  and reference date MUST give the same results (001 FR-043).

### Key Entities

- **Prediction** (changed): drops the list of applied caps; adds typical rate, trend (or none), trend
  runs, trend weight, why no trend was used, weekly rate, improvement limit, likely improvement, and
  the uncertainties of today, of the improvement, and in total.
- **Goal rating** (changed): adds the chance of reaching the goal.

## Success Criteria *(mandatory)*

- **SC-001**: Every formula in FR-001 to FR-010 is confirmed by an automated test against a
  hand-calculated value.
- **SC-002**: For every distance, week count, and day count in the 001 plan grid, safe ≥ likely ≥
  stretch, the chances at safe, likely, and stretch are 80%, 50%, and 20%, and every plan still
  passes the 001 plan rules.
- **SC-003**: The rating boundaries of 001 FR-026 still hold and are tested.
- **SC-004**: All quality gates pass with coverage of at least 95% for the domain and 90% overall.

## Assumptions

- The typical rate (0.3% a week, the 001 "likely" rate), its uncertainty (0.15%), the limit (8%),
  the prior strength (8 runs), and the formula uncertainty (2% plus 1% per doubling of distance) are
  starting values chosen to stay close to 001's results for a typical 10–12 week plan. They are
  tunable settings, not proven constants, and the results say they are estimates.
- 80% and 20% are used for safe and stretch so that the 001 rating names keep their meaning:
  Conservative means over 80% chance, Realistic 50–80%, Ambitious 20–50%.
- The 12-week window of 001 FR-009 is kept; a longer history would measure trends better but is out
  of scope.
