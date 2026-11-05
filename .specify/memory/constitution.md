# Strava Data Predictor Constitution

## Core Principles

### I. Testing Is Mandatory (NON-NEGOTIABLE)

- Development MUST follow test-driven development: write a test, confirm that it fails, then
  write the code that makes it pass.
- Every functional requirement and acceptance scenario MUST map to at least one automated test.
- A task is not complete, and a change MUST NOT be merged, until all tests pass.
- Tests MUST NOT be skipped, disabled, weakened, or deleted to make a build pass. A test MAY be
  marked as an expected failure only with the project owner's explicit approval.
- Every bug fix MUST include a regression test that fails without the fix.
- Required test levels:
  - Unit tests for all parsing, prediction, rating, and plan-generation rules.
  - Integration tests for each web route, including invalid input.
  - End-to-end browser tests for each primary user journey.
- Minimum line and branch coverage: 95% for domain logic and 90% for the project overall.
  Coverage is a minimum, not proof of quality.

**Rationale**: The app produces numbers a runner will train by; untested rules are unsafe rules.

### II. Correct, Explainable Numbers

- Every prediction, rating, and plan value MUST come from a documented rule.
- Formulas, thresholds, and rates MUST live in named configuration values, never as unexplained
  numbers in code.
- Domain logic MUST be deterministic: the same inputs and reference date MUST give the same
  output.
- The interface MUST show what data a result is based on and how reliable it is.

**Rationale**: A runner can only trust and act on a result they can trace back to its inputs.

### III. Honest About Uncertainty

- An estimate MUST NOT be presented as a guarantee.
- Missing, excluded, or weak data MUST be shown to the user, not hidden.
- Low confidence MUST be shown when the data is too thin to support a strong result.
- The app MUST NOT invent a value that the data does not contain.

**Rationale**: Overconfident predictions lead to poor goals and poor training decisions.

### IV. Athlete Safety

- A goal MUST NOT push training beyond the limits the rules allow.
- Easy paces MUST come from current fitness, not from the goal.
- Hard training paces MUST NOT be faster than the projected stretch pace.
- Plans MUST follow the configured limits on volume growth, recovery, and hard training.
- The app gives training guidance. It MUST NOT present itself as medical advice.

**Rationale**: An ambitious goal is not a reason to risk injury or overtraining.

### V. Privacy by Default

- Running and heart rate data is personal and MUST stay on the machine running the app.
- User data MUST NOT be sent to third-party services, analytics, or external scripts.
- Uploaded CSV data MUST NOT be written to disk or included in logs.
- Automated tests and committed files MUST use synthetic data, never the runner's real activity
  file.

**Rationale**: Health and location-adjacent data must never leave the owner's control.

### VI. Separation of Concerns

- Domain logic MUST be independent of the web framework so that it can be tested alone and
  reused later.
- Web routes MUST only validate input, call domain logic, and present results.

**Rationale**: Isolated domain logic is easier to test exhaustively and to reuse.

### VII. Simplicity

- Build only what the current specification requires.
- Prefer the standard library and a small set of dependencies.
- Accounts, databases, cloud services, or background workers MUST NOT be added unless a
  specification requires them.
- Any added complexity MUST be justified in the implementation plan.

**Rationale**: A small single-user app stays maintainable only if it stays small.

## Product Scope

Strava Data Predictor is a small web app for one runner. It reads a Strava activities CSV,
predicts an achievable race pace, rates the runner's goal, and generates a training plan. It runs
locally on the runner's own machine. Features outside this scope require a specification before
any work begins.

## Development Workflow & Quality Gates

- Every change follows the TDD cycle in Principle I: failing test first, then implementation.
- Before a task is marked complete: all tests pass and coverage meets the Principle I minimums.
- Before a change is merged: it complies with Principles I–VII or carries a justified exception
  recorded in the implementation plan.
- Reviews MUST check for unexplained numeric constants (Principle II), hidden or invented data
  (Principle III), safety-limit bypasses (Principle IV), and any external data transfer or
  persistence of uploaded data (Principle V).

## Governance

- This constitution takes priority over other project practices.
- Every implementation plan MUST include a constitution check, and any violation MUST be resolved
  or explicitly justified before work begins.
- Amendments MUST state the reason and update the version using semantic versioning:
  - MAJOR: removing or redefining a principle.
  - MINOR: adding a principle or section, or materially expanding guidance.
  - PATCH: wording, clarification, or typo fixes.
- Compliance is reviewed at each plan's constitution check and at each change review.

**Version**: 1.0.0 | **Ratified**: 2026-11-05 | **Last Amended**: 2026-11-05
