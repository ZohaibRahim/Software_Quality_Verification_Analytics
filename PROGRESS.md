# Project Progress — Software Quality Verification Analytics

**Purpose:** Resumable log. Any session can pick up by reading this file plus the master brief in-conversation.

**Last updated:** 2026-10-03

---

## Current state

- **Current step:** ALL STEPS 1–23 COMPLETE + **STEP 24 (Monte Carlo simulation extension) COMPLETE**.
- **Next step:** Optional polish only.
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
- [x] **STEP 15** Connect Power BI to PostgreSQL (Import mode, 127.0.0.1:5433).
- [x] **STEP 16** Create data model and DAX measures (6 measures, star relationships verified).
- [x] **STEP 17** Build dashboard (1 page: 4 KPIs + 4 visuals + 4 slicers).
- [x] **STEP 18** Reconcile dashboard values against SQL — Total=3000, Median=9.56, HiSev=139, HiSev%=11.85% (classified-only denominator; was initially 4.63% using full-population denominator — fixed to match methodology).
- [x] **STEP 19** Identify one meaningful metric movement — Apr→May median +69.9% (8.47d → 14.39d).
- [x] **STEP 20** Perform root-cause investigation — cross-component time-based slowdown; written up in `docs/root_cause_analysis.md`.
- [x] **STEP 21** Write user guide and methodology — `docs/dashboard_user_guide.md`, `docs/methodology.md`.
- [x] **STEP 22** Complete README — all sections populated with real numbers.
- [x] **STEP 23** Generate final evidence/results for resume bullets — `docs/resume_bullets.md`.
- [x] **STEP 24** Monte Carlo backlog-forecast simulation (v1) — Poisson arrivals + bootstrap service.
- [x] **STEP 25** Simulation upgrade: staffing elasticity α, dispersion diagnostic, 5-seed convergence, walk-forward backtest — `scripts/monte_carlo_backtest.py`. Actual (231) within predicted 95% range [230, 293].

---

## MVP success criteria (from master brief §48)

- [x] Bugzilla data successfully retrieved
- [x] Approximately 2,000–3,000 valid defects available (3,000)
- [x] Raw dataset preserved (`data/raw/firefox_bugs.csv`)
- [x] PostgreSQL staging table created
- [x] Cleaning logic implemented
- [x] Invalid records transparently identified (0 quarantined; 5 reason codes defined)
- [x] Resolution time calculated
- [x] Severity groups created (High / Lower / Unclassified)
- [x] Star schema working (1 fact + 4 dims)
- [x] QA checks passing (7/7)
- [x] Row counts reconciled (3000 raw = 3000 valid + 0 quarantined)
- [x] R analysis reproducible (`r/hypothesis_test.R`)
- [x] Hypothesis test completed (Wilcoxon W=58544, p=0.00038)
- [x] Statistical finding interpreted correctly (association, not causation)
- [x] Power BI model working (Import mode, 1:many single-direction relationships, dim_date marked)
- [x] Four headline metrics implemented
- [x] Four useful visuals created
- [x] Filters working
- [x] Power BI numbers reconciled against SQL (all 4 match)
- [x] Root-cause investigation completed (`docs/root_cause_analysis.md`)
- [x] User guide completed (`docs/dashboard_user_guide.md`)
- [x] README completed
- [x] Dashboard screenshot captured (`images/dashboard.png`)
- [x] Resume bullets based only on actual results (`docs/resume_bullets.md`)

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
- High-severity %: **11.85%** (139 / 1,173 classified; denominator excludes `--`/`N/A` per methodology)
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

### Monte Carlo backlog forecast + backtest (5,000 trials × 5 seeds, 90-day horizon)
- Arrival rate: λ = 9.87 defects/day (from throughput).
- Service times: bootstrap from empirical `resolution_days` (3,000 obs).
- Seed convergence: baseline median range [252, 252] across 5 seeds — 5,000 trials sufficient.
- Daily-arrival dispersion var/mean = **4.58** — strongly overdispersed vs Poisson; results are a lower bound on real uncertainty.
- Staffing elasticity α ∈ {0.3, 0.6, 1.0}: +50% staff cuts median open-at-ship by **6% (α=0.3) to 19% (α=1.0)**.
- **Backtest:** train Jan–Jun 2024 → predict Jul–Sep 2024. Predicted median 260, 95% range [230, 293]. Actual = **231 — inside the predicted range** (error −12.8%).

### Root-cause investigation
- Metric movement observed: median resolution days rose from **8.47 → 14.39 (+69.9%)** between Apr 2024 and May 2024, then returned to 8.16 days in Jun 2024.
- Contributing factors identified: not primarily severity or component mix. Within-component medians rose simultaneously across most top components (Profile Backup ×2.2, Translations ×3.3, Messaging System ×2.0, Sidebar ×1.8, PDF Viewer ×4.1). Pattern consistent with a **time-based, cross-component capacity effect** (e.g. holiday/release/staffing). Hypotheses, not causal conclusions — the Bugzilla fields in scope cannot test them.

---

## How to resume a session

1. Read this file top-to-bottom.
2. Read the master project brief (pinned in chat; or re-paste from source).
3. Look at the "Current state" block above — pick up at **Next step**.
4. Before any destructive action, run `git status` and stash/commit anything there.
5. Update this file at the end of each working session.
