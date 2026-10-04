"""
monte_carlo_backlog.py

Monte Carlo backlog forecast: how many defects remain unfixed by a
ship date under different tester-staffing levels and staffing-return
assumptions (elasticity alpha).

Model
-----
Arrivals: Poisson(lambda). Dispersion of daily counts is reported;
    if variance/mean is far above 1, the Poisson assumption understates
    burstiness and should be swapped for weekly block-resampling.
Service: bootstrap samples from empirical resolution_days.
Staffing: service time divided by k**alpha, where k = headcount
    multiplier and alpha in {0.3, 0.6, 1.0} controls returns-to-scale:
      alpha = 1.0  perfect scaling (double staff -> half time)
      alpha = 0.6  partial scaling
      alpha = 0.3  heavy diminishing returns
    Reported as a RANGE, not a single number.
Convergence: each cell is run with 5 seeds; range across seeds is the
    Monte Carlo noise.
"""

from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "data" / "processed" / "analysis_dataset.csv"
RAW = ROOT / "data" / "raw" / "firefox_bugs.csv"
OUT_CSV = ROOT / "data" / "processed" / "mc_results.csv"
OUT_BOX = ROOT / "images" / "mc_backlog_boxplot.png"
OUT_BAR = ROOT / "images" / "mc_backlog_summary.png"

HORIZON = 90
TRIALS = 5000
STAFFING = [0.75, 1.00, 1.25, 1.50]
ALPHAS = [0.3, 0.6, 1.0]
SEEDS = [42, 7, 1337, 2024, 99]
OBS_SPAN = 304  # 2024-01-01 to 2024-10-30


def simulate(service: np.ndarray, lam: float, k: float, alpha: float,
             trials: int, horizon: float, rng: np.random.Generator) -> np.ndarray:
    speedup = k ** alpha
    arrivals = rng.poisson(lam * horizon, size=trials)
    n = int(arrivals.sum())
    trial_id = np.repeat(np.arange(trials), arrivals)
    t_arrive = rng.uniform(0, horizon, n)
    t_service = rng.choice(service, size=n, replace=True) / speedup
    open_mask = (t_arrive + t_service) > horizon
    return np.bincount(trial_id[open_mask], minlength=trials)


def dispersion(raw: Path) -> tuple[float, float, float]:
    df = pd.read_csv(raw, usecols=["creation_time"])
    df["day"] = pd.to_datetime(df["creation_time"]).dt.date
    daily = df.groupby("day").size()
    return float(daily.mean()), float(daily.var()), float(daily.var() / daily.mean())


def main() -> int:
    service = pd.read_csv(ANALYSIS)["resolution_days"].to_numpy()
    service = service[service > 0]
    lam = len(service) / OBS_SPAN

    mean_d, var_d, disp = dispersion(RAW)
    print(f"Daily arrivals: mean={mean_d:.2f}, var={var_d:.2f}, "
          f"variance/mean={disp:.2f} (1.0 = Poisson)")
    if disp > 1.5:
        print("  WARNING: overdispersed vs Poisson; results understate day-to-day burstiness.")

    rows = []
    for k in STAFFING:
        for a in ALPHAS:
            per_seed = []
            for s in SEEDS:
                counts = simulate(service, lam, k, a, TRIALS, HORIZON, np.random.default_rng(s))
                per_seed.append((np.median(counts), np.percentile(counts, 95)))
            per_seed = np.asarray(per_seed)
            rows.append({
                "staffing": k, "alpha": a,
                "median_mean": per_seed[:, 0].mean(),
                "median_min":  per_seed[:, 0].min(),
                "median_max":  per_seed[:, 0].max(),
                "p95_mean":    per_seed[:, 1].mean(),
                "p95_min":     per_seed[:, 1].min(),
                "p95_max":     per_seed[:, 1].max(),
            })
    out = pd.DataFrame(rows).round(1)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)

    print(f"\nMonte Carlo backlog forecast "
          f"({TRIALS:,} trials x {len(SEEDS)} seeds, {HORIZON}-day horizon, lambda={lam:.2f}/day)")
    print("Median open at ship (range across seeds in parentheses):\n")
    pivot_med = out.pivot(index="staffing", columns="alpha", values="median_mean").round(1)
    print(pivot_med.to_string())
    print("\nP95 open at ship:\n")
    pivot_p95 = out.pivot(index="staffing", columns="alpha", values="p95_mean").round(1)
    print(pivot_p95.to_string())

    base = out[(out.staffing == 1.00) & (out.alpha == 1.0)].iloc[0]
    print(f"\nSeed convergence check: baseline (k=1.0, alpha=1.0) median range across "
          f"{len(SEEDS)} seeds = [{base.median_min:.0f}, {base.median_max:.0f}], "
          f"spread = {base.median_max - base.median_min:.0f} bugs. "
          f"P95 range = [{base.p95_min:.0f}, {base.p95_max:.0f}].")

    # Plots: boxplot at alpha=0.6 only (middle), bar for median across alphas
    rng = np.random.default_rng(42)
    data_per_staff = [simulate(service, lam, k, 0.6, TRIALS, HORIZON, rng) for k in STAFFING]
    labels = [f"{int(k*100)}%" for k in STAFFING]

    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.boxplot(data_per_staff, showfliers=False)
    ax.set_xticks(np.arange(1, len(STAFFING) + 1)); ax.set_xticklabels(labels)
    ax.set_xlabel("Staffing (% of baseline)")
    ax.set_ylabel("Open defects at ship")
    ax.set_title(f"Monte Carlo: open at {HORIZON}-day ship (alpha=0.6)")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout(); fig.savefig(OUT_BOX, dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    x = np.arange(len(STAFFING)); w = 0.25
    for i, a in enumerate(ALPHAS):
        vals = pivot_med[a].to_numpy()
        ax.bar(x + (i - 1) * w, vals, w, label=f"alpha={a}")
    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_xlabel("Staffing (% of baseline)")
    ax.set_ylabel("Median open at ship")
    ax.set_title("Backlog forecast across staffing elasticity assumptions")
    ax.legend(); ax.grid(axis="y", alpha=0.3)
    fig.tight_layout(); fig.savefig(OUT_BAR, dpi=150); plt.close(fig)

    print(f"\nwrote {OUT_CSV}\nwrote {OUT_BOX}\nwrote {OUT_BAR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
