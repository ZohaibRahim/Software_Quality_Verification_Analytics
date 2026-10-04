# Monte Carlo Backlog Forecast + Rolling Backtest

## Question

Given current defect arrival volume and resolution-time behavior, how many Firefox defects remain unfixed at a 90-day ship date under different staffing scenarios — and does the model predict a period held out from training?

## Model

- **Arrivals:** week-block resampling of observed daily counts. Preserves the day-to-day burstiness that a Poisson model misses (daily var/mean = **5.45** in this dataset).
- **Service times:** bootstrap samples from empirical `resolution_days` (3,000 obs). No parametric fit — the real distribution is heavy-tailed in a way lognormal/exponential don't capture.
- **Staffing:** service time divided by `k^α`, where `k` is the headcount multiplier and `α` is the returns-to-scale exponent:
  - **α = 1.0** — linear best-case (double the staff → half the time).
  - **α = 0.6** — realistic team scaling with coordination overhead.
  - **α = 0.3** — heavy diminishing returns (Brooks's-law regime).
- **Servers:** infinite (no queue contention — the big-upgrade path; see Limitations).
- **Trials:** 5,000 × 5 seeds per cell.

## Diagnostics

**Monte Carlo standard error (baseline, k=1.0, α=1.0):**
- Median: 248.4 ± 0.24 across 5 seeds.
- P95: 285.8 ± 0.37.
- At 5,000 trials × 5 seeds, estimator noise is ~0.1% of the point estimates. More trials would not change the headline.

**Arrival dispersion:**
- Daily mean = 9.87, variance = 53.75 → **var/mean = 5.45** (Poisson = 1).
- Strongly overdispersed. Week-block resampling uses the empirical daily sequence directly, so the resulting prediction intervals reflect the real clustering (release days, triage days) rather than Poisson's smoother spread.

## Forecast — open defects at 90-day ship

Median defects open at ship (mean ± MC SE in parentheses):

| Staffing | α=0.3 | α=0.6 | α=1.0 |
|---|---|---|---|
| 75% | 259.6 (±0.24) | 271.6 (±0.24) | 287.6 (±0.24) |
| **100% (baseline)** | **248.4** | **248.4** | **248.4** |
| 125% | 240.4 (±0.24) | 231.8 (±0.20) | 221.4 (±0.24) |
| 150% | 233.4 (±0.24) | 219.0 (±0.32) | 200.2 (±0.20) |

**Headline (defensible claim):** +50% staffing cuts the baseline backlog (248) by somewhere between **6%** (α=0.3) and **19%** (α=1.0). The true number depends on how much a given team's throughput actually scales with headcount — operational data this project doesn't have.

P95 forecasts (planning target — budget for the bad case, not the median):

| Staffing | α=0.3 | α=0.6 | α=1.0 |
|---|---|---|---|
| 75% | 298.0 | 311.0 | 329.0 |
| 100% | 285.8 | 285.8 | 285.8 |
| 125% | 276.8 | 267.6 | 255.8 |
| 150% | 269.2 | 253.2 | 232.4 |

Plots: `images/mc_backlog_boxplot.png` (α=0.6 across staffing), `images/mc_backlog_summary.png` (all three α values with ±SE error bars).

## Rolling walk-forward backtest

Four expanding-train / 3-month-test windows. Each predicts bugs *created in* the test window that remain open at test end; compared to the actual count from raw data.

| Train window | Test window | Train bugs | Test bugs | **Actual** | Predicted mean | 95% range | Error | Inside? |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2024-01-01 → 2024-04-01 | 2024-04-01 → 2024-07-01 | 866 | 943 | 265 | 247.2 | [202, 296] | −6.7% | ✓ |
| 2024-01-01 → 2024-05-01 | 2024-05-01 → 2024-08-01 | 1,186 | 936 | 265 | 248.7 | [206, 294] | −6.1% | ✓ |
| 2024-01-01 → 2024-06-01 | 2024-06-01 → 2024-09-01 | 1,458 | 901 | 233 | 250.4 | [209, 296] | +7.5% | ✓ |
| 2024-01-01 → 2024-07-01 | 2024-07-01 → 2024-10-01 | 1,809 | 848 | 231 | 255.4 | [212, 300] | +10.6% | ✓ |

**Coverage: 4 of 4 windows inside the predicted 95% range. Mean |% error|: 7.7%.**

Honest reading: this is a working forecast, not a "validated" model. One sign the uncertainty bands are still generous: coverage is 4/4 rather than the 3-4/4 we'd expect under correctly calibrated 95% intervals. The mean error has a slight upward bias in late windows (model over-predicts the backlog by ~8–11% in Jun–Sep), which is consistent with the dataset undercount — bugs created in those months that remained unresolved at the 2026-10-03 fetch date are missing from "actual." A full backlog model would need to re-pull all resolutions including still-open bugs.

## Limitations (ordered by impact)

- **Service times are from `FIXED` bugs only.** Bugs that got WONTFIX, DUPLICATE, or were never resolved are missing — biasing the service distribution toward "fixable" bugs. The medium-tier upgrade is a Kaplan–Meier survival fit on all bugs including right-censored (still-open) ones.
- **Infinite-server abstraction.** Real teams have finite capacity; elasticity α approximates diminishing returns but doesn't model queue contention. A true M/G/c queue with `c` fixers (from Bugzilla's `assigned_to`, hashed for privacy) is the big-upgrade path.
- **Still only one project-year of data.** Rolling backtest results come from four overlapping test windows within 2024. More history (or Firefox 2025 data) would strengthen the coverage claim.
- **No warm-up (initial backlog).** Forecasts count only bugs that arrive *within* the horizon. Realistic ship forecasts should add the current open-bug count on top. For the backtest this is correct by construction (we compare like with like).
- **Staffing-as-elasticity** is a first-order approximation. Real staffing changes affect prioritization and parallelism, not just raw speed.
- **Observational.** This is a forecasting exercise under modeled assumptions, not a causal statement about staffing policy.
