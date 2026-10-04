# Dashboard User Guide — Software Quality Verification Overview

One page. Written for a stakeholder opening the dashboard for the first time.

## Purpose

Summarizes defect-arrival volume, resolution-time performance, and severity mix for Firefox defects, to help QA stakeholders answer:

- Is defect volume rising?
- Which components are slowest to resolve?
- Are high-severity defects resolved faster than lower-severity defects?
- Has an important quality metric shifted recently, and if so, what changed?

## Data Source

Mozilla Bugzilla REST API → PostgreSQL (`qa_project` on `localhost:5433`) → Power BI (Import mode). Only Firefox defects resolved as FIXED since 2024-01-01 are included. Snapshot captured 2026-10-03 covers 2024-01-01 → 2024-10-30 (3,000 defects).

## Data Refresh

Manual. Re-run `scripts/fetch_bugzilla_data.py`, re-run `sql/01` → `sql/05`, then **Power BI → Home → Refresh**.

## Dashboard KPIs (observed values on this snapshot)

| KPI | Value | Definition |
|---|---|---|
| Total Defects | 3,000 | Count of valid FIXED Firefox defects after QA filtering. |
| Median Resolution Days | 9.56 | Median of `resolution_days` across the analytical population. |
| High-Severity Defects | 139 | Count where severity ∈ {S1, S2}. |
| High-Severity % | 4.63% | High-Severity Defects / Total Defects. |

## Available Filters

- **Date** — range slicer over `dim_date.full_date`.
- **Component** — dropdown over 44 Firefox components.
- **Severity** — tiles for S1 / S2 / S3 / S4 / `--` / `N/A`.
- **Priority** — dropdown for P1–P5 and `--`.

All filters apply to all visuals.

## How to Interpret

- **Defect Arrival Trend** — monthly counts (`year_month` on X-axis). Watch for sustained changes rather than single-month blips.
- **Defects by Severity** — raw S1–S4 counts plus `--` and `N/A` (missing-severity). The missing-severity codes are ~61% of defects — call this out when comparing severity shares.
- **Median Resolution Days by Component (Top 10 by volume)** — filtered to the 10 components with the most defects. Tooltip shows the count. Low-volume components are deliberately hidden because a single outlier bug can inflate their median.
- **Median Resolution Days by Severity** — pairs with the statistical finding. S1+S2 bars should be noticeably shorter than S3+S4 (confirmed: median 8.86 vs 13.61 days, Wilcoxon p = 0.00038).

## Data Quality Checks

Seven QA rules implemented in `sql/05_qa_checks.sql`:

1. Unique bug IDs in fact.
2. No negative `resolution_days`.
3. All FK references resolve.
4. Severity ∈ {S1, S2, S3, S4, --, N/A}.
5. `last_resolved_time ≥ creation_time`.
6. Raw rows = valid rows + quarantined rows (3,000 = 3,000 + 0).
7. Power BI headline metrics match SQL outputs (verified: Total, Median, High-Sev, High-Sev %).

## Known Limitations

- Mozilla Firefox is a **public proxy**; does not represent any specific organization's QA process.
- `resolution_days` is wall-clock, not active engineering effort — includes triage/dependency/release waits.
- Associations are **observational**, not causal.
- Low-volume components can look extreme; always read volume alongside median.
- **S1 is effectively absent in the 2024 Firefox FIXED population** (1/3,000). The "High-severity" group is driven ~99% by S2.
- `--` and `N/A` severities (~61% of defects) are kept in the dashboard counts but excluded from the Wilcoxon test and the High-Severity % metric.

## Exporting

To ship this guide as a PDF, open the markdown in any viewer that prints to PDF (VS Code with the "Markdown PDF" extension, pandoc, or a browser preview + print → Save as PDF). The source stays markdown so it's diffable in git.
