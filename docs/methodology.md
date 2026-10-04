# Methodology & Metric Definitions

Companion document to `README.md`. Every metric shown in Power BI must match
this file, `sql/06_analysis_queries.sql`, and `r/hypothesis_test.R`.

> Status: definitions are stable; actual numbers populate `PROGRESS.md` once
> the pipeline runs.

---

## Data source

- **System:** Mozilla Bugzilla REST API (`https://bugzilla.mozilla.org/rest/bug`).
- **Scope:** `product = Firefox`, `resolution = FIXED`, `creation_time >= 2024-01-01`.
- **Access:** public; no credentials.
- **Sensitive fields excluded by design:** reporter email, assignee email, CC lists, comment authors, user IDs.

## Timestamp conventions

| Field | Definition |
|---|---|
| `creation_time` | Defect creation timestamp. |
| `cf_last_resolved` | Last time the defect was moved to a resolved state. Preferred final-resolution timestamp. |
| `resolution_hours` | `(cf_last_resolved − creation_time)` in hours. |
| `resolution_days` | `resolution_hours / 24`. |

> **Why `cf_last_resolved` and not the latest update:** a defect may be edited after resolution (status comments, tag edits). Using `cf_last_resolved` keeps the metric tied to the resolution event.

## Severity grouping

Original severity values are preserved. A derived `severity_group` is added:

| severity | severity_group |
|---|---|
| S1, S2 | High |
| S3, S4 | Lower |
| `--`, `N/A` | Unclassified |
| anything else | → quarantined with reason `UNKNOWN_SEVERITY` |

**Observed distribution (3,000-row sample on 2026-10-03):**
S1 = 1, S2 = 138, S3 = 690, S4 = 344, `--` = 1,298, `N/A` = 529.

**S1 is effectively absent in Firefox FIXED bugs** — the "High-severity" group in the Wilcoxon test is driven ~99% by S2. This is called out in the statistical write-up and in `root_cause_analysis.md`.

Unclassified rows are **kept** in `fact_bug` so dashboard totals and arrival trends reflect the full population. They are **excluded** from the Wilcoxon test and from the High-Severity % metric (which uses `severity_group = 'High'` only).

## Headline metrics

### Total Defects
Count of valid FIXED Firefox defects in `fact_bug` after data-quality filtering.

### Median Resolution Days
`PERCENTILE_CONT(0.5)` of `resolution_days` across `fact_bug`.

Chosen over the mean because defect-resolution times are typically right-skewed.

### High-Severity Defects
Count of `fact_bug` rows whose `severity_group = 'High'` (i.e. severity ∈ {S1, S2}).

### High-Severity %
`High-Severity Defects / Total Defects`.

## Supporting metrics

- Average Resolution Days (for comparison with the median only).
- 75th Percentile Resolution Days.
- Defects per Month (based on `creation_time`).
- Defects by Component.
- Median Resolution Days by Component.
- Defects by Severity (S1–S4).

## Data-quality rules

Implemented in `sql/02_clean_transform.sql` and verified by `sql/05_qa_checks.sql`:

1. Unique bug IDs in `fact_bug`.
2. No negative `resolution_days`.
3. Every fact row maps to valid `component`, `severity`, `priority`, and `date` dimensions.
4. Severity values restricted to the whitelist {S1, S2, S3, S4}.
5. `last_resolved_time ≥ creation_time` in staging.
6. Row reconciliation: `raw = valid + quarantined`.
7. Dashboard reconciliation: Power BI metrics match SQL outputs under equivalent filters.

## Statistical analysis

**Question:** Does the resolution-time distribution of High-severity defects differ from Lower-severity defects?

- H₀: distributions do not differ.
- H₁: distributions differ.
- Method: Wilcoxon rank-sum test (`wilcox.test` in R), two-sided.
- Significance level: α = 0.05.

Choice of test:

- Resolution times are typically skewed with heavy right tails → mean/variance assumptions are unsafe.
- The Wilcoxon test does not assume normality and is robust to outliers.

Interpretation rule: a significant p-value supports a difference in distributions. It does **not** establish causation. Severity is observational, not randomized.

### Observed result (2026-10-03)

- High (S1+S2) n = 139, median = 8.86 days.
- Lower (S3+S4) n = 1,034, median = 13.61 days.
- Wilcoxon W = 58,544, p = 0.00038.
- At α = 0.05 the difference is statistically significant.
- Direction: high-severity resolves FASTER than lower-severity — consistent with triage prioritization. Not causal.

## Known limitations

- Mozilla Firefox is a **public proxy**; results do not describe any specific private organization's QA process.
- `resolution_days` is wall-clock, not active engineering effort — it includes triage waits, dependency blocks, release scheduling, etc.
- All associations are observational — no causal claim is appropriate.
- Some Bugzilla records are missing or anomalous; they are quarantined with a documented reason, not silently dropped.
