# How the Race-Day Prediction Works

This explains, step by step, how the app turns your Strava runs into today's estimate, the safe,
likely, and stretch race-day times, the goal rating, and the chance of reaching your goal. Every
number below is a named setting in [config.py](../src/strava_predictor/config.py) and can be tuned.

The rules come from three specs:
[001](../specs/001-race-pace-training-plan/spec.md) (reading data, today's estimate, rating),
[002](../specs/002-adaptive-pace-projection/spec.md) (projection to race day), and
[003](../specs/003-flexible-hr-parsing/spec.md) (reading heart rate).

```text
CSV ─► runs in the last 12 weeks ─► heart rate & effort ─► today's estimate (Riegel)
                                                   │
                                                   ├─► your trend ─┐
                     volume & consistency ─► typical rate ─────────┴─► weekly rate
                                                                           │
                     levelling-off curve ─► likely time ◄──────────────────┘
                     uncertainty ─► safe (80%) and stretch (20%)
                     long-run check ─► slowdown ─► final times ─► rating & goal chance
```

---

## 1. Which runs are used

- Only **Run**, **Trail Run**, and **Virtual Run** activities from the **12 weeks** (84 days) up to
  today.
- A run needs a usable distance and moving time, with a pace between 2:00 and 20:00 per km.
  Otherwise it is excluded and counted in the data summary.

## 2. Reading average heart rate

The app looks for the number right after the word **"Avg"** in the activity description. "Avg" may
be followed by "HR" and by a colon or a dash:

| Description | Heart rate |
|---|---|
| `Avg 165`, `Avg: 165`, `avg165` | 165 |
| `Avg - 165`, `Avg HR - 165`, `Avg HR: 165`, `Avg HR 165bpm` | 165 |
| `With …/athletes/12345678/12 … Avg - 143` | 143 (link numbers ignored) |
| `Overall Rank: 125`, `19x400m Reps`, `Max : 199`, `Average pace 4:58` | none |

A value outside **30–250** is ignored. A run with no heart rate still counts for weekly distance,
but cannot be classed as easy or hard.

> Pattern: `\bavg(?:\s*hr)?\s*[:\-]?\s*(\d{2,3})(?!\d)`, case-insensitive
> ([parsing.py](../src/strava_predictor/domain/parsing.py#L20)).

## 3. Easy, moderate, or hard

Thresholds come from your max heart rate, rounded half up to whole bpm
([effort.py](../src/strava_predictor/domain/effort.py#L8)):

| Effort | Rule | At max HR 201 |
|---|---|---|
| Easy | ≤ 75% of max | ≤ 151 |
| Moderate | between | 152–164 |
| **Hard** | ≥ 82% of max | **≥ 165** |

A run whose name contains "interval" or "repeat" is an **interval run**. Its heart rate counts, but
its whole-run pace includes the slow jogs, so it understates your fitness.

## 4. Today's estimate (Riegel formula)

Each **hard run of at least 3 km** is converted to a predicted race time:

```text
race time = run time × (race distance / run distance) ^ 1.06
```

Today's estimate is the **average of the 3 fastest** predictions (or all of them if fewer).

- *Example*: 5 km in 25:00 predicts a 10 km of 25:00 × 2^1.06 = **52:07**.
- **No hard runs?** The 3 fastest runs of 3 km or more are used instead, and confidence is low.
- **All basis runs are intervals?** The page warns that the estimate is probably too slow.

The same method with 10 km as the race gives **today's 10 km pace**, which the training plan uses
for easy paces.

Code: [`riegel`, `_basis`, `_estimate`](../src/strava_predictor/domain/prediction.py#L27).

## 5. The typical weekly improvement rate

A typical runner in structured training improves by about **0.3% a week** at first. This is
multiplied by your **rate multiplier**:

| Condition (last 12 weeks) | Multiplier | Why |
|---|---|---|
| Ran in fewer than 8 weeks, or averaged under 15 km/week | × 1.25 | More room to improve |
| Averaged over 60 km/week | × 0.75 | Already well trained |
| Both | × 0.9375 | |

The multiplier also scales the improvement limit (step 8) and the rate's uncertainty (step 9).

## 6. Your own trend

If you have **at least 4 hard runs of 3 km or more, spread over at least 28 days**, the app measures
whether you are actually getting faster:

1. For each such run, take the log of its predicted race time (step 4).
2. Work out the slope between **every pair** of runs on different dates (change in log time per
   week).
3. Take the **median** of those slopes. This is the **Theil–Sen** estimate: one bad day (heat,
   hills, tired legs) cannot drag it, unlike an ordinary straight-line fit.
4. Convert to a weekly percentage: `trend = 1 − e^slope` (positive means getting faster).
5. Limit it to **−0.5% to +1.0% a week**, so one lucky block cannot dominate.

No trend is measured, and the page says why, when there are too few hard runs, they are too close
together, or the estimate used the no-hard-runs fallback.

Code: [`_trend`](../src/strava_predictor/domain/prediction.py#L79).

## 7. Blending trend and typical rate

Twelve weeks of hard runs is not much data, so your trend is **blended** with the typical rate. The
more trend runs, the more weight your own data gets:

```text
weight      = n / (n + 8)          n = number of trend runs
weekly rate = weight × trend + (1 − weight) × typical rate      (never below 0)
```

| Trend runs | Weight of your trend |
|---|---|
| 4 | 33% |
| 7 | 47% |
| 12 | 60% |

This is **Bayesian shrinkage**: the typical rate counts as if it were 8 runs of evidence.

*Example*: 5 hard runs showing 0.5% a week → weight 5/13 = 38% →
rate = 0.385 × 0.5% + 0.615 × 0.3% = **0.377% a week**.

If you are trending slower and the blend falls below zero, the rate is set to **0** (no projected
improvement), and the page says so.

## 8. Improvement levels off

Gains come quickly at first and then flatten. Instead of `rate × weeks`, which grows forever, the
likely improvement follows a curve that starts at the weekly rate and approaches a **limit of 8%**
(× the multiplier):

```text
likely improvement G = limit × (1 − e^(−rate × weeks / limit))
likely time          = today's time × (1 − G)
```

| Weeks (rate 0.3%, limit 8%) | 1 | 4 | 10 | 12 | 20 | 52 |
|---|---|---|---|---|---|---|
| Likely improvement | 0.29% | 1.1% | 2.5% | 2.9% | 4.2% | 6.9% |

For short plans this is almost the same as `rate × weeks`. For long plans it levels off below the
limit, so no separate caps are needed.

## 9. Uncertainty: safe and stretch

The app does not know your race-day time exactly. It combines two sources of uncertainty, each as
a share of time:

**Today's estimate** ([`_sigma_today`](../src/strava_predictor/domain/prediction.py#L112))

```text
formula = 2% + 1% × average |log2(race distance / run distance)|
spread  = standard deviation of the log predicted times of the basis runs (0 for one run)
σ_today = √(formula² + spread²)
```

Riegel is most accurate when the run and race are the same distance and gets less accurate the
further it stretches: a 10 km run predicting a 10 km race gives 2%, a 5 km run predicting 10 km
gives 3%, and a 10 km run predicting a marathon gives about 4.1%.

**The improvement**

```text
rate uncertainty = 0.15% × multiplier × √(1 − weight)
σ_improvement    = rate uncertainty × weeks × e^(−rate × weeks / limit)
```

More trend runs make the rate more certain. The last factor is the slope of the curve, so once
gains have levelled off, uncertainty about the rate matters less.

**Combined**: `σ = √(σ_today² + σ_improvement²)`.

Race time is treated as **log-normal** around the likely time with this σ:

```text
safe    = likely × e^(+0.8416 × σ)     80% chance of running this time or faster
stretch = likely × e^(−0.8416 × σ)     20% chance
```

0.8416 is the point of the standard normal curve with 80% below it.

## 10. Distance fitness check

Speed alone is not enough for longer races, so the app checks your long run:

- **Target long run**: 8 km for 5 km, 12 km for 10 km, 18 km for a half marathon, 30 km for a
  marathon, interpolated between, and held to 8–35 km.
- **Reachable long run**: your longest run in the last 12 weeks, grown by 10% for each week before
  the taper.
- For each **full 10%** the reachable long run falls short of the target, **all three times are
  slowed by 1%**, and the page says so.

*Example*: a half marathon in 1 week with a longest run of 14 km: 14 is 22% short of 18, which is
2 full steps, so the times are slowed by 2%.

## 11. Rating your goal and its chance

The goal pace is compared with the three projected paces:

| Rating | Goal is… | Chance of reaching it |
|---|---|---|
| Conservative | slower than safe | over 80% |
| Realistic | between safe and likely | 50–80% |
| Ambitious | between likely and stretch | 20–50% |
| Very ambitious | up to 2% faster than stretch | under 20% |
| Unlikely in this time | more than 2% faster than stretch | lower still |

The **chance** is the probability that the log-normal race time from step 9 is at or below your
goal time ([`goal_chance`](../src/strava_predictor/domain/rating.py#L52)).

**Confidence** is low, with the reason shown, if fewer than 3 hard runs were used, the fallback was
used, or fewer than half the runs have a usable heart rate.

---

## Worked example

One hard 10 km run in **50:00**, a 10 km race in **10 weeks**, normal volume, no trend (only one
hard run), and a long run that already meets the target.

| Step | Calculation | Result |
|---|---|---|
| Today | 50:00 × (10/10)^1.06 | 50:00 (5:00/km) |
| Rate | 0.3% × 1, no trend | 0.30% a week |
| Improvement | 8% × (1 − e^(−0.003 × 10 / 0.08)) | 2.50% |
| Likely | 50:00 × (1 − 0.0250) | **48:45** (4:52/km) |
| σ_today | 2% + 1% × 0 | 2.00% |
| σ_improvement | 0.15% × 10 × e^(−0.375) | 1.03% |
| σ | √(2.00² + 1.03²) | 2.25% |
| Safe | 48:45 × e^(0.8416 × 0.0225) | **49:41** (4:58/km) |
| Stretch | 48:45 × e^(−0.8416 × 0.0225) | **47:50** (4:47/km) |

| Goal pace | Rating | Chance |
|---|---|---|
| 4:50/km | Ambitious | 35% |
| 4:45/km | Very ambitious | 12% |
| 4:40/km | Unlikely in this time | 3% |

The tests check this example exactly (`test_scenario_1_ten_weeks_from_fifty_minutes` and
`test_scenario_2_rating_and_chance`).

## Settings

| Setting | Value | Step |
|---|---|---|
| `RIEGEL_EXPONENT` | 1.06 | 4 |
| `MIN_PREDICTION_RUN_KM` / `TOP_PREDICTIONS` | 3 km / 3 | 4 |
| `TYPICAL_WEEKLY_RATE` | 0.3% | 5 |
| `LOW_VOLUME_MULTIPLIER` / `HIGH_VOLUME_MULTIPLIER` | 1.25 / 0.75 | 5 |
| `TREND_MIN_RUNS` / `TREND_MIN_SPAN_DAYS` | 4 / 28 days | 6 |
| `TREND_RATE_MIN` / `TREND_RATE_MAX` | −0.5% / +1.0% a week | 6 |
| `TREND_PRIOR_RUNS` | 8 | 7 |
| `MAX_IMPROVEMENT` | 8% | 8 |
| `RIEGEL_SIGMA_BASE` / `RIEGEL_SIGMA_PER_DOUBLING` | 2% / 1% | 9 |
| `RATE_SIGMA` | 0.15% | 9 |
| `SAFE_PROBABILITY` | 0.8 | 9 |
| `LONG_RUN_TARGETS`, `LONG_RUN_GROWTH`, `SHORTFALL_STEP`, `SLOWDOWN_PER_STEP` | see config | 10 |
| `VERY_AMBITIOUS_MARGIN` | 2% | 11 |

## Limitations

- **The rule values are starting values, not fitted constants.** The 0.3% rate, 8% limit, 0.15%
  rate uncertainty, prior of 8 runs, and 2% + 1% Riegel uncertainty were chosen so that a typical
  10–12 week plan gives results close to the original fixed-rate method (spec 001). They have not
  been fitted to race results.
- **Only 12 weeks are used.** A longer history would measure your trend more reliably.
- **Interval runs understate fitness.** If most hard runs are intervals, today's estimate is
  probably slow and the trend reflects interval pace, not race pace.
- **Heat, hills, and wind are not adjusted for.** The trend's median resists single bad days, but
  a whole block of hot weather will still show.
- These are estimates, not guarantees, and not medical advice.
