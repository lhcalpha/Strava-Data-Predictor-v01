# Feature Specification: Race Pace Prediction and 80/20 Training Plan

**Feature Branch**: `001-race-pace-training-plan`

**Created**: 2026-11-05

**Status**: Draft

**Input**: User description: "Build a web app that turns a runner's Strava activity history into an
achievable race pace, an honest rating of their goal, and a week-by-week training plan with an 80/20
easy/hard balance." (full description: `specify.txt` in the project root)

## Clarifications

### Session 2026-11-05

- Q: What is the most the projected race-day time may improve on today's time, in total? → A: Cap
  the total at 4% (safe), 6% (likely), and 10% (stretch), applied after the rate multipliers.
- Q: How much should weekly distance drop in each taper week before the race? → A: Measured from
  the last peak week: 1-week taper −40%; 2-week taper −25%, −50%; 3-week taper −20%, −35%, −55%.
- Q: Should the race count toward the 80/20 limits? → A: Yes, the race counts as hard time; the
  race week alone is exempt from the 20% weekly limit, but the plan total must still be 15% to 20%.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Check a race goal (Priority: P1)

The runner uploads a Strava activities CSV and enters race distance, weeks to race, goal pace, days
per week, and max heart rate. They see today's predicted pace and time, the safe, likely, and stretch
paces and times for race day, and a rating of their goal.

**Why this priority**: This is the core question the runner has ("is my goal realistic?"). It is
useful on its own, without a plan.

**Independent Test**: Upload a synthetic CSV with known runs, submit known inputs, and check that the
predicted, projected, and rated values match hand-calculated results.

**Acceptance Scenarios**:

1. **Given** a valid CSV with at least 3 hard runs of 3 km or more in the last 12 weeks, **When** the
   runner submits valid inputs, **Then** the results show today's pace and time, the safe, likely,
   and stretch paces and times, the goal pace and time, a goal rating, and a confidence level.
2. **Given** a single hard run of 5 km in 25:00 and a 10 km race, **When** today's estimate is
   calculated, **Then** the predicted 10 km time is 52:07 (25:00 × 2^1.06).
3. **Given** today's 10 km estimate of 50:00, 10 weeks to race, normal improvement rates, and no
   distance-fitness adjustment, **When** paces are projected, **Then** safe is 49:00 (4:54/km),
   likely is 48:30 (4:51/km), and stretch is 47:30 (4:45/km).
4. **Given** the projected paces in scenario 3, **When** the goal pace is 4:50/km, **Then** the
   rating is Ambitious; at 4:40/km it is Very ambitious; at 4:39/km it is Unlikely in this time.
5. **Given** a CSV with no hard runs, **When** results are shown, **Then** the estimate uses the 3
   fastest runs and confidence is shown as low.
6. **Given** a CSV whose hard runs are all interval runs, **When** results are shown, **Then** a
   message states that the prediction is probably slower than the runner's true fitness.
7. **Given** a CSV missing a required column, or with fewer than 3 usable runs in the window,
   **When** the runner submits, **Then** a clear error is shown and no prediction or plan is shown.
8. **Given** an invalid input (for example, weeks to race of 60), **When** the runner submits,
   **Then** a clear message appears beside that field and every valid value entered is kept.

---

### User Story 2 - Get a training plan (Priority: P2)

On the same results page, the runner sees a plan for every week up to the race. Each week shows its
phase, weekly distance, weekly time, and easy/hard percentages, and lists each session with its day,
type, distance, and target pace.

**Why this priority**: The plan turns the prediction into action, but it depends on the prediction
from User Story 1.

**Independent Test**: Generate plans for a range of distances, weeks to race, and days per week from
synthetic data, and check every plan against the volume, phase, session, pace, and 80/20 rules.

**Acceptance Scenarios**:

1. **Given** valid inputs and data, **When** results are shown, **Then** the plan has exactly one
   table per week up to the race, and the final week ends with the race.
2. **Given** any generated plan, **When** each week is checked, **Then** it has exactly the requested
   number of sessions, including one long run.
3. **Given** any generated plan, **When** hard running time is measured with the race counted as
   hard, **Then** no week except the race week exceeds 20% hard time, and the whole plan totals 15%
   to 20% hard time unless the plan is too short, in which case the actual total and reason are
   shown.
4. **Given** any generated plan, **When** weekly training distances (excluding the race) are
   compared, **Then** no week rises more than 10% above the previous normal week, and every 4th week
   before the taper is 20% to 25% below the week before.
5. **Given** a marathon plan with a 3-week taper and a last peak week of 50 km, **When** the taper is
   checked, **Then** taper weeks have 40 km, 32.5 km, and 22.5 km of training distance.
5. **Given** a goal rated Very ambitious or Unlikely in this time, **When** the plan is shown,
   **Then** it states that training targets the stretch pace, and no hard pace is faster than it.
