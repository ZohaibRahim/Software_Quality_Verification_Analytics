"""Load the EXISTING public Firefox CSV into the SQL Server staging table.

From repository root, after running SQL 00 and 01:
    python -m pip install pyodbc
    python sqlserver/import_csv.py --server localhost\\SQLEXPRESS

Uses Windows integrated authentication and Microsoft ODBC Driver 18.
No Bugzilla API call; no data refresh; preserves the original 3,000-row snapshot.
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

HEADERS = [
    "id", "product", "component", "status", "resolution", "severity",
    "priority", "creation_time", "cf_last_resolved",
    "target_milestone", "version", "summary",
]


def timestamp_utc(value: str) -> datetime | None:
    if not value or not value.strip():
        return None
    parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"Timezone missing from CSV timestamp: {value!r}")
    return parsed.astimezone(timezone.utc).replace(tzinfo=None)


def nullable(value: str | None) -> str | None:
    return value if value is not None and value != "" else None


def load_rows(path: Path) -> list[tuple]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != HEADERS:
            raise ValueError(f"Unexpected CSV header. Expected {HEADERS}, got {reader.fieldnames}")
        rows = []
        ids = set()
        for line_number, record in enumerate(reader, 2):
            if not record["id"]:
                raise ValueError(f"Missing Bugzilla ID at CSV line {line_number}")
            bug_id = int(record["id"])
            if bug_id in ids:
                raise ValueError(f"Duplicate ID in CSV: {bug_id}")
            ids.add(bug_id)
            rows.append((
                bug_id, nullable(record["product"]), nullable(record["component"]),
                nullable(record["status"]), nullable(record["resolution"]),
                nullable(record["severity"]), nullable(record["priority"]),
                timestamp_utc(record["creation_time"]),
                timestamp_utc(record["cf_last_resolved"]),
                nullable(record["target_milestone"]), nullable(record["version"]),
                nullable(record["summary"]),
            ))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", default=r"localhost\SQLEXPRESS", help=r"SQL Server name, e.g. localhost or localhost\SQLEXPRESS")
    parser.add_argument("--database", default="SQVA_SQLServer")
    parser.add_argument("--driver", default="ODBC Driver 18 for SQL Server")
    parser.add_argument("--csv", type=Path, default=Path("data/raw/firefox_bugs.csv"))
    args = parser.parse_args()

    if not args.csv.is_file():
        print(f"CSV not found: {args.csv.resolve()}\nRun from the GitHub repo root or supply --csv.", file=sys.stderr)
        return 1
    rows = load_rows(args.csv)
    print(f"Parsed {len(rows)} CSV rows from {args.csv.resolve()}")

    try:
        import pyodbc
    except ImportError:
        print("Missing pyodbc. Run: python -m pip install pyodbc", file=sys.stderr)
        return 1

    driver = f"{{{args.driver}}}"
    connection_string = (
        f"DRIVER={driver};SERVER={args.server};DATABASE={args.database};"
        "Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;"
        "Connection Timeout=15;"
    )
    # TrustServerCertificate=yes is for LOCAL development only.
    try:
        with pyodbc.connect(connection_string, autocommit=False) as con:
            cursor = con.cursor()
            cursor.execute("SELECT DB_NAME()")
            connected_db = cursor.fetchone()[0]
            if connected_db != args.database:
                raise RuntimeError(f"Connected to wrong database: {connected_db}")
            cursor.execute("DELETE FROM dbo.stg_bugs")
            sql = """INSERT INTO dbo.stg_bugs (
                bug_id, product, component, status, resolution, severity,
                priority, creation_time, last_resolved_time, target_milestone,
                version, summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            cursor.fast_executemany = True
            cursor.executemany(sql, rows)
            cursor.execute("SELECT COUNT(*) FROM dbo.stg_bugs")
            loaded = cursor.fetchone()[0]
            if loaded != len(rows):
                raise RuntimeError(f"Row count mismatch: CSV={len(rows)} staged={loaded}")
            con.commit()
            print(f"SUCCESS: loaded {loaded} records to {connected_db}.dbo.stg_bugs")
    except Exception as ex:
        print(f"Import failed (transaction rolled back): {ex}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
