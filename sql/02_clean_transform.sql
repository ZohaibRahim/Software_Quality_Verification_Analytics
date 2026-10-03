-- =============================================================================
-- 02_clean_transform.sql
-- Purpose: Clean staging data and produce the valid analytical population
--          plus a transparent quarantine table of rejected rows.
-- Stage:   STEPS 7–8 (master brief §10, §11)
-- Notes:   Do NOT silently discard records. Every exclusion gets a reason.
-- =============================================================================

-- ---------- Quarantine of rows unfit for analysis ----------------------------
DROP TABLE IF EXISTS qa_quarantine;

CREATE TABLE qa_quarantine (
    bug_id             INTEGER,
    rejection_reason   TEXT NOT NULL,
    rejected_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Populate with each failure mode. One row per (bug_id, reason).
-- TODO (STEP 7–8): implement INSERTs for:
--   MISSING_BUG_ID
--   DUPLICATE_BUG_ID
--   MISSING_CREATION_TIME
--   MISSING_RESOLUTION_TIME
--   NEGATIVE_RESOLUTION_DURATION
--   UNKNOWN_SEVERITY
--   NON_FIXED_RESOLUTION

-- ---------- Cleaned analytical view -----------------------------------------
DROP VIEW IF EXISTS v_bugs_clean;

CREATE VIEW v_bugs_clean AS
SELECT
    s.bug_id,
    s.product,
    s.component,
    s.status,
    s.resolution,
    s.severity,
    s.priority,
    s.creation_time,
    s.last_resolved_time,
    s.target_milestone,
    s.version,
    EXTRACT(EPOCH FROM (s.last_resolved_time - s.creation_time)) / 3600.0  AS resolution_hours,
    EXTRACT(EPOCH FROM (s.last_resolved_time - s.creation_time)) / 86400.0 AS resolution_days,
    CASE
        WHEN s.severity IN ('S1', 'S2') THEN 'High'
        WHEN s.severity IN ('S3', 'S4') THEN 'Lower'
        ELSE 'Unclassified'
    END AS severity_group,
    DATE(s.creation_time)                       AS created_date,
    EXTRACT(YEAR    FROM s.creation_time)::INT  AS created_year,
    EXTRACT(QUARTER FROM s.creation_time)::INT  AS created_quarter,
    EXTRACT(MONTH   FROM s.creation_time)::INT  AS created_month,
    TO_CHAR(s.creation_time, 'Month')           AS created_month_name
FROM stg_bugs s
WHERE s.bug_id NOT IN (SELECT bug_id FROM qa_quarantine);
