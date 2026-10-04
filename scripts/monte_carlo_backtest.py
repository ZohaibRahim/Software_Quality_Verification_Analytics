"""
monte_carlo_backtest.py

Walk-forward validation of the Monte Carlo backlog model.

Train window: 2024-01-01 to 2024-06-30 (fit lambda and empirical
    resolution_days distribution using only training bugs).
Test window:  2024-07-01 to 2024-09-30 (92 days). Predict how many
    bugs CREATED in the test window are still open at the test end.
Actual: same count computed from the raw data.

Limitation: our fetch was 2026-10-03, resolution=FIXED only. Bugs
created in Jul-Sep 2024 and still unresolved as of 2026-10-03 are
missing, so the actual count is a (very small) undercount of the
true backlog. Fine for walk-forward sanity-check; a complete backtest
needs the medium-tier upgrade (K-M survival on all resolutions).
"""

from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "firefox_bugs.csv"

TRAIN_START = pd.Timestamp("2024-01-01", tz="UTC")
TRAIN_END   = pd.Timestamp("2024-07-01", tz="UTC")   # exclusive
TEST_START  = TRAIN_END
TEST_END    = pd.Timestamp("2024-10-01", tz="UTC")   # exclusive

TRIALS = 5000
SEEDS = [42, 7, 1337, 2024, 99]


def simulate(service: np.ndarray, lam: float, trials: int, horizon: float,
             rng: np.random.Generator) -> np.ndarray:
    arrivals = rng.poisson(lam * horizon, size=trials)
    n = int(arrivals.sum())
    trial_id = np.repeat(np.arange(trials), arrivals)
    t_arrive = rng.uniform(0, horizon, n)
    t_service = rng.choice(service, size=n, replace=True)
    open_mask = (t_arrive + t_service) > horizon
    return np.bincount(trial_id[open_mask], minlength=trials)


def main() -> int:
    df = pd.read_csv(RAW, parse_dates=["creation_time", "cf_last_resolved"])
    df = df.rename(columns={"cf_last_resolved": "resolved"})
    df = df.dropna(subset=["creation_time", "resolved"])
    df["resolution_days"] = (df["resolved"] - df["creation_time"]).dt.total_seconds() / 86400.0
    df = df[df["resolution_days"] > 0]

    train = df[(df["creation_time"] >= TRAIN_START) & (df["creation_time"] < TRAIN_END)]
    test  = df[(df["creation_time"] >= TEST_START)  & (df["creation_time"] < TEST_END)]

    train_days = (TRAIN_END - TRAIN_START).days
    test_days  = (TEST_END  - TEST_START).days
    lam_train = len(train) / train_days
    service_train = train["resolution_days"].to_numpy()

    print(f"Train: {TRAIN_START.date()} -> {TRAIN_END.date()}  "
          f"({train_days}d, {len(train):,} bugs, lambda={lam_train:.2f}/day, "
          f"median_service={np.median(service_train):.2f}d)")
    print(f"Test:  {TEST_START.date()} -> {TEST_END.date()}  "
          f"({test_days}d, {len(test):,} bugs created)")

    per_seed = np.array([
        simulate(service_train, lam_train, TRIALS, test_days, np.random.default_rng(s))
        for s in SEEDS
    ])
    pred_all = per_seed.flatten()
    pred_median = np.median(pred_all)
    pred_mean = pred_all.mean()
    pred_lo, pred_hi = np.percentile(pred_all, [2.5, 97.5])

    actual_open = int((test["resolved"] > TEST_END).sum())
    inside = pred_lo <= actual_open <= pred_hi

    print(f"\nPREDICTED open at test end:  median={pred_median:.0f}, "
          f"mean={pred_mean:.1f}, 95% range=[{pred_lo:.0f}, {pred_hi:.0f}]")
    print(f"ACTUAL open at test end:     {actual_open}")
    err = actual_open - pred_mean
    pct = 100 * err / actual_open if actual_open else float("nan")
    print(f"Error (actual - predicted mean): {err:+.1f} bugs ({pct:+.1f}% of actual). "
          f"Actual {'IS' if inside else 'is NOT'} within predicted 95% range.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
