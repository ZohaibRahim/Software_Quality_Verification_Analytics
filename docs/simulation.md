# Monte Carlo Backlog Forecast

## Question

Given current defect arrival volume and resolution-time behavior, how many Firefox defects are expected to remain unfixed by a ship date 90 days out, under four tester-staffing scenarios?

## Model

- **Arrivals:** Poisson process with rate λ estimated from observed throughput: 3,000 FIXED defects over 304 days ⇒ **λ = 9.87 defects/day**.
- **Service times:** bootstrap samples from the empirical `resolution_days` distribution (3,000 observations). No parametric fit — the real distribution is heavy-tailed (High mean 32 d, Lower mean 71 d — see `methodology.md`) in a way that lognormal / exponential don't capture well.
- **Staffing:** scalar multiplier on effective resolution speed. 1.5× staffing ⇒ sampled service times divided by 1.5.
- **Servers:** infinite (no queue contention). This is a deliberate simplification; see Limitations.

## Parameters

| | |
|---|---|
| Trials | 5,000 |
| Horizon | 90 days |
| Staffing levels | 75%, 100%, 125%, 150% |
| Seed | 42 (reproducible) |

Script: `scripts/monte_carlo_backlog.py`.

## Results

Observed defects still open at ship date, by staffing level:

| Staffing | Median | Mean | P95 | Max |
|---|---|---|---|---|
| 75% | 291 | 291.1 | 319 | 354 |
| 100% (baseline) | 252 | 252.3 | 279 | 308 |
| 125% | 225 | 225.3 | 251 | 284 |
| 150% | 204 | 203.8 | 227 | 257 |

Plots: `images/mc_backlog_boxplot.png`, `images/mc_backlog_summary.png`.

## Interpretation

- **Baseline forecast:** ~252 bugs expected to be open at a 90-day ship date; the P95 pessimistic case is 279.
- **Marginal value of staffing:** moving from baseline to +25% headcount reduces median open bugs by ~27 (−11%). Moving to +50% reduces by a further ~21 (−9%). Returns diminish because the service-time distribution is heavy-tailed — a staffing boost speeds the body of the distribution but has less effect on the long tail of slow bugs.
- **For planning:** report the **P95**, not the median. QA plans should hold capacity for the bad case, not the typical case.
- **Decision shape:** if business constraint is "under 250 open bugs at ship, 95th-percentile confidence," only the 150% scenario meets it (P95 = 227 ≤ 250).

## Limitations

- **Arrivals assumed stationary** — no monthly seasonality or trend. The observed data shows month-to-month variation (272–351 bugs/month); a non-stationary Poisson or empirical-rate-per-month would be a natural extension.
- **Infinite-server abstraction** — real teams have finite capacity; a bug arriving when the team is full waits in queue, which lengthens effective service time. True M/G/c queueing would show steeper returns at low staffing.
- **Staffing-as-scalar** — real staffing changes affect which bugs get prioritized, not just raw speed. The scalar is a first-order approximation.
- **Service times are from historical FIXED bugs** — any process change since late 2024 is not reflected.
- **Observational** — like the rest of the project, this is a forecasting exercise under modeled assumptions, not a causal statement about staffing policy.