6. **Given** any generated plan, **When** easy paces are checked, **Then** they are 1.18 to 1.27
   times today's estimated 10 km pace, regardless of the goal.

---

### User Story 3 - Try another scenario (Priority: P3)

The runner changes any input and regenerates the results without uploading the CSV again.

**Why this priority**: Comparing scenarios (a different race, more weeks, more days) is valuable but
needs User Stories 1 and 2 first.

**Independent Test**: Upload once, then change each input in turn and check that results update
correctly without a new upload.

**Acceptance Scenarios**:

1. **Given** results already shown, **When** the runner changes the race distance and regenerates,
   **Then** new results appear without the CSV being uploaded again.
2. **Given** results already shown, **When** the runner enters an invalid value and regenerates,
   **Then** the field error is shown, other values are kept, and the uploaded data is still
   available.

---

### User Story 4 - Understand the data (Priority: P4)

The runner sees which data was used, what was excluded and why, and how much confidence the result
deserves.

**Why this priority**: It makes results trustworthy and explains low confidence, but it adds no new
prediction.

**Independent Test**: Upload a synthetic CSV with known exclusions and missing heart rates, and check
every count, date, and warning in the data summary.

**Acceptance Scenarios**:

1. **Given** a CSV with runs outside the window, non-running activities, and runs with no usable
   distance or moving time, **When** results are shown, **Then** the data summary shows runs used,
   runs excluded with reasons, runs with usable heart rate, hard runs used, and the date range.
2. **Given** a newest run more than 14 days before the reference date, **When** results are shown,
   **Then** a warning says the data may be out of date.
3. **Given** fewer than half of the runs with usable heart rate, **When** results are shown, **Then**
   confidence is shown as low with the reason.

---

### Edge Cases

- Race distance below 3 km or above 42.195 km: results are produced with a reliability warning.
- Weeks to race below 4: results are produced with a warning; the taper and phases shrink to fit.
- Weeks to race of 1: the plan is a single race week; with a long race, the plan's hard total can
  exceed 20%, and the results show the actual total and explain why.
- Max heart rate changed: effort classes, hard runs used, prediction, and confidence all update.
- Heart rate at exactly the easy or hard threshold (151 and 165 at max 201): 151 is easy, 152 is
  moderate, 164 is moderate, 165 is hard.
- Description with several numbers (for example "Avg 165 Max 190, 12 laps"): only 165 is used.
- Heart rate value outside 30 to 250, or no "Avg" value: the run counts for volume only.
- CSV with two Distance columns in different units: both are read correctly and distances in km
  agree.
- No run of 3 km or more: no prediction can be made, so a clear error is shown.
- Goal pace slower than today's predicted pace: rated Conservative; training targets today's
  predicted pace, so hard paces never get slower over the plan.
- Runner both ran in fewer than 8 weeks and averaged over 60 km per week: both rate multipliers apply.
- Days per week of 2: one long run and one other session each week.
- Long plan (for example 52 weeks at 0.5% per week): stretch improvement stops at the 10% cap, and
  safe and likely stop at 4% and 6%.

## Requirements *(mandatory)*

### Functional Requirements

**Inputs**

- **FR-001**: The runner MUST provide a Strava activities CSV file.
- **FR-002**: Race distance MUST be a positive number of km up to 100. Values below 3 km or above
  42.195 km MUST show a reliability warning.
- **FR-003**: Weeks to race MUST be a whole number from 1 to 52. Values below 4 MUST show a warning.
- **FR-004**: Goal pace MUST be entered as min:sec per km, with seconds from 00 to 59.
- **FR-005**: Days per week MUST be a whole number from 2 to 7.
- **FR-006**: Max heart rate MUST default to 201 bpm, be editable, and be valid from 100 to 240.
- **FR-007**: Invalid input MUST show a clear message beside the field, and valid values already
  entered MUST be kept.
- **FR-008**: The runner MUST be able to change any input and regenerate results without uploading
  the CSV again.

**Reading the CSV**

- **FR-009**: The reference date MUST be today. Only running activities dated within the 12 weeks
  (84 days) up to and including the reference date MUST be used.
- **FR-010**: The system MUST read activity date, name, type, description, distance, and moving time.
  If any of these columns is missing, it MUST show a clear error and no prediction or plan.
- **FR-011**: When the export contains repeated column names with different units (for example two
  Distance columns), the system MUST identify each column's unit and convert all distances to km.
- **FR-012**: Average heart rate MUST be the number directly after "Avg" in the description,
  ignoring case and accepting "Avg 165", "Avg: 165", and "avg165". All other numbers MUST be ignored.
  A value outside 30 to 250 MUST be treated as invalid.
