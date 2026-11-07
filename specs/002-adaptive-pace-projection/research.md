# Research: Adaptive Race-Day Pace Projection

**Feature**: [spec.md](./spec.md) | **Date**: 2026-11-07

## P1. Improvement curve

- **Decision**: `G(t) = Gmax × (1 − e^(−r·t / Gmax))`.
- **Rationale**: Training gains are fast at first and then level off. This curve's slope at `t = 0`
  is exactly `r`, so short plans behave like 001's linear rates, while long plans approach `Gmax`
  smoothly instead of hitting a hard cap. One formula replaces three rates and three caps.
- **Alternatives considered**: Linear with caps (001; abrupt and arbitrary); power law
  `a·t^b` (no upper limit); Banister fitness–fatigue model (needs per-runner parameters that 12
  weeks of average heart rates cannot fit reliably; kept for later).

## P2. Personal trend

- **Decision**: Theil–Sen slope of `ln(Riegel-predicted race time)` against weeks, over hard runs of
  3 km or more; at least 4 runs over at least 28 days; limited to −0.5% to +1.0% a week.
- **Rationale**: Theil–Sen (median of pairwise slopes) ignores up to about 29% outliers such as a hot
  day or a hilly route, which ordinary least squares does not. Logs make the slope a weekly
  percentage. Hard runs only, because easy-run pace mostly reflects effort, not fitness.
- **Alternatives considered**: Least squares (sensitive to one bad run); best-run-per-week (needs
  more data than 12 weeks usually holds).

## P3. Blending with a typical rate

- **Decision**: weight `w = n / (n + k)` with `k = 8` pseudo-runs; rate `= w·trend + (1 − w)·typical`,
  floored at 0. Rate uncertainty `= s₀·m·sqrt(1 − w)`.
- **Rationale**: This is the normal–normal (Bayesian shrinkage) result when the prior counts as `k`
  observations: few runs → mostly the typical rate, many runs → mostly the runner's own trend; the
  posterior variance shrinks by `(1 − w)`. With 12 weeks of data, `n` is usually 3–15, so the trend
  gets 25–65% of the weight. The floor at zero keeps a training plan from projecting a loss; a
  falling trend is shown to the runner instead.

## P4. Uncertainty and percentiles

- **Decision**: race time is log-normal around the likely time with
  `σ² = σ_today² + σ_improve²`. `σ_today = sqrt((2% + 1% × mean |log2(D_race/D_run)|)² + spread²)`.
  `σ_improve = σ_rate × t × e^(−r·t/Gmax)` (delta method: the curve's derivative with respect to `r`).
  Safe and stretch are the 80th and 20th percentiles: `likely × e^(±z·σ)`, `z = Φ⁻¹(0.8)`.
- **Rationale**: Race-time prediction errors are roughly proportional to time, so logs fit.
  Riegel's error grows with how far the run distance is from the race distance, so the formula
  term grows per doubling. The spread of the basis runs adds the disagreement between them. 80/20
  keeps the 001 rating names meaningful (Conservative > 80% chance, Realistic 50–80%, Ambitious
  20–50%).
- **Calibration**: With 50:00 for 10 km and 10 weeks, the new method gives 49:41 / 48:45 / 47:50
  where 001 gave 49:00 / 48:30 / 47:30: a similar centre with an honest, wider band. At 52 weeks the
  likely improvement is 6.9% (001: capped at 6%).

## P5. Settings

| Name | Value | Spec |
|------|-------|------|
| TYPICAL_WEEKLY_RATE | 0.003 | FR-001 |
| RATE_SIGMA | 0.0015 | FR-007 |
| MAX_IMPROVEMENT | 0.08 | FR-005 |
| TREND_MIN_RUNS | 4 | FR-003 |
| TREND_MIN_SPAN_DAYS | 28 | FR-003 |
| TREND_RATE_MIN / MAX | −0.005 / 0.010 | FR-002 |
| TREND_PRIOR_RUNS | 8 | FR-004 |
| RIEGEL_SIGMA_BASE | 0.02 | FR-006 |
| RIEGEL_SIGMA_PER_DOUBLING | 0.01 | FR-006 |
| SAFE_PROBABILITY | 0.8 | FR-008 (stretch is 1 − 0.8) |

Removed: WEEKLY_RATE_SAFE / LIKELY / STRETCH and IMPROVEMENT_CAP_SAFE / LIKELY / STRETCH.
