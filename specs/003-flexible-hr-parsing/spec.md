# Feature Specification: Flexible Average Heart Rate Reading

**Feature Branch**: `003-flexible-hr-parsing`

**Created**: 2026-11-07

**Status**: Draft

**Builds on**: [001](../001-race-pace-training-plan/spec.md) FR-012 and research R5;
[002](../002-adaptive-pace-projection/spec.md)

**Input**: The runner writes heart rate as "Avg - 187" and "Avg HR - 176". 001 FR-012 accepts only
"Avg 165", "Avg: 165", and "avg165", so the app found no heart rate in most real runs, no hard runs,
and no trend. The owner considered taking the first number from 100 to 240 in the description and
accepted the recommendation to keep "Avg" as the anchor instead, because the first number is often
not a heart rate (athlete links, "5x1km", race ranks, cadence).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Heart rate is read in the runner's own format (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a description "Avg - 187", **When** it is read, **Then** the average heart rate is 187.
2. **Given** "Avg HR - 176", "Avg HR: 175", "Avg HR-168", "Avg HR 182", or "Avg HR - 160bpm",
   **Then** the value is 176, 175, 168, 182, or 160.
3. **Given** "With [strava://athletes/12345678/12]Some Friend Avg - 143", **Then** the value is
   143; the numbers in the link are ignored.
4. **Given** "5x1km Pace, Rest runs 6x1k in between Avg HR 173", **Then** the value is 173.
5. **Given** "Overall Rank: 125", "19x400m Reps", "Max : 199", or "Average pace: 04:58/km", **Then**
   there is no value.
6. **Given** the 001 formats "Avg 165", "Avg: 165", "avg165", **Then** they still give 165.

## Requirements *(mandatory)*

This **replaces 001 FR-012's list of accepted forms**; the valid range and the rule that all other
numbers are ignored are unchanged.

- **FR-001**: Average heart rate MUST be the 2- or 3-digit number after the word "Avg" (any case),
  optionally followed by "HR", then optional spaces, then an optional ":" or "-", then optional
  spaces. The number MUST NOT be followed by another digit. Only the first such match counts.
- **FR-002**: The value MUST be used only if it is from 30 to 250 (001 FR-012); otherwise the run
  has no usable heart rate.
- **FR-003**: Every other number in the description MUST be ignored, and "Average" MUST NOT count
  as "Avg".

## Success Criteria *(mandatory)*

- **SC-001**: Every scenario above is confirmed by an automated test using made-up descriptions.
- **SC-002**: All quality gates pass.

## Assumptions

- The pattern is `\bavg(?:\s*hr)?\s*[:\-]?\s*(\d{2,3})(?!\d)`, case-insensitive, stored as
  `AVG_HR_PATTERN` in `config.py`.
- The first number from 100 to 240 anywhere in the description was rejected: it misses heart rates
  that follow other numbers and misreads ranks, durations, or cadence as heart rate.