- **FR-013**: A run with a missing or invalid heart rate MUST count toward training volume but MUST
  NOT be used to judge effort.
- **FR-014**: A run with no usable distance or moving time MUST be excluded and counted, with its
  reason, in the data summary. A distance is not usable if it gives a pace faster than 2:00 per km
  or slower than 20:00 per km.
- **FR-015**: Fewer than 3 usable runs in the window MUST produce a clear error and no prediction or
  plan.
- **FR-016**: If the newest run is more than 14 days before the reference date, the system MUST warn
  that the data may be out of date.

**Classifying effort**

- **FR-017**: A run MUST be easy if its average heart rate is at or below 75% of max heart rate, hard
  if at or above 82%, and moderate otherwise. Both thresholds MUST be rounded to the nearest whole
  bpm.
- **FR-018**: A run whose name contains "interval" or "repeat", ignoring case, MUST be marked as an
  interval run. Its heart rate is valid; its whole-run pace counts only as a minimum estimate of
  fitness.

**Predicting achievable pace**

- **FR-019**: For each hard run of at least 3 km, the system MUST predict race time with the Riegel
  formula: race time = run moving time × (race distance / run distance) ^ 1.06. Today's estimate
  MUST be the average of the 3 fastest predictions, or of all of them if fewer than 3.
- **FR-020**: If there are no hard runs of at least 3 km, the same method MUST be applied to the 3
  fastest runs of at least 3 km, and the result MUST be marked low confidence.
- **FR-021**: If every run used for the estimate is an interval run, the results MUST state that the
  prediction is probably slower than the runner's true fitness.
- **FR-022**: Race-day times MUST be today's time reduced by weekly improvement rate × weeks to race,
  with rates of 0.2% (safe), 0.3% (likely), and 0.5% (stretch). After the multipliers in FR-023,
  the total improvement MUST be capped at 4% (safe), 6% (likely), and 10% (stretch), and the results
  MUST state when a cap was applied.
- **FR-023**: Each rate MUST be multiplied by 1.25 if the runner ran in fewer than 8 of the 12 weeks
  or averaged under 15 km per week, and by 0.75 if they averaged over 60 km per week.
- **FR-024**: The target long run MUST be 8 km for 5 km, 12 km for 10 km, 18 km for 21.0975 km, and
  30 km for 42.195 km, interpolated linearly by race distance and limited to 8 to 35 km.
- **FR-025**: The reachable long run MUST be the longest run in the window grown by up to 10% per
  training week. For each full 10% that it falls short of the target, all three projected paces MUST
  be slowed by 1%, and the results MUST state this. The slowdown MUST be applied after the
  improvement caps in FR-022.

**Rating the goal**

- **FR-026**: The goal MUST be rated against the projected paces: Conservative (slower than safe),
  Realistic (from safe to likely, inclusive), Ambitious (faster than likely, up to and including
  stretch), Very ambitious (faster than stretch by up to and including 2%), and Unlikely in this time
  (faster than stretch by more than 2%).
- **FR-027**: Confidence MUST be low if fewer than 3 hard runs were used or fewer than half of the
  runs have usable heart rate, and normal otherwise. The reason for low confidence MUST be shown.

**Generating the plan**

- **FR-028**: The training target pace MUST be the goal pace, but never faster than stretch pace and
  never slower than today's predicted race pace. If the goal is rated Very ambitious or Unlikely in
  this time, the plan MUST say that training targets the stretch pace.
- **FR-029**: The taper MUST be 1 week for races up to 10 km, 2 weeks up to 21.1 km, and 3 weeks for
  longer races, shortened when the plan is too short to hold it. Taper training distance (weekly
  distance excluding the race) MUST be measured from the last peak week: a 1-week taper is −40%; a 2-week taper is −25%, then −50%; a
  3-week taper is −20%, −35%, then −55%. A shortened taper MUST use the cuts for its actual length.
- **FR-030**: The remaining weeks MUST be divided into base 40%, build 40%, and peak 20%. Plans under
  8 weeks MUST lose base weeks first.
- **FR-031**: Starting weekly distance MUST be the average of the last 4 weeks.
- **FR-032**: Weekly training distance (weekly distance excluding the race) MUST NOT rise more than
  10% above the previous normal week. Every 4th week before the taper MUST be a lighter week, 20% to
  25% below the week before it.
- **FR-033**: Each week MUST have the requested number of sessions, including one long run, and the
  final week MUST end with the race.
- **FR-034**: Hard time MUST count only the hard portion of a session. Warm-ups, cool-downs, recovery
  jogs, and easy runs MUST count as easy.
- **FR-035**: The 80/20 split MUST be measured by running time. The race MUST count as hard time.
  Hard time MUST NOT exceed 20% in any week except the race week, and MUST total 15% to 20% across
  the whole plan, race included. If a plan is too short for the total to reach this range, the
  results MUST show the actual total and say why.
