-- 02_clean_transform.sql
-- Quarantine unfit rows, then expose a clean analytical view (v_bugs_clean).

DROP TABLE IF EXISTS qa_quarantine;
CREATE TABLE qa_quarantine (
    bug_id           INTEGER,
    rejection_reason TEXT NOT NULL,
    rejected_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO qa_quarantine (bug_id, rejection_reason)
SELECT bug_id, 'MISSING_CREATION_TIME'        FROM stg_bugs WHERE creation_time IS NULL
UNION ALL
SELECT bug_id, 'MISSING_RESOLUTION_TIME'      FROM stg_bugs WHERE last_resolved_time IS NULL
UNION ALL
SELECT bug_id, 'NEGATIVE_RESOLUTION_DURATION' FROM stg_bugs WHERE last_resolved_time < creation_time
UNION ALL
SELECT bug_id, 'UNKNOWN_SEVERITY'             FROM stg_bugs
    WHERE severity IS NULL OR severity NOT IN ('S1','S2','S3','S4','--','N/A')
UNION ALL
SELECT bug_id, 'NON_FIXED_RESOLUTION'         FROM stg_bugs WHERE resolution <> 'FIXED';

DROP VIEW IF EXISTS v_bugs_clean;
CREATE VIEW v_bugs_clean AS
SELECT
    s.bug_id, s.product, s.component, s.status, s.resolution, s.severity,
    COALESCE(s.priority, '--')         AS priority,
    s.creation_time, s.last_resolved_time, s.target_milestone, s.version,
    EXTRACT(EPOCH FROM (s.last_resolved_time - s.creation_time)) / 3600.0  AS resolution_hours,
    EXTRACT(EPOCH FROM (s.last_resolved_time - s.creation_time)) / 86400.0 AS resolution_days,
    CASE
        WHEN s.severity IN ('S1','S2') THEN 'High'
        WHEN s.severity IN ('S3','S4') THEN 'Lower'
        ELSE 'Unclassified'
    END AS severity_group,
    DATE(s.creation_time)                      AS created_date,
    EXTRACT(YEAR    FROM s.creation_time)::INT AS created_year,
    EXTRACT(QUARTER FROM s.creation_time)::INT AS created_quarter,
    EXTRACT(MONTH   FROM s.creation_time)::INT AS created_month,
    TRIM(TO_CHAR(s.creation_time, 'Month'))    AS created_month_name
FROM stg_bugs s
WHERE s.bug_id NOT IN (SELECT bug_id FROM qa_quarantine);
