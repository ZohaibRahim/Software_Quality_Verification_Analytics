-- =============================================================================
-- 06_analysis_queries.sql
-- Purpose: Supporting analytical queries that feed R, Power BI, and
--          the root-cause investigation.
-- Stage:   STEPS 11, 18, 19 (master brief §16, §19, §27)
-- =============================================================================

-- --- Export dataset for R ---------------------------------------------------
-- COPY (
--     SELECT bug_id, severity, severity_group, resolution_days, resolution_hours,
--            component_name, year_month
--     FROM fact_bug f
--     JOIN dim_severity  ds ON ds.severity_key  = f.severity_key
--     JOIN dim_component dc ON dc.component_key = f.component_key
--     JOIN dim_date      dd ON dd.date_key      = f.created_date_key
-- ) TO 'analysis_dataset.csv' WITH (FORMAT csv, HEADER true);

-- --- Headline KPIs ----------------------------------------------------------
SELECT
    COUNT(*)                                                        AS total_defects,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY resolution_days)    AS median_resolution_days,
    AVG(resolution_days)                                            AS avg_resolution_days,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY resolution_days)   AS p75_resolution_days
FROM fact_bug;

-- --- Defects per month ------------------------------------------------------
SELECT dd.year_month, COUNT(*) AS defects
FROM fact_bug f
JOIN dim_date dd ON dd.date_key = f.created_date_key
GROUP BY dd.year_month
ORDER BY dd.year_month;

-- --- Median resolution by component (top 10) --------------------------------
SELECT
    dc.component_name,
    COUNT(*)                                                       AS defect_count,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY resolution_days)   AS median_resolution_days
FROM fact_bug f
JOIN dim_component dc ON dc.component_key = f.component_key
GROUP BY dc.component_name
ORDER BY defect_count DESC
LIMIT 10;

-- --- Resolution by severity -------------------------------------------------
SELECT
    ds.severity,
    ds.severity_group,
    COUNT(*)                                                       AS defect_count,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY resolution_days)   AS median_resolution_days
FROM fact_bug f
JOIN dim_severity ds ON ds.severity_key = f.severity_key
GROUP BY ds.severity, ds.severity_group
ORDER BY ds.severity;

-- --- Severity mix by month (for root-cause decomposition) -------------------
SELECT
    dd.year_month,
    ds.severity_group,
    COUNT(*) AS defects
FROM fact_bug f
JOIN dim_date     dd ON dd.date_key     = f.created_date_key
JOIN dim_severity ds ON ds.severity_key = f.severity_key
GROUP BY dd.year_month, ds.severity_group
ORDER BY dd.year_month, ds.severity_group;

-- --- Component share by month (for root-cause decomposition) ----------------
SELECT
    dd.year_month,
    dc.component_name,
    COUNT(*) AS defects
FROM fact_bug f
JOIN dim_date      dd ON dd.date_key      = f.created_date_key
JOIN dim_component dc ON dc.component_key = f.component_key
GROUP BY dd.year_month, dc.component_name
ORDER BY dd.year_month, defects DESC;
