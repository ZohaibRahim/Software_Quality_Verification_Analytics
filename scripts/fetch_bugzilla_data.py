"""
fetch_bugzilla_data.py

Retrieves Firefox defect data from the public Mozilla Bugzilla REST API and
saves a raw CSV snapshot to data/raw/firefox_bugs.csv.

Design notes (see master project brief §8, §50):
    - This script does ONLY acquisition + light inspection.
      Business transformations happen in SQL.
    - No credentials needed for public Bugzilla data.
    - Request only the fields the project uses.
    - Validate HTTP response; implement pagination if the endpoint caps rows.
    - Print a short inspection report (row/col counts, column names, date range,
      severity distribution, missingness for cf_last_resolved).

Status: SKELETON. Fill in before STEP 2 is checked off in PROGRESS.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Target population: Firefox bugs resolved FIXED, created on/after 2024-01-01.
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

QUERY_PARAMS = {
    "product": "Firefox",
    "resolution": "FIXED",
    "creation_time": "2024-01-01",
    "include_fields": ",".join(REQUESTED_FIELDS),
    # pagination controls go here (limit / offset)
}

RAW_OUTPUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "firefox_bugs.csv"


def fetch_bugs():
    """TODO: implement paginated GET against BUGZILLA_ENDPOINT and return a list of dicts."""
    raise NotImplementedError("STEP 2 — implement acquisition")


def inspect(df) -> None:
    """TODO: print row count, column names, date range, severity distribution,
    and missingness for cf_last_resolved."""
    raise NotImplementedError("STEP 3/4 — implement inspection")


def main() -> int:
    bugs = fetch_bugs()
    # import pandas as pd
    # df = pd.DataFrame(bugs)
    # inspect(df)
    # RAW_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    # df.to_csv(RAW_OUTPUT, index=False)
    # print(f"Wrote {len(df):,} rows to {RAW_OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
