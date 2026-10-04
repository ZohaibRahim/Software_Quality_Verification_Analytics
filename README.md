# Software Quality Verification Analytics

End-to-end defect analytics project built with **PostgreSQL, R, and Power BI**, using public Mozilla Firefox Bugzilla data as a proxy for internal Quality Verification telemetry.

> Status: **MVP complete.** See `PROGRESS.md` for the full checklist and measured results.

---

## Overview

Software Quality Verification Analytics models software defects into a dimensional reporting structure, validates analytical quality, measures defect-resolution performance, tests whether defect severity is associated with resolution time, and investigates changes in quality metrics through an interactive Power BI dashboard.

## Business Problem

Quality Verification teams need to answer questions such as:

- How many defects are being discovered, and is the volume rising?
- Which components produce the most defects?
- What proportion are high severity?
- How long do defects take to resolve, and does severity influence resolution time?
- Why did a key quality metric suddenly move?
- Can decision-makers trust the reported metrics?

## Architecture

```text
Mozilla Bugzilla REST API
          |
          v
      Raw CSV
          |
          v
     PostgreSQL (staging)
          |
          v
Cleaning / Transformation / Quarantine
          |
          v
     Star Schema (fact_bug + dims)
       /      \
      v        v
      R      Power BI
      |         |
      v         v
Hypothesis   Dashboard
Testing      + KPIs
       \       /
        v     v
    Findings + Root-Cause Analysis
```

## Dataset

- **Source:** Mozilla Bugzilla REST API (public).
- **Target population:** ~2,000–3,000 Firefox defects resolved as FIXED since 2024-01-01.
- **No sensitive fields collected** (no emails, user IDs, CC lists).

## Data Pipeline

| Stage | Tool | Artifact |
|-------|------|----------|
| Acquire | Python | `scripts/fetch_bugzilla_data.py` → `data/raw/firefox_bugs.csv` |
| Stage | SQL | `sql/01_create_staging.sql` |
| Clean | SQL | `sql/02_clean_transform.sql` |
| Model | SQL | `sql/03_create_star_schema.sql`, `sql/04_load_star_schema.sql` |
| Validate | SQL | `sql/05_qa_checks.sql` |
| Analyze | SQL / R | `sql/06_analysis_queries.sql`, `r/hypothesis_test.R` |
| Visualize | Power BI | `powerbi/quality_verification_dashboard.pbix` |

## Data Model

```text
               dim_component
                    |
dim_severity ---- fact_bug ---- dim_priority
                    |
                 dim_date
```

## Quality Metrics (headline)

- **Total Defects**
- **Median Resolution Days**
- **High-Severity Defects**
- **High-Severity %**

See `docs/methodology.md` for formal definitions once populated.

## Data Quality & Validation

Seven QA checks are implemented in `sql/05_qa_checks.sql` (unique IDs, non-negative durations, dimension integrity, severity whitelist, timestamp integrity, row reconciliation, dashboard reconciliation). See `PROGRESS.md` for status.

## Statistical Analysis

Wilcoxon rank-sum test comparing resolution-time distributions of **high-severity (S1+S2)** vs **lower-severity (S3+S4)** defects. Observational — results describe association, not causation.

**Result (2026-10-03 snapshot):** High (n=139) median 8.86 d vs Lower (n=1,034) median 13.61 d; **W = 58,544, p = 0.00038** — significant at α = 0.05. Direction is opposite of the naive guess (severe = complex = slow), consistent with triage prioritization. Full write-up in `docs/methodology.md`. Diagnostic plots in `images/hist_resolution_by_severity.png` and `images/box_resolution_by_severity.png`.

## Power BI Dashboard

One page: 4 KPI cards + 4 analytical visuals (defect arrival trend, severity mix, resolution by component Top-10-by-volume, resolution by severity) + 4 slicers (Date, Component, Severity, Priority). File: `powerbi/quality_verification_dashboard.pbix`. Screenshot: `images/dashboard.png`.

Six DAX measures: `Total Defects`, `Median Resolution Days`, `Average Resolution Days`, `P75 Resolution Days`, `High Severity Defects`, `High Severity %`. All four headline KPIs match the equivalent SQL (QA 7).

## Root-Cause Investigation

Monthly median resolution time jumped from **8.47 days in April 2024 to 14.39 in May 2024 (+69.9%)** then returned to 8.16 in June. Decomposition ruled out severity-mix (moved the wrong direction) and component-mix (shifts too small to explain). The surviving pattern is a **cross-component time-based slowdown** — multiple top components had their per-component median double or triple in May simultaneously. Consistent with a time-bound capacity effect (holiday / release / staffing); flagged as hypothesis, not causal conclusion. Full write-up: `docs/root_cause_analysis.md`.

## Key Findings

_Based on the 3,000-row Firefox FIXED-defects snapshot (2024-01-01 → 2024-10-30)._

- **Dataset survived QA cleanly:** 3,000 raw records in, 3,000 valid analytical records out, 0 quarantined, all 7 QA rules passing. Dashboard metrics reconcile against SQL.
- **Headline metrics:** 3,000 defects · median resolution 9.56 days · 139 high-severity (4.63%) · 44 components · 279 active days.
- **Severity is associated with resolution time (Wilcoxon rank-sum, p = 0.00038):** high-severity defects (S1+S2, n=139) resolve in a median of 8.86 days vs 13.61 days for lower-severity (S3+S4, n=1,034). The direction is **opposite** of the naive expectation that severe = complex = slow — consistent with triage prioritization accelerating high-severity work. Observational finding; no causal claim.
- **Severity caveat:** S1 is effectively absent in the dataset (1/3,000). The "High" group is driven ~99% by S2.
- **Distribution shape:** both groups are heavily right-skewed. Mean ≫ median in both (High 32 vs 9; Lower 71 vs 14). Median is the honest headline metric.

## Limitations

- Mozilla Firefox is a **public proxy**, not representative of any specific organization's processes.
- `resolution_time` is wall-clock, not active engineering time.
- Analysis is **observational**; associations ≠ causation.
- Some Bugzilla records contain missing or unusual values; handling is documented transparently.

## Repository Structure

```text
software-quality-verification-analytics/
├── README.md
├── PROGRESS.md
├── .gitignore
├── requirements.txt
├── config/
├── data/
│   ├── raw/
│   └── processed/
├── scripts/
│   └── fetch_bugzilla_data.py
├── sql/
│   ├── 01_create_staging.sql
│   ├── 02_clean_transform.sql
│   ├── 03_create_star_schema.sql
│   ├── 04_load_star_schema.sql
│   ├── 05_qa_checks.sql
│   └── 06_analysis_queries.sql
├── r/
│   └── hypothesis_test.R
├── powerbi/
│   └── quality_verification_dashboard.pbix
├── docs/
│   ├── dashboard_user_guide.md
│   ├── root_cause_analysis.md
│   ├── methodology.md
│   └── resume_bullets.md
└── images/
    └── dashboard.png
```

## How to Run

1. `pip install -r requirements.txt`
2. `python scripts/fetch_bugzilla_data.py` → produces `data/raw/firefox_bugs.csv`
3. Load into PostgreSQL and execute `sql/01_` through `sql/06_` in order.
4. Open `r/hypothesis_test.R` and run against the processed dataset.
5. Open `powerbi/quality_verification_dashboard.pbix` and refresh.

## Technologies

PostgreSQL · SQL · R · Power BI · DAX · Python · REST API · Git/GitHub · Dimensional Modelling · Statistical Hypothesis Testing · Data Quality Validation · Root-Cause Analysis
