"""
fetch_bugzilla_data.py

Retrieves Firefox defect data from the public Mozilla Bugzilla REST API
and writes a raw CSV snapshot to data/raw/firefox_bugs.csv. Also prints a
short inspection report so we can finalize SQL design before loading.

Scope (master project brief §3-§5):
    product    = Firefox
    resolution = FIXED
    creation_time >= 2024-01-01

Usage:
    python scripts/fetch_bugzilla_data.py                 # full pull
    python scripts/fetch_bugzilla_data.py --limit 50      # small sample
    python scripts/fetch_bugzilla_data.py --out other.csv # custom output path
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

BUGZILLA_ENDPOINT = "https://bugzilla.mozilla.org/rest/bug"

REQUESTED_FIELDS = [
    "id",
    "product",
    "component",
    "status",
    "resolution",
    "severity",
    "priority",
    "creation_time",
    "cf_last_resolved",
    "target_milestone",
    "version",
    "summary",
]

PAGE_SIZE = 500          # Bugzilla's REST endpoint caps a single call around this
REQUEST_TIMEOUT = 60     # seconds
POLITE_DELAY = 0.4       # between pages, to be a good API citizen


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_OUTPUT = PROJECT_ROOT / "data" / "raw" / "firefox_bugs.csv"


def fetch_bugs(max_rows: Optional[int] = None, start_date: str = "2024-01-01") -> list[dict]:
    """Paginate the Bugzilla REST endpoint and return a list of bug dicts."""
    collected: list[dict] = []
    offset = 0
    while True:
        remaining = None if max_rows is None else max(0, max_rows - len(collected))
        if remaining == 0:
            break
        limit = PAGE_SIZE if remaining is None else min(PAGE_SIZE, remaining)
        params = {
            "product": "Firefox",
            "resolution": "FIXED",
            "creation_time": start_date,
            "include_fields": ",".join(REQUESTED_FIELDS),
            "limit": limit,
            "offset": offset,
        }
        resp = requests.get(BUGZILLA_ENDPOINT, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        page = resp.json().get("bugs", [])
        if not page:
            break
        collected.extend(page)
        print(f"  page offset={offset:>6}  rows={len(page):>4}  total={len(collected):>6}")
        if len(page) < limit:
            break
        offset += limit
        time.sleep(POLITE_DELAY)
    return collected


def inspect(df: pd.DataFrame) -> None:
    """Short inspection report so we can validate assumptions before SQL design."""
    print("\n--- Inspection ---")
    print(f"rows:    {len(df):,}")
    print(f"columns: {list(df.columns)}")

    if "creation_time" in df.columns:
        s = df["creation_time"].dropna()
        if len(s):
            print(f"creation_time range: {s.min()}  ->  {s.max()}")

    for col in ("severity", "resolution", "status", "priority"):
        if col in df.columns:
            print(f"\n{col} distribution (top 15):")
            print(df[col].astype("string").fillna("<NaN>").value_counts().head(15).to_string())

    if "cf_last_resolved" in df.columns:
        missing_mask = df["cf_last_resolved"].isna() | (df["cf_last_resolved"].astype(str).str.strip() == "")
        print(f"\ncf_last_resolved missing: {int(missing_mask.sum()):,} / {len(df):,}")

    if "component" in df.columns:
        print(f"\nunique components: {df['component'].nunique()}")

    print("--- end inspection ---\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch Firefox defects from Bugzilla.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Cap total rows (useful for a sample run).")
    parser.add_argument("--start-date", default="2024-01-01",
                        help="Earliest creation_time, ISO date.")
    parser.add_argument("--out", type=Path, default=RAW_OUTPUT,
                        help="Output CSV path.")
    args = parser.parse_args()

    scope = f"sample ({args.limit})" if args.limit else "full"
    print(f"Fetching Firefox bugs [{scope}] since {args.start_date} ...")
    bugs = fetch_bugs(max_rows=args.limit, start_date=args.start_date)
    if not bugs:
        print("No rows returned.", file=sys.stderr)
        return 1

    df = pd.DataFrame(bugs).reindex(columns=REQUESTED_FIELDS)
    inspect(df)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(f"Wrote {len(df):,} rows to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
