# Monte Carlo Backlog Forecast + Walk-Forward Backtest

## Question

Given current defect arrival volume and resolution-time behavior, how many Firefox defects remain unfixed at a 90-day ship date under different staffing scenarios — and does the model actually predict reality?

## Model

- **Arrivals:** Poisson(λ) with λ = **9.87 defects/day** (3,000 / 304 days).
- **Service times:** bootstrap samples from empirical `resolution_days` (3,000 obs). No parametric fit — the real distribution is heavy-tailed in a way lognormal/exponential don't capture.
- **Staffing:** service time divided by `k^α` where `k` ∈ {0.75, 1.0, 1.25, 1.5} and α ∈ {0.3, 0.6, 1.0} is the returns-to-scale exponent (1.0 = perfect scaling, 0.3 = heavy diminishing returns).
- **Servers:** infinite (no queue contention — see Limitations).
- **Trials:** 5,000 × 5 seeds per cell. Convergence verified.

## Diagnostics

**Convergence (baseline, k=1.0, α=1.0, 5 seeds × 5,000 trials):**
- Median range across seeds: **[252, 252]** — zero spread.
- P95 range across seeds: [278, 279] — one bug spread.
- 5,000 trials is enough; Monte Carlo noise is negligible.

**Arrival dispersion:**
- Daily mean = 10.75, variance = 49.24, **variance/mean = 4.58**.
- Strongly overdispersed vs Poisson (where variance/mean = 1). Real arrivals cluster (release days, triage days, weekday-vs-weekend).
- **Consequence:** the Poisson model understates day-to-day burstiness. A week-block resampling model (keeping observed weekday patterns intact) would produce wider confidence intervals. Treat the ±ranges below as lower bounds on real uncertainty.

## Forecast results — open at 90-day ship

Median defects open at ship, by (staffing, α):

| Staffing | α=0.3 | α=0.6 | α=1.0 |
|---|---|---|---|
| 75% | 263 | 275 | 291 |
| 100% (baseline) | 252 | 252 | 252 |
| 125% | 243 | 235 | 225 |
| 150% | 237 | 222 | 203 |

**Headline claim:** +50% staffing cuts the backlog by somewhere between **6%** (α=0.3, heavy diminishing returns) and **19%** (α=1.0, perfect scaling). The true number depends on how much a given team's throughput scales with headcount, which this project doesn't have operational data to pin down.

Plots: `images/mc_backlog_boxplot.png` (α=0.6 across staffing), `images/mc_backlog_summary.png` (all three α values).

## Backtest (walk-forward validation)

The single most important test. If the model can't predict a period we already know the answer for, nothing else matters.

- **Train:** 2024-01-01 → 2024-06-30 (182 days, 1,809 bugs). Fit λ_train = 9.94/day and empirical `resolution_days`_train (median = 9.71 d).
- **Test:** 2024-07-01 → 2024-09-30 (92 days, 848 bugs created). Predict how many of those bugs are still open at Sep 30 2024.
- **Simulation:** 5,000 trials × 5 seeds; k=1.0, α=1.0 (no staffing counterfactual — we're predicting actual history).
- **Compared to actual:** bugs created in the test window whose `cf_last_resolved > 2024-09-30`.

| | Open at Sep 30 2024 |
|---|---|
| Predicted mean | 260.6 |
| Predicted median | 260 |
| Predicted 95% range | **[230, 293]** |
| **Actual** | **231** |
| Error (actual − pred mean) | −29.6 bugs (−12.8%) |
| Actual inside 95% range? | **Yes** |

**Interpretation.** Actual (231) sits near the lower bound of the predicted range. The model slightly over-predicts the backlog, which is consistent with two known biases:

1. Our dataset is `resolution=FIXED` only, snapshotted 2026-10-03. A bug created in Jul-Sep 2024 that was never resolved (still open 2+ years later) is absent from the "actual" count — the actual is a very mild underestimate.
2. The Poisson arrival model understates clustering (var/mean = 4.58). Real arrivals are more concentrated around release windows, so some real bugs arrive late in the window and don't get a chance to finish, but others cluster early and do. Net effect is modest.

Despite those caveats, the actual value lands inside the predicted 95% range — the model is doing meaningful work.

## Limitations (ordered by impact)

- **Service times are from `FIXED` bugs only.** Bugs that got WONTFIX, DUPLICATE, or were never resolved are missing from the service distribution — biasing it toward bugs that *can* be fixed. The medium-tier upgrade is a Kaplan–Meier survival fit on all bugs, including right-censored (still-open) ones.
- **Infinite-server abstraction.** Real teams have finite capacity; the elasticity α approximates diminishing returns but doesn't model queue contention. A true M/G/c queue with `c` = active fixers per month (`assigned_to` field, hashed for privacy) is the big-upgrade path.
- **Poisson arrivals are overdispersed in the real data** (var/mean = 4.58). Week-block resampling would be a cleaner fit without picking a parametric distribution.
- **No warm-up.** The forecast assumes zero open bugs at day 0 of the horizon; realistic ship forecasts should layer the current open-bug count on top. For the backtest this is handled implicitly because we count only bugs created *in* the test window.
- **Staffing-as-elasticity** is a first-order approximation. Real staffing changes affect prioritization and parallelism, not just raw speed.
- **Observational.** This is a forecasting exercise under modeled assumptions, not a causal statement about staffing policy.
