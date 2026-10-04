"""
monte_carlo_backtest.py

Rolling walk-forward validation. Four windows: training ends at the first
of April, May, June, July 2024 respectively; each predicts the following
three months and compares to actual bugs created in-window still open at
window end. Reports coverage (how often actual lands in the predicted 95%
range) and mean |% error|.

Arrivals: week-block resampling of training daily counts (preserves
    burstiness, matching the main forecast script).
Service: bootstrap of training resolution_days.
Staffing: k=1.0, alpha=1.0 (we're predicting actual history, no scenario).
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
    header = f"{'window':<34} {'train_n':>7} {'test_n':>7} {'actual':>7} {'pred_mean':>9} {'95% lo':>7} {'95% hi':>7} {'err%':>7} {'inside':>7}"
    print(header); print("-" * len(header))

    for ts, te, vs, ve in WINDOWS:
        TS, TE = pd.Timestamp(ts, tz="UTC"), pd.Timestamp(te, tz="UTC")
        VS, VE = pd.Timestamp(vs, tz="UTC"), pd.Timestamp(ve, tz="UTC")
        tr = df[(df.creation_time >= TS) & (df.creation_time < TE)]
        te_df = df[(df.creation_time >= VS) & (df.creation_time < VE)]

        idx = pd.date_range(TS, TE - pd.Timedelta(days=1), freq="D", tz="UTC")
        daily = tr.set_index("creation_time").resample("D").size().reindex(idx, fill_value=0).to_numpy()
        service = tr["res_days"].to_numpy()
        horizon = (VE - VS).days

        all_counts = np.concatenate([
            simulate(service, daily, TRIALS, horizon, np.random.default_rng(s))
            for s in SEEDS
        ])
        pred_mean = all_counts.mean()
        lo, hi = np.percentile(all_counts, [2.5, 97.5])
        actual = int((te_df["resolved"] > VE).sum())
        err_pct = 100 * (pred_mean - actual) / actual if actual else float("nan")
        inside = int(lo <= actual <= hi)
        results.append({
            "train": f"{ts}->{te}", "test": f"{vs}->{ve}",
            "train_n": len(tr), "test_n": len(te_df), "actual": actual,
            "pred_mean": pred_mean, "lo": lo, "hi": hi,
            "err_pct": err_pct, "inside": inside,
        })
        w = f"train {ts[5:]}->{te[5:]} test {vs[5:]}->{ve[5:]}"
        print(f"{w:<34} {len(tr):>7} {len(te_df):>7} {actual:>7} {pred_mean:>9.1f} {lo:>7.0f} {hi:>7.0f} {err_pct:>+7.1f} {inside:>7}")

    r = pd.DataFrame(results)
    coverage = r["inside"].mean()
    mape = np.abs(r["err_pct"]).mean()
    print(f"\nCoverage: {int(r['inside'].sum())}/{len(r)} windows inside predicted 95% range  "
          f"(target: ~0.95 under correct uncertainty).")
    print(f"Mean |% error|: {mape:.1f}%.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
