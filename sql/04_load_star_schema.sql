-- =============================================================================
-- 04_load_star_schema.sql
-- Purpose: Populate dimensions and fact_bug from v_bugs_clean.
-- Stage:   STEP 9 (master brief §12)
-- Notes:   Deterministic surrogate keys. Idempotent via TRUNCATE.
-- =============================================================================

TRUNCATE fact_bug, dim_component, dim_severity, dim_priority, dim_date RESTART IDENTITY CASCADE;

-- ---------- dim_component ---------------------------------------------------
INSERT INTO dim_component (component_name)
SELECT DISTINCT component
FROM v_bugs_clean
WHERE component IS NOT NULL;

-- ---------- dim_severity ----------------------------------------------------
INSERT INTO dim_severity (severity, severity_group)
SELECT DISTINCT severity, severity_group
FROM v_bugs_clean
WHERE severity IS NOT NULL;

-- ---------- dim_priority ----------------------------------------------------
INSERT INTO dim_priority (priority)
SELECT DISTINCT priority FROM v_bugs_clean;

-- ---------- dim_date (contiguous calendar; no gaps so Power BI accepts it) --
INSERT INTO dim_date (date_key, full_date, year, quarter, month_number, month_name, year_month)
SELECT
    TO_CHAR(d, 'YYYYMMDD')::INT  AS date_key,
    d::DATE                      AS full_date,
    EXTRACT(YEAR    FROM d)::INT,
    EXTRACT(QUARTER FROM d)::INT,
    EXTRACT(MONTH   FROM d)::INT,
    TRIM(TO_CHAR(d, 'Month')),
    TO_CHAR(d, 'YYYY-MM')
FROM generate_series(
    (SELECT MIN(created_date) FROM v_bugs_clean),
    (SELECT MAX(created_date) FROM v_bugs_clean),
    '1 day'::interval
) d;

-- ---------- fact_bug --------------------------------------------------------
INSERT INTO fact_bug (
    bug_id, component_key, severity_key, priority_key, created_date_key,
    resolution_hours, resolution_days
)
SELECT
    c.bug_id,
    dc.component_key,
    ds.severity_key,
    dp.priority_key,
    dd.date_key,
    c.resolution_hours,
    c.resolution_days
FROM v_bugs_clean c
JOIN dim_component dc ON dc.component_name = c.component
JOIN dim_severity  ds ON ds.severity       = c.severity
JOIN dim_priority  dp ON dp.priority       = c.priority
JOIN dim_date      dd ON dd.full_date      = c.created_date;
