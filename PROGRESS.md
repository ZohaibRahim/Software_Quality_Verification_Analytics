# Project Progress — Software Quality Verification Analytics

**Purpose:** Resumable log. Any session can pick up by reading this file plus the master brief in-conversation.

**Last updated:** 2026-10-03

---

## Current state

- **Current step:** STEP 1 complete — repo scaffolding done.
- **Next step:** STEP 2 — implement `scripts/fetch_bugzilla_data.py` to pull a small sample from the Bugzilla REST API and inspect the real schema.
- **Blockers / open questions:** None.

---

## Implementation checklist (from master brief §41)

Tick as each step completes. Keep this honest — do not tick ahead of real work.

- [x] **STEP 1** Initialize repository and project structure.
- [ ] **STEP 2** Create Bugzilla data-acquisition script.
- [ ] **STEP 3** Download and inspect actual dataset (small sample first).
- [ ] **STEP 4** Report real columns, values, missingness and severity distribution.
- [ ] **STEP 5** Create PostgreSQL staging table.
- [ ] **STEP 6** Import raw data.
- [ ] **STEP 7** Create cleaning/transformation SQL.
- [ ] **STEP 8** Create quarantine/data-quality logic.
- [ ] **STEP 9** Build star schema.
- [ ] **STEP 10** Run QA checks and record actual results.
- [ ] **STEP 11** Generate processed analytical dataset for R.
- [ ] **STEP 12** Perform exploratory statistics in R.
- [ ] **STEP 13** Perform Wilcoxon hypothesis test.
- [ ] **STEP 14** Interpret results.
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

---

## Actual measured results

**Do not fill in anything here until the pipeline has actually run.** No fabricated numbers.

### Dataset counts
- Raw Bugzilla records retrieved: _TBD_
- Valid analytical defects: _TBD_
- Quarantined records: _TBD_

### QA results
- Duplicate analytical bug IDs: _TBD_
- Negative resolution durations: _TBD_
- Broken dimensional relationships: _TBD_
- QA rules implemented: _TBD_

### Statistical test
- High-severity n: _TBD_
- Lower-severity n: _TBD_
- High-severity median resolution days: _TBD_
- Lower-severity median resolution days: _TBD_
- Wilcoxon test statistic: _TBD_
- p-value: _TBD_
- Conclusion at α = 0.05: _TBD_

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
