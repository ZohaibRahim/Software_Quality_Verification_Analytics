-- T-SQL equivalent of sql/02_clean_transform.sql.
-- Preserve all FIVE original quarantine reason codes and clean-view fields.
USE SQVA_SQLServer;
GO
IF OBJECT_ID(N'dbo.v_bugs_clean', N'V') IS NOT NULL DROP VIEW dbo.v_bugs_clean;
IF OBJECT_ID(N'dbo.qa_quarantine', N'U') IS NOT NULL DROP TABLE dbo.qa_quarantine;
GO
CREATE TABLE dbo.qa_quarantine (
    bug_id INT NULL,
    rejection_reason NVARCHAR(50) NOT NULL,
    rejected_at DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO
INSERT INTO dbo.qa_quarantine(bug_id, rejection_reason)
SELECT bug_id, N'MISSING_CREATION_TIME' FROM dbo.stg_bugs WHERE creation_time IS NULL
UNION ALL
SELECT bug_id, N'MISSING_RESOLUTION_TIME' FROM dbo.stg_bugs WHERE last_resolved_time IS NULL
UNION ALL
SELECT bug_id, N'NEGATIVE_RESOLUTION_DURATION' FROM dbo.stg_bugs WHERE last_resolved_time < creation_time
UNION ALL
SELECT bug_id, N'UNKNOWN_SEVERITY' FROM dbo.stg_bugs WHERE severity IS NULL OR severity NOT IN (N'S1',N'S2',N'S3',N'S4',N'--',N'N/A')
UNION ALL
SELECT bug_id, N'NON_FIXED_RESOLUTION' FROM dbo.stg_bugs WHERE resolution <> N'FIXED';
GO
CREATE VIEW dbo.v_bugs_clean AS
SELECT
    s.bug_id, s.product, s.component, s.status, s.resolution, s.severity,
    COALESCE(s.priority, N'--') AS priority,
    s.creation_time, s.last_resolved_time, s.target_milestone, s.version,
    DATEDIFF_BIG(SECOND, s.creation_time, s.last_resolved_time) / 3600.0 AS resolution_hours,
    DATEDIFF_BIG(SECOND, s.creation_time, s.last_resolved_time) / 86400.0 AS resolution_days,
    CASE WHEN s.severity IN (N'S1',N'S2') THEN N'High'
         WHEN s.severity IN (N'S3',N'S4') THEN N'Lower'
         ELSE N'Unclassified' END AS severity_group,
    CONVERT(DATE, s.creation_time) AS created_date,
    DATEPART(YEAR, s.creation_time) AS created_year,
    DATEPART(QUARTER, s.creation_time) AS created_quarter,
    DATEPART(MONTH, s.creation_time) AS created_month,
    DATENAME(MONTH, s.creation_time) AS created_month_name
FROM dbo.stg_bugs AS s
WHERE NOT EXISTS (
    SELECT 1 FROM dbo.qa_quarantine AS q WHERE q.bug_id = s.bug_id
);
GO
SELECT (SELECT COUNT(*) FROM dbo.stg_bugs) AS staged_rows,
       (SELECT COUNT(*) FROM dbo.qa_quarantine) AS quarantine_reasons,
       (SELECT COUNT(DISTINCT bug_id) FROM dbo.qa_quarantine) AS quarantined_bugs,
       (SELECT COUNT(*) FROM dbo.v_bugs_clean) AS clean_rows;
