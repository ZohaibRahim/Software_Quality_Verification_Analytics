"""
monte_carlo_backlog.py

Monte Carlo backlog forecast with:
  - Week-block resampling of real daily arrival counts (preserves burstiness
    the Poisson model misses; var/mean of daily arrivals is ~4.6, not 1).
  - Staffing elasticity: service / k^alpha with alpha in {0.3, 0.6, 1.0}.
      alpha = 1.0   linear best-case: double staff -> half time.
      alpha = 0.6   realistic team scaling with some coordination overhead.
      alpha = 0.3   heavy diminishing returns (Brooks's-law regime).
  - Monte Carlo SE on summary stats across seeds (not just min/max).

Service times: bootstrap samples from empirical resolution_days.
Servers: infinite (no queue). Elasticity approximates diminishing returns.
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
OBS_START = pd.Timestamp("2024-01-01", tz="UTC")
OBS_END   = pd.Timestamp("2024-10-31", tz="UTC")   # exclusive upper bound


def daily_arrivals(raw: Path, start: pd.Timestamp, end: pd.Timestamp) -> np.ndarray:
    df = pd.read_csv(raw, usecols=["creation_time"])
    df["creation_time"] = pd.to_datetime(df["creation_time"], utc=True)
    df = df[(df["creation_time"] >= start) & (df["creation_time"] < end)]
    df["day"] = df["creation_time"].dt.floor("D")
    idx = pd.date_range(start, end - pd.Timedelta(days=1), freq="D", tz="UTC")
    return df.groupby("day").size().reindex(idx, fill_value=0).to_numpy()


def simulate(service: np.ndarray, daily_counts: np.ndarray, k: float, alpha: float,
             trials: int, horizon: int, rng: np.random.Generator) -> np.ndarray:
    """Week-block resample arrivals; bootstrap services; divide service by k^alpha."""
    speedup = k ** alpha
    full_weeks = len(daily_counts) // 7
    week_counts = daily_counts[:full_weeks * 7].reshape(full_weeks, 7)
    n_blocks = -(-horizon // 7)  # ceil
    week_idx = rng.integers(0, full_weeks, size=(trials, n_blocks))
    day_counts = week_counts[week_idx].reshape(trials, -1)[:, :horizon]  # (trials, horizon)

    arrivals_per_trial = day_counts.sum(axis=1)
    n = int(arrivals_per_trial.sum())
    trial_ids = np.repeat(np.arange(trials), arrivals_per_trial)
    day_of_arrival = np.repeat(np.tile(np.arange(horizon), trials), day_counts.ravel())
    t_arrive = day_of_arrival + rng.uniform(0, 1, n)
    t_service = rng.choice(service, size=n, replace=True) / speedup
    open_mask = (t_arrive + t_service) > horizon
    return np.bincount(trial_ids[open_mask], minlength=trials)


def main() -> int:
    service = pd.read_csv(ANALYSIS)["resolution_days"].to_numpy()
    service = service[service > 0]
    daily = daily_arrivals(RAW, OBS_START, OBS_END)
    disp = daily.var() / daily.mean()
    print(f"Daily arrivals: n_days={len(daily)}, mean={daily.mean():.2f}, "
          f"var={daily.var():.2f}, var/mean={disp:.2f} (Poisson=1.0)")
    print(f"Using week-block resampling (preserves observed burstiness).\n")

    rows = []
    for k in STAFFING:
        for a in ALPHAS:
            meds, p95s = [], []
            for s in SEEDS:
                counts = simulate(service, daily, k, a, TRIALS, HORIZON, np.random.default_rng(s))
                meds.append(np.median(counts))
                p95s.append(np.percentile(counts, 95))
            meds, p95s = np.asarray(meds), np.asarray(p95s)
            rows.append({
                "staffing": k, "alpha": a,
                "median_mean": meds.mean(),
                "median_se": meds.std(ddof=1) / np.sqrt(len(SEEDS)),
                "p95_mean": p95s.mean(),
                "p95_se": p95s.std(ddof=1) / np.sqrt(len(SEEDS)),
            })
    out = pd.DataFrame(rows).round(2)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)

    print(f"Backlog forecast ({TRIALS:,} trials x {len(SEEDS)} seeds, {HORIZON}-day horizon)\n")
    print("Median open at ship (mean +/- MC SE across seeds):\n")
    pm = out.pivot(index="staffing", columns="alpha", values="median_mean").round(1)
    ps = out.pivot(index="staffing", columns="alpha", values="median_se").round(2)
    for k in STAFFING:
        parts = [f"{k:.2f}  "] + [f"{pm.loc[k, a]:>6.1f} +/- {ps.loc[k, a]:>4.2f}" for a in ALPHAS]
        print("  " + "  ".join(parts))
    print("\nP95 open at ship:\n")
    pm95 = out.pivot(index="staffing", columns="alpha", values="p95_mean").round(1)
    ps95 = out.pivot(index="staffing", columns="alpha", values="p95_se").round(2)
    for k in STAFFING:
        parts = [f"{k:.2f}  "] + [f"{pm95.loc[k, a]:>6.1f} +/- {ps95.loc[k, a]:>4.2f}" for a in ALPHAS]
        print("  " + "  ".join(parts))

    base = out[(out.staffing == 1.0) & (out.alpha == 1.0)].iloc[0]
    print(f"\nSeed convergence: baseline median {base.median_mean:.1f} +/- {base.median_se:.2f} (MC SE), "
          f"P95 {base.p95_mean:.1f} +/- {base.p95_se:.2f}.")

    # Plots
    rng = np.random.default_rng(42)
    data_per_staff = [simulate(service, daily, k, 0.6, TRIALS, HORIZON, rng) for k in STAFFING]
    labels = [f"{int(k*100)}%" for k in STAFFING]

    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.boxplot(data_per_staff, showfliers=False)
    ax.set_xticks(np.arange(1, len(STAFFING) + 1)); ax.set_xticklabels(labels)
    ax.set_xlabel("Staffing (% of baseline)"); ax.set_ylabel("Open defects at ship")
    ax.set_title(f"Monte Carlo: open at {HORIZON}-day ship (alpha=0.6, block resampling)")
    ax.grid(axis="y", alpha=0.3); fig.tight_layout(); fig.savefig(OUT_BOX, dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    x = np.arange(len(STAFFING)); w = 0.25
    for i, a in enumerate(ALPHAS):
        ax.bar(x + (i - 1) * w, pm[a].to_numpy(), w, label=f"alpha={a}",
               yerr=ps[a].to_numpy(), capsize=3)
    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_xlabel("Staffing (% of baseline)"); ax.set_ylabel("Median open at ship")
    ax.set_title("Backlog forecast across staffing elasticity")
    ax.legend(); ax.grid(axis="y", alpha=0.3)
    fig.tight_layout(); fig.savefig(OUT_BAR, dpi=150); plt.close(fig)

    print(f"\nwrote {OUT_CSV}\nwrote {OUT_BOX}\nwrote {OUT_BAR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
