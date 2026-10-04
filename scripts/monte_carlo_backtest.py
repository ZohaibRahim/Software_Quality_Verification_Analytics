"""
monte_carlo_backtest.py

Rolling walk-forward validation with a naive baseline.

Four overlapping windows (expanding train, 3-month test, sliding by 1 month).
For each window: train the simulation on the training data, predict open-at-
test-end, compare to actual AND to a naive forecast = actual of the 3 months
immediately preceding the test window.

Reports:
  - coverage of the model's 95% range
  - range width (so coverage can be read against band tightness)
  - mean |% error| of the model vs the naive baseline
"""

from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "firefox_bugs.csv"

TRIALS = 5000
SEEDS = [42, 7, 1337, 2024, 99]

WINDOWS = [
    ("2024-01-01", "2024-04-01", "2024-04-01", "2024-07-01"),
    ("2024-01-01", "2024-05-01", "2024-05-01", "2024-08-01"),
    ("2024-01-01", "2024-06-01", "2024-06-01", "2024-09-01"),
    ("2024-01-01", "2024-07-01", "2024-07-01", "2024-10-01"),
]


def simulate(service: np.ndarray, daily: np.ndarray, trials: int, horizon: int,
             rng: np.random.Generator) -> np.ndarray:
    full = len(daily) // 7
    week = daily[:full * 7].reshape(full, 7)
    n_blocks = -(-horizon // 7)
    week_idx = rng.integers(0, full, size=(trials, n_blocks))
    day_counts = week[week_idx].reshape(trials, -1)[:, :horizon]
    arrivals = day_counts.sum(axis=1)
    n = int(arrivals.sum())
    trial_ids = np.repeat(np.arange(trials), arrivals)
    day_of_arrival = np.repeat(np.tile(np.arange(horizon), trials), day_counts.ravel())
    t_arrive = day_of_arrival + rng.uniform(0, 1, n)
    t_service = rng.choice(service, size=n, replace=True)
    open_mask = (t_arrive + t_service) > horizon
    return np.bincount(trial_ids[open_mask], minlength=trials)


def main() -> int:
    df = pd.read_csv(RAW, usecols=["creation_time", "cf_last_resolved"])
    df["creation_time"] = pd.to_datetime(df["creation_time"], utc=True)
    df["resolved"] = pd.to_datetime(df["cf_last_resolved"], utc=True)
    df = df.dropna(subset=["creation_time", "resolved"])
    df["res_days"] = (df["resolved"] - df["creation_time"]).dt.total_seconds() / 86400.0
    df = df[df["res_days"] > 0]

    results = []
    print(f"Rolling walk-forward backtest ({TRIALS:,} trials x {len(SEEDS)} seeds per window):\n")
    header = (f"{'test window':<22} {'actual':>7} {'naive':>6} {'model':>6} "
              f"{'95% range':>12} {'width%':>7} {'naive_err%':>10} {'model_err%':>10} {'inside':>7}")
    print(header); print("-" * len(header))

    for ts, te, vs, ve in WINDOWS:
        TS, TE = pd.Timestamp(ts, tz="UTC"), pd.Timestamp(te, tz="UTC")
        VS, VE = pd.Timestamp(vs, tz="UTC"), pd.Timestamp(ve, tz="UTC")
        tr = df[(df.creation_time >= TS) & (df.creation_time < TE)]
        te_df = df[(df.creation_time >= VS) & (df.creation_time < VE)]
        horizon = (VE - VS).days

        # Train/predict
        idx = pd.date_range(TS, TE - pd.Timedelta(days=1), freq="D", tz="UTC")
        daily = tr.set_index("creation_time").resample("D").size().reindex(idx, fill_value=0).to_numpy()
        service = tr["res_days"].to_numpy()
        all_counts = np.concatenate([
            simulate(service, daily, TRIALS, horizon, np.random.default_rng(s))
            for s in SEEDS
        ])
        pred_mean = all_counts.mean()
        lo, hi = np.percentile(all_counts, [2.5, 97.5])

        # Actual
        actual = int((te_df["resolved"] > VE).sum())

        # Naive baseline: open-at-end of the 3 months IMMEDIATELY BEFORE the test window
        NS = VS - pd.Timedelta(days=horizon)
        naive_df = df[(df.creation_time >= NS) & (df.creation_time < VS)]
        naive = int((naive_df["resolved"] > VS).sum())

        model_err = 100 * (pred_mean - actual) / actual if actual else float("nan")
        naive_err = 100 * (naive - actual) / actual if actual else float("nan")
        width_pct = 100 * (hi - lo) / pred_mean
        inside = int(lo <= actual <= hi)

        results.append({"test": f"{vs}->{ve}", "actual": actual, "naive": naive,
                        "pred_mean": pred_mean, "lo": lo, "hi": hi,
                        "width_pct": width_pct, "model_err": model_err,
                        "naive_err": naive_err, "inside": inside})
        w = f"{vs[5:]}->{ve[5:]}"
        print(f"{w:<22} {actual:>7} {naive:>6} {pred_mean:>6.1f} "
              f"[{lo:>4.0f}, {hi:>4.0f}] {width_pct:>6.1f}% {naive_err:>+9.1f}% {model_err:>+9.1f}% {inside:>7}")

    r = pd.DataFrame(results)
    print(f"\nCoverage (model):  {int(r['inside'].sum())}/{len(r)} windows inside 95% range "
          f"(width averages {r['width_pct'].mean():.1f}% of the point estimate).")
    print(f"Mean |% error|:    model = {r['model_err'].abs().mean():.1f}%   "
          f"naive = {r['naive_err'].abs().mean():.1f}%.")
    verdict = ("model BEATS naive" if r['model_err'].abs().mean() < r['naive_err'].abs().mean()
               else "naive BEATS model" if r['naive_err'].abs().mean() < r['model_err'].abs().mean()
               else "tied")
    print(f"Verdict:           {verdict}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
