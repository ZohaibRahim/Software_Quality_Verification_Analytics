# Dashboard User Guide — Software Quality Verification Overview

> **Status:** skeleton. Populate concrete numbers and screenshots after the pipeline runs end-to-end.

## Purpose

The Software Quality Verification Overview dashboard summarizes defect-arrival volume, resolution-time performance, and severity mix for Firefox defects, to help QA stakeholders answer:

- Is defect volume rising?
- Which components are slowest to resolve?
- Are high-severity defects resolved faster than lower-severity defects?
- Has an important quality metric shifted recently, and if so, what changed?

## Data Source

Mozilla Bugzilla REST API → PostgreSQL star schema. Only Firefox defects resolved as FIXED since 2024-01-01 are included.

## Data Refresh

Manual. Re-run `scripts/fetch_bugzilla_data.py`, reload SQL (01→06), and refresh the Power BI dataset.

## Dashboard KPIs

1. **Total Defects**
2. **Median Resolution Days**
3. **High-Severity Defects**
4. **High-Severity %**

See `docs/methodology.md` for definitions.

## Metric Definitions

| Metric | Definition |
|---|---|
| Total Defects | Count of valid FIXED Firefox defects after QA filtering. |
| Median Resolution Days | Median of `resolution_days` across the analytical population. |
| High-Severity Defects | Count where severity ∈ {S1, S2}. |
| High-Severity % | High-Severity Defects / Total Defects. |

## Available Filters

- Date
- Component
- Severity
- Priority

Filters apply to all visuals on the page.

## How to Interpret the Dashboard

- **Defect Arrival Trend** — monthly defect counts. Watch for sustained changes rather than single-month blips.
- **Severity Mix** — S1–S4 distribution. Shifts here feed into both the headline metric and the Wilcoxon result.
- **Resolution by Component** — top 10 by volume. Low-volume components may look extreme and should be interpreted alongside count.
- **Resolution by Severity** — pairs with the R hypothesis test.

## Data Quality Checks

Seven QA rules — see `sql/05_qa_checks.sql` and `docs/methodology.md`.

## Known Limitations

- Public proxy data; not representative of any specific organization.
- Resolution time is wall-clock, not active engineering effort.
- Associations are observational.
- Low-volume components can mislead on resolution averages — read with count in view.
