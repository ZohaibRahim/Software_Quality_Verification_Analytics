-- =============================================================================
-- 05_qa_checks.sql
-- Purpose: Analytical data-quality validation. Each check returns 0 rows
--          when the rule passes.
-- Stage:   STEP 10 (master brief §14)
-- =============================================================================

-- QA 1: Unique bug IDs in fact_bug
SELECT bug_id, COUNT(*) AS n
FROM fact_bug
GROUP BY bug_id
HAVING COUNT(*) > 1;

-- QA 2: No negative resolution duration
SELECT bug_id, resolution_days
FROM fact_bug
WHERE resolution_days < 0;

-- QA 3: Dimensional integrity — every FK resolves
SELECT 'component' AS dim, f.bug_id FROM fact_bug f LEFT JOIN dim_component dc ON dc.component_key = f.component_key WHERE dc.component_key IS NULL
UNION ALL
SELECT 'severity',          f.bug_id FROM fact_bug f LEFT JOIN dim_severity  ds ON ds.severity_key  = f.severity_key  WHERE ds.severity_key  IS NULL
UNION ALL
SELECT 'priority',          f.bug_id FROM fact_bug f LEFT JOIN dim_priority  dp ON dp.priority_key  = f.priority_key  WHERE dp.priority_key  IS NULL
UNION ALL
SELECT 'date',              f.bug_id FROM fact_bug f LEFT JOIN dim_date      dd ON dd.date_key      = f.created_date_key WHERE dd.date_key   IS NULL;

-- QA 4: Severity whitelist
--     S1-S4 are the analytical categories.
--     '--' and 'N/A' are Mozilla's "unset" codes; mapped to Unclassified, not quarantined.
SELECT severity
FROM dim_severity
WHERE severity NOT IN ('S1','S2','S3','S4','--','N/A');

-- QA 5: Timestamp integrity in staging
SELECT bug_id, creation_time, last_resolved_time
FROM stg_bugs
WHERE last_resolved_time < creation_time;

-- QA 6: Row reconciliation
--     raw = valid + quarantined
SELECT
    (SELECT COUNT(*) FROM stg_bugs)       AS raw_rows,
    (SELECT COUNT(*) FROM fact_bug)       AS valid_rows,
    (SELECT COUNT(DISTINCT bug_id) FROM qa_quarantine) AS quarantined_rows,
    (SELECT COUNT(*) FROM fact_bug)
      + (SELECT COUNT(DISTINCT bug_id) FROM qa_quarantine) AS reconciled_total;

-- QA 7: Dashboard reconciliation metrics (run equivalents in Power BI)
SELECT
    COUNT(*)                                                           AS total_defects,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY resolution_days)       AS median_resolution_days,
    COUNT(*) FILTER (
        WHERE severity_key IN (SELECT severity_key FROM dim_severity WHERE severity_group = 'High')
    )                                                                  AS high_severity_defects
FROM fact_bug;
