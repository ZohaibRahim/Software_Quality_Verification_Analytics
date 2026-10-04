"""
monte_carlo_backlog.py

Monte Carlo backlog forecast: how many defects remain unfixed by a
ship date under different tester-staffing levels?

Arrivals: Poisson(lambda) with lambda estimated from observed throughput.
Service times: bootstrap samples from empirical resolution_days (no parametric fit).
Staffing: scalar multiplier on effective resolution speed (infinite servers).
"""

from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "analysis_dataset.csv"
OUT_CSV = ROOT / "data" / "processed" / "mc_results.csv"
OUT_BOX = ROOT / "images" / "mc_backlog_boxplot.png"
OUT_BAR = ROOT / "images" / "mc_backlog_summary.png"

HORIZON_DAYS = 90
N_TRIALS = 5000
STAFFING = [0.75, 1.00, 1.25, 1.50]
OBS_SPAN_DAYS = 304   # 2024-01-01 to 2024-10-30
SEED = 42


def simulate(service: np.ndarray, lam: float, mult: float,
             n_trials: int, horizon: float, rng: np.random.Generator) -> np.ndarray:
    arrivals = rng.poisson(lam * horizon, size=n_trials)
    n = int(arrivals.sum())
    trial_id = np.repeat(np.arange(n_trials), arrivals)
    t_arrive = rng.uniform(0, horizon, n)
    t_service = rng.choice(service, size=n, replace=True) / mult
    open_mask = (t_arrive + t_service) > horizon
    return np.bincount(trial_id[open_mask], minlength=n_trials)


def main() -> int:
    service = pd.read_csv(INPUT)["resolution_days"].to_numpy()
    service = service[service > 0]
    lam = len(service) / OBS_SPAN_DAYS
    rng = np.random.default_rng(SEED)

    frames = []
    for mult in STAFFING:
        counts = simulate(service, lam, mult, N_TRIALS, HORIZON_DAYS, rng)
        frames.append(pd.DataFrame({"staffing": mult, "open_at_ship": counts}))
    out = pd.concat(frames, ignore_index=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)

    summary = (out.groupby("staffing")["open_at_ship"]
                  .agg(median="median", mean="mean",
                       p95=lambda x: np.percentile(x, 95), max="max")
                  .round(1))
    print(f"\nMonte Carlo backlog forecast "
          f"({N_TRIALS:,} trials, {HORIZON_DAYS}-day horizon, lambda={lam:.2f}/day):\n")
    print(summary.to_string())

    data_per_staff = [out.loc[out["staffing"] == m, "open_at_ship"].to_numpy() for m in STAFFING]
    labels = [f"{int(m*100)}%" for m in STAFFING]

    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.boxplot(data_per_staff, showfliers=False)
    ax.set_xticks(np.arange(1, len(STAFFING) + 1))
    ax.set_xticklabels(labels)
    ax.set_xlabel("Staffing (% of baseline)")
    ax.set_ylabel("Open defects at ship")
    ax.set_title(f"Monte Carlo: open defects at {HORIZON_DAYS}-day ship")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout(); fig.savefig(OUT_BOX, dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4.2))
    x = np.arange(len(STAFFING)); w = 0.4
    ax.bar(x - w/2, summary["median"], w, label="Median")
    ax.bar(x + w/2, summary["p95"],    w, label="P95")
    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_xlabel("Staffing (% of baseline)")
    ax.set_ylabel("Open defects at ship")
    ax.set_title("Backlog forecast by staffing level")
    ax.legend(); ax.grid(axis="y", alpha=0.3)
    fig.tight_layout(); fig.savefig(OUT_BAR, dpi=150); plt.close(fig)

    print(f"\nwrote {OUT_CSV}\nwrote {OUT_BOX}\nwrote {OUT_BAR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