- **FR-036**: Easy pace MUST be 1.18 to 1.27 times today's estimated 10 km pace, calculated from
  current fitness and never from the goal.
- **FR-037**: Hard pace MUST start at today's predicted race pace and move evenly to the training
  target pace by the end of the peak phase. No hard pace MUST be faster than the stretch pace.

**Output**

- **FR-038**: The results MUST show a summary with today's pace and time, the three projected paces
  and times, goal pace and time, rating, and confidence.
- **FR-039**: The results MUST show a data summary with runs used, runs excluded with reasons, runs
  with usable heart rate, hard runs used, date range, and all warnings.
- **FR-040**: The plan MUST be shown as one table per week with phase, weekly distance, weekly time,
  easy/hard percentages, and each session's day, type, distance, and target pace. The page MUST say
  that weekly time and the hard share are calculated at the fast end of the easy pace range.
- **FR-041**: The results MUST state that they are estimates, not guarantees, and not medical advice.

**Privacy and rules**

- **FR-042**: Uploaded data MUST stay on the machine running the app, MUST NOT be sent to any
  external service, and MUST NOT be written to disk or included in logs.
- **FR-043**: Every threshold, rate, and limit in this specification MUST be a named, documented
  setting, and the same inputs and reference date MUST always give the same results.

### Key Entities

- **Activity**: One row from the CSV: date, name, type, description, distance (km), moving time,
  average heart rate (if usable), effort class, interval flag, and exclusion reason (if excluded).
- **Runner inputs**: Race distance, weeks to race, goal pace, days per week, and max heart rate.
- **Data summary**: Counts of runs used, excluded (by reason), with usable heart rate, and hard runs
  used; date range; warnings.
- **Prediction**: Today's time and pace, the safe, likely, and stretch times and paces, applied rate
  multipliers, distance-fitness adjustment, and notes.
- **Goal rating**: Rating category and confidence level with reasons.
- **Training plan**: Ordered weeks, each with phase, weekly distance, weekly time, easy/hard
  percentages, and sessions.
- **Session**: Day, type (easy, long run, hard, race), distance, target pace, and hard portion.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A runner can go from upload to a complete result in under 2 minutes.
- **SC-002**: Regenerating with new inputs takes under 2 seconds for a CSV of up to 5,000 activities.
- **SC-003**: All generated plans satisfy the volume and 80/20 rules across every supported
  combination of distance, weeks to race, and days per week covered by the tests.
- **SC-004**: Every rating boundary and effort threshold is confirmed by an automated test.
- **SC-005**: Every user journey and acceptance scenario is covered by an automated test.
- **SC-006**: Every excluded run and every warning in the data summary can be traced to a specific
  rule, and no value is shown that the data does not contain.

## Assumptions

- The app runs locally for one runner; there are no accounts, login, or saved history.
- The uploaded data is kept in memory only for the current session so that scenarios can be
  regenerated; it is lost when the app restarts.
- Running activities are those with type Run, Trail Run, or Virtual Run.
- The 12-week window is split into 12 seven-day weeks counted back from the reference date. "Ran in a
  week" means at least one usable run in it, and average weekly distance is the total over 12.
- The last 4 weeks for the starting distance are the 4 most recent seven-day weeks.
- When two Distance columns exist, the one in metres is authoritative; the other is used only if the
  metre value is missing.
- Thresholds are rounded half up (150.75 → 151, 164.82 → 165).
- Today's estimated 10 km pace uses the same Riegel method as the race prediction, with 10 km as the
  race distance.
- Distance-fitness growth compounds weekly over the weeks before the taper.
- When the plan is too short for the full taper, the taper uses all weeks except one, and a 1-week
  plan is a single race week.
- Phase weeks are rounded to whole weeks, filling peak first, then build, then base.
- Lighter weeks are counted from the first plan week and apply only before the taper.
- Normal weeks grow training distance by 8% (below the 10% limit), up to 1.5 times the starting
  weekly distance. If the last 4 weeks average 0 km, the 12-week average is used with a warning.
- Hard share of each non-race week by phase: base 15%, build 18%, peak 19%, taper 15%.
- Hard sessions: 1 a week when days per week is 3 or fewer; otherwise 2 in build and peak and 1 in
  base and taper. Each has a 2 km warm-up and 1.5 km cool-down at easy pace.
- The long run starts at the longest recent run, grows by up to 10% a week toward the target long
  run, and is never more than half the week's distance. In the race week the race replaces it.
- Plan days are labelled Day 1 to Day 7 of each week, because no calendar race date is entered.
- Goal pace is accepted from 2:00 to 15:00 per km.
- Strava account connection, live heart rate, mobile apps, plan adaptation, elevation or weather
  adjustment, and plan export are out of scope.
