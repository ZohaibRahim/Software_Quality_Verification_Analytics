# Project Progress — Software Quality Verification Analytics

**Purpose:** Resumable log. Any session can pick up by reading this file plus the master brief in-conversation.

**Last updated:** 2026-10-03

---

## Current state

- **Current step:** STEPS 12–14 complete. Wilcoxon ran clean; result is significant and in the opposite direction of the naive guess (high-severity resolves FASTER).
- **Next step:** STEP 15 — connect Power BI Desktop to the `qa_project` database. User installs the Npgsql connector and sets up the connection; I'll give exact clicks.
- **Blockers / open questions:** None.

---

## Implementation checklist (from master brief §41)

Tick as each step completes. Keep this honest — do not tick ahead of real work.

- [x] **STEP 1** Initialize repository and project structure.
- [x] **STEP 2** Create Bugzilla data-acquisition script.
- [x] **STEP 3** Download and inspect actual dataset — 3,000-row sample saved to `data/raw/firefox_bugs.csv`.
- [x] **STEP 4** Report real columns, values, missingness and severity distribution — see Decisions log and `docs/methodology.md`.
- [x] **STEP 5** Create PostgreSQL staging table (`stg_bugs`, 12 cols).
- [x] **STEP 6** Import raw data (3,000 rows loaded via `\copy`).
- [x] **STEP 7** Create cleaning/transformation SQL (`v_bugs_clean`).
- [x] **STEP 8** Create quarantine/data-quality logic (`qa_quarantine`, 5 reason codes).
- [x] **STEP 9** Build star schema (`fact_bug` 3000 + 4 dims).
- [x] **STEP 10** Run QA checks — all 7 passed; metrics: 3000 defects, median 9.56 days, 139 high-severity.
- [x] **STEP 11** Generate processed analytical dataset for R (`data/processed/analysis_dataset.csv`, 3000 rows).
- [x] **STEP 12** Perform exploratory statistics in R (summary tibble + histogram + log-boxplot).
- [x] **STEP 13** Perform Wilcoxon hypothesis test (W=58544, p=0.00038).
- [x] **STEP 14** Interpret results — see Statistical test block below and README Key Findings.
- [ ] **STEP 15** Connect Power BI to PostgreSQL.
- [ ] **STEP 16** Create data model and DAX measures.
- [ ] **STEP 17** Build dashboard.
- [ ] **STEP 18** Reconcile dashboard values against SQL.
- [ ] **STEP 19** Identify one meaningful metric movement.
- [ ] **STEP 20** Perform root-cause investigation.
- [ ] **STEP 21** Write user guide and methodology.
- [ ] **STEP 22** Complete README.
- [ ] **STEP 23** Generate final evidence/results for resume bullets.

---

## MVP success criteria (from master brief §48)

- [ ] Bugzilla data successfully retrieved
- [ ] Approximately 2,000–3,000 valid defects available
- [ ] Raw dataset preserved
- [ ] PostgreSQL staging table created
- [ ] Cleaning logic implemented
- [ ] Invalid records transparently identified
- [ ] Resolution time calculated
- [ ] Severity groups created
- [ ] Star schema working
- [ ] QA checks passing
- [ ] Row counts reconciled
- [ ] R analysis reproducible
- [ ] Hypothesis test completed
- [ ] Statistical finding interpreted correctly
- [ ] Power BI model working
- [ ] Four headline metrics implemented
- [ ] Four useful visuals created
- [ ] Filters working
- [ ] Power BI numbers reconciled against SQL
- [ ] Root-cause investigation completed
- [ ] User guide completed
- [ ] README completed
- [ ] Dashboard screenshot captured
- [ ] Resume bullets based only on actual results

---

## Decisions log

Append each non-trivial decision with date + rationale.

