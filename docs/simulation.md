# Monte Carlo Backlog Forecast + Rolling Backtest

## Question

Given current defect arrival volume and resolution-time behavior, how many Firefox defects remain unfixed at a 90-day ship date under different staffing scenarios — and does the model beat a naive forecast?

## Model

- **Arrivals:** week-block resampling of observed daily counts. Preserves the day-to-day burstiness the Poisson model misses (daily var/mean = **5.45** in this dataset).
- **Service times:** bootstrap samples from empirical `resolution_days` (3,000 obs).
- **Staffing:** service time divided by `k^α`:
  - **α = 1.0** — linear best-case (double staff → half time).
  - **α = 0.6** — realistic team scaling with coordination overhead.
  - **α = 0.3** — heavy diminishing returns (Brooks's-law regime).
- **Servers:** infinite (no queue — see Limitations).
- **Trials:** 5,000 × 5 seeds per cell.

## Diagnostics

**Monte Carlo standard error (baseline, k=1.0, α=1.0):** median 248.4 ± 0.24 across 5 seeds, P95 285.8 ± 0.37. Noise is ~0.1% of the estimates — 5,000 trials is enough.

**Arrival dispersion:** daily mean 9.87, variance 53.75, **var/mean = 5.45**. Week-block resampling reflects this clustering; Poisson would not.

## Forecast — median open at 90-day ship

| Staffing | α=0.3 | α=0.6 | α=1.0 |
|---|---|---|---|
| 75% | 259.6 | 271.6 | 287.6 |
| **100%** | **248.4** | **248.4** | **248.4** |
| 125% | 240.4 | 231.8 | 221.4 |
| 150% | 233.4 | 219.0 | 200.2 |

**Headline claim:** +50% staffing cuts the baseline backlog (248) by **6%–19%** depending on returns-to-scale. The true number depends on how much a given team's throughput actually scales with headcount — operational data this project doesn't have.

## Rolling backtest with naive baseline

Four **overlapping** expanding-train / 3-month-test windows (nested training sets; test windows share 2 of 3 months with neighbors). Model vs a naive persistence forecast: *"use the actual open-at-end of the 3 months immediately before the test window."*

| Test window | Actual | Naive | Model | Model 95% range | Range width | Naive err | Model err | Inside? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| Apr–Jun 2024 | 265 | 272 | 247.2 | [202, 296] | 38.0% | +2.6% | −6.7% | ✓ |
| May–Jul 2024 | 265 | 269 | 248.7 | [206, 294] | 35.4% | +1.5% | −6.1% | ✓ |
| Jun–Aug 2024 | 233 | 263 | 250.4 | [209, 296] | 34.7% | +12.9% | +7.5% | ✓ |
| Jul–Sep 2024 | 231 | 265 | 255.4 | [212, 300] | 34.5% | +14.7% | +10.6% | ✓ |

**Headline numbers (honest):**
- Model mean |% error|: **7.7%**.
- Naive mean |% error|: **7.9%**.
- Coverage: 4/4 inside the 95% range, but range width averages **35.7%** of the point estimate — coverage is cheaper to earn when the bands are wide.
- **The model marginally beats the naive baseline.** It wins on the two windows where the actual trends down (Jun–Aug, Jul–Sep); the naive wins on the two early windows where the backlog is roughly flat.

**What the model actually adds over the naive:** calibrated uncertainty intervals. The naive produces a single point estimate with no honesty about range — the model gives a 95% band that contained the actual in every window. For planning, that's the useful difference, not the 0.2pp improvement in point accuracy.

## What this means for the simulation claim

- The model does **not** dramatically outperform a 3-month persistence rule at the point-estimate level.
- Its real contribution is the uncertainty quantification (which the naive doesn't have) and the ability to run counterfactual staffing scenarios (which the naive also can't).
- To improve point accuracy, the natural next upgrades are (1) time-weighted arrival sampling so the model tracks a declining trend, and (2) a true queueing model (`c` fixers, `assigned_to` field) so diminishing returns are structural rather than parametric.

## Limitations (ordered by impact)

- **Service times are from `FIXED` bugs only.** Bugs that got WONTFIX, DUPLICATE, or were never resolved are missing — biasing the service distribution toward "fixable" bugs. Medium-tier upgrade: Kaplan–Meier survival fit on all bugs including right-censored (still-open) ones.
- **Infinite-server abstraction.** Real teams have finite capacity; elasticity α approximates diminishing returns parametrically rather than structurally. Big-upgrade path: M/G/c queue with `c` = active fixers per month (from Bugzilla's `assigned_to`, hashed).
- **Overlapping backtest windows, nested training sets.** Not four independent tests. Coverage is "4/4 inside" across four correlated windows.
- **Wide 95% ranges inflate coverage.** Average range width is 35.7% of the point estimate — a ±18% band is forgiving. Narrower bands (from a well-calibrated model with less uncertainty) would be a stronger test.
- **No warm-up (initial backlog).** The forecast counts only bugs that arrive *within* the horizon. Realistic ship forecasts should add the current open-bug count on top. For the backtest this is correct by construction (both predicted and actual count bugs created in-window only).
- **Observational.** Forecasting exercise under modeled assumptions, not a causal statement about staffing.
