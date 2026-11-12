-- SQL Server adaptation of the seven original quality checks.
-- QA1-5: anomaly counts must be zero. QA6: reconciliation must PASS.
-- QA7: compare the output with the ORIGINAL Power BI cards, manually.
USE SQVA_SQLServer;
GO
SELECT 'QA1 Duplicate fact bug IDs' AS qa_check, COUNT(*) AS anomalies
FROM (SELECT bug_id FROM dbo.fact_bug GROUP BY bug_id HAVING COUNT(*) > 1) x
UNION ALL
SELECT 'QA2 Negative duration', COUNT(*) FROM dbo.fact_bug WHERE resolution_days < 0
UNION ALL
SELECT 'QA3 Orphan dimension keys', COUNT(*) FROM (
    SELECT f.bug_id FROM dbo.fact_bug f LEFT JOIN dbo.dim_component d ON d.component_key=f.component_key WHERE d.component_key IS NULL
    UNION ALL SELECT f.bug_id FROM dbo.fact_bug f LEFT JOIN dbo.dim_severity d ON d.severity_key=f.severity_key WHERE d.severity_key IS NULL
    UNION ALL SELECT f.bug_id FROM dbo.fact_bug f LEFT JOIN dbo.dim_priority d ON d.priority_key=f.priority_key WHERE d.priority_key IS NULL
    UNION ALL SELECT f.bug_id FROM dbo.fact_bug f LEFT JOIN dbo.dim_date d ON d.date_key=f.created_date_key WHERE d.date_key IS NULL
) x
UNION ALL
SELECT 'QA4 Unknown severity code', COUNT(*) FROM dbo.dim_severity WHERE severity NOT IN (N'S1',N'S2',N'S3',N'S4',N'--',N'N/A')
UNION ALL
SELECT 'QA5 Reversed staging timestamps', COUNT(*) FROM dbo.stg_bugs WHERE last_resolved_time < creation_time;
GO
;WITH counts AS (
    SELECT
       (SELECT COUNT(*) FROM dbo.stg_bugs) AS raw_rows,
       (SELECT COUNT(*) FROM dbo.fact_bug) AS valid_rows,
       (SELECT COUNT(DISTINCT bug_id) FROM dbo.qa_quarantine) AS quarantined_rows
)
SELECT 'QA6 Row reconciliation' AS qa_check, raw_rows, valid_rows, quarantined_rows,
       valid_rows + quarantined_rows AS reconciled_total,
       CASE WHEN raw_rows = valid_rows + quarantined_rows THEN 'PASS' ELSE 'FAIL' END AS status
FROM counts;
GO
-- SQL Server PERCENTILE_CONT is a WINDOW function, unlike the PostgreSQL aggregate.
;WITH metrics AS (
    SELECT f.resolution_days, s.severity_group,
           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.resolution_days) OVER () AS median_days,
           PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY f.resolution_days) OVER () AS p75_days
    FROM dbo.fact_bug f
    JOIN dbo.dim_severity s ON s.severity_key = f.severity_key
)
SELECT 'QA7 Compare with Power BI' AS qa_check,
       COUNT(*) AS total_defects,
       CAST(MAX(median_days) AS DECIMAL(18,4)) AS median_resolution_days,
       CAST(AVG(resolution_days) AS DECIMAL(18,4)) AS average_resolution_days,
       CAST(MAX(p75_days) AS DECIMAL(18,4)) AS p75_resolution_days,
       SUM(CASE WHEN severity_group = N'High' THEN 1 ELSE 0 END) AS high_severity_defects,
       SUM(CASE WHEN severity_group = N'Lower' THEN 1 ELSE 0 END) AS lower_severity_defects,
       CAST(100.0 * SUM(CASE WHEN severity_group=N'High' THEN 1 ELSE 0 END)
            / NULLIF(SUM(CASE WHEN severity_group IN (N'High',N'Lower') THEN 1 ELSE 0 END),0)
            AS DECIMAL(8,2)) AS high_severity_percent
FROM metrics;
GO
-- Original 3,000-row snapshot reference from the repository methodology:
-- total_defects=3000; high_severity_defects=139; lower_severity_defects=1034;
-- high_severity_percent ~= 11.85%. These are reference values, not claimed SQL Server results.
-- Quarantined rows expected=0 for original snapshot.