- **2026-10-03** — Scaffolding uses the structure in master brief §7 verbatim (no deviations yet). Added `PROGRESS.md` as a resumable project log (not in the original brief but requested by the user).
- **2026-10-03** — Data snapshots (`data/raw/*.csv`, `data/processed/*.csv`) are **not** ignored by git initially so the reviewed sample stays reproducible. If the raw CSV grows past a few MB, uncomment the lines in `.gitignore`.
- **2026-10-03** — Environment: Python 3.12.7, Git 2.51.2, R + RStudio and Power BI Desktop installed. Fresh `.venv` created in-project with `requests`, `pandas`, `python-dateutil`. GitHub remote: `https://github.com/ZohaibRahim/Software_Quality_Verification_Analytics`. **PostgreSQL 16 pending install** (user is handling).
- **2026-10-03** — 50-row Bugzilla sample inspected (`data/raw/firefox_bugs.csv`). All 12 requested fields returned. Severity values observed: `S2`, `S3`, `S4`, plus `--` and `N/A` (missing-severity, 52% of the sample). `S1` absent in this tiny slice. 50 rows span only 2024-01-01 → 2024-01-09, so a full 2024-01-01→today pull would be very large; a cap is needed. `cf_last_resolved` missing 0/50 in this slice. Priority `--` is common; handled by `COALESCE('Unspecified')`.
- **2026-10-03** — Severity cleaning decision: map `--` and `N/A` to `severity_group = 'Unclassified'` and KEEP them in `fact_bug` (so dashboard counts/trends aren't biased), but EXCLUDE them from the Wilcoxon test and from the High-Severity % metric. Only genuinely unexpected codes (anything outside `{S1,S2,S3,S4,--,N/A}`) would be quarantined with reason `UNKNOWN_SEVERITY`. See `docs/methodology.md`.
- **2026-10-03** — 3,000-row sample locked as the project dataset. Rationale: brief §3 says "do not increase dataset size unnecessarily", and we have 1,173 clean S1–S4 defects (139 High + 1,034 Lower) — comfortable for Wilcoxon. Date range of this snapshot: 2024-01-01 → 2024-10-30. **Caveat to call out in the write-up:** S1 count is 1/3,000, so the "High" group is effectively S2 only.
- **2026-10-03** — Local Postgres instance: 16.15 server on `localhost:5433`, user `postgres`, database `qa_project` (dedicated for this project). psql client bundled with Postgres 18.1. psql binary at `C:\Program Files\PostgreSQL\16\bin\psql.exe` (not on PATH; invoked by full path). Password stays with user, never committed.
- **2026-10-03** — SQL pipeline ran clean: 0 rows quarantined out of 3,000; all 7 QA checks pass; dim counts {component: 44, severity: 6, priority: 6, date: 279}.

---

## Actual measured results

**Do not fill in anything here until the pipeline has actually run.** No fabricated numbers.

### Dataset counts
- Raw Bugzilla records retrieved: 3,000
- Valid analytical defects: 3,000
- Quarantined records: 0

### QA results
- Duplicate analytical bug IDs: 0
- Negative resolution durations: 0
- Broken dimensional relationships: 0
- QA rules implemented: 7

### Headline metrics (as of SQL pipeline run on 2026-10-03)
- Total defects: 3,000
- Median resolution days: 9.56
- Average resolution days: _see 06_analysis_queries.sql_
- High-severity defects (S1+S2): 139
- High-severity %: 4.63%
- Unique components: 44
- Dates with activity: 279 (2024-01-01 → 2024-10-30)

### Statistical test
- High-severity n: 139 (S1=1, S2=138)
- Lower-severity n: 1,034 (S3=690, S4=344)
- High-severity median resolution days: 8.86
- Lower-severity median resolution days: 13.61
- High-severity mean: 32.3 days (sd 77.8) — right-skewed
- Lower-severity mean: 70.8 days (sd 153) — right-skewed
- Wilcoxon test statistic W: 58,544
- p-value: 0.00038
- Conclusion at α = 0.05: **statistically significant difference**; high-severity defects resolve FASTER (opposite of naive expectation, consistent with triage prioritization). Observational — not causal.

### Root-cause investigation
- Metric movement observed: _TBD_
- Contributing factors identified: _TBD_

---

## How to resume a session

1. Read this file top-to-bottom.
2. Read the master project brief (pinned in chat; or re-paste from source).
3. Look at the "Current state" block above — pick up at **Next step**.
4. Before any destructive action, run `git status` and stash/commit anything there.
5. Update this file at the end of each working session.
