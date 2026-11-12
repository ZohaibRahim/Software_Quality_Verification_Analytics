-- T-SQL adaptation of sql/06_analysis_queries.sql.
USE SQVA_SQLServer;
GO
-- Headline KPIs. PERCENTILE_CONT is a SQL Server window function.
;WITH x AS (
    SELECT f.resolution_days,
           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.resolution_days) OVER () AS median_days,
           PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY f.resolution_days) OVER () AS p75_days
    FROM dbo.fact_bug f
)
SELECT COUNT(*) AS total_defects, CAST(MAX(median_days) AS DECIMAL(18,4)) AS median_resolution_days,
       CAST(AVG(resolution_days) AS DECIMAL(18,4)) AS avg_resolution_days,
       CAST(MAX(p75_days) AS DECIMAL(18,4)) AS p75_resolution_days
FROM x;
GO
-- Defects per month.
SELECT d.year_month, COUNT(*) AS defects
FROM dbo.fact_bug f JOIN dbo.dim_date d ON d.date_key=f.created_date_key
GROUP BY d.year_month ORDER BY d.year_month;
GO
-- Median resolution by component, top 10 by volume.
;WITH component_medians AS (
    SELECT d.component_name, f.resolution_days,
           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.resolution_days)
                OVER (PARTITION BY d.component_key) AS median_days
    FROM dbo.fact_bug f JOIN dbo.dim_component d ON d.component_key=f.component_key
)
SELECT TOP (10) component_name, COUNT(*) AS defect_count,
       CAST(MAX(median_days) AS DECIMAL(18,4)) AS median_resolution_days
FROM component_medians
GROUP BY component_name ORDER BY defect_count DESC, component_name;
GO
-- Median resolution by severity and severity group.
;WITH severity_medians AS (
    SELECT d.severity, d.severity_group, f.resolution_days,
           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.resolution_days)
                OVER (PARTITION BY d.severity_key) AS median_days
    FROM dbo.fact_bug f JOIN dbo.dim_severity d ON d.severity_key=f.severity_key
)
SELECT severity, severity_group, COUNT(*) AS defect_count,
       CAST(MAX(median_days) AS DECIMAL(18,4)) AS median_resolution_days
FROM severity_medians GROUP BY severity,severity_group ORDER BY severity;
GO
-- Severity mix by month.
SELECT d.year_month, s.severity_group, COUNT(*) AS defects
FROM dbo.fact_bug f
JOIN dbo.dim_date d ON d.date_key=f.created_date_key
JOIN dbo.dim_severity s ON s.severity_key=f.severity_key
GROUP BY d.year_month,s.severity_group ORDER BY d.year_month,s.severity_group;
GO
-- Component share by month.
SELECT d.year_month,c.component_name,COUNT(*) AS defects
FROM dbo.fact_bug f
JOIN dbo.dim_date d ON d.date_key=f.created_date_key
JOIN dbo.dim_component c ON c.component_key=f.component_key
GROUP BY d.year_month,c.component_name ORDER BY d.year_month,defects DESC;
GO
-- R-export equivalent: in SSMS Results to File (Ctrl+Shift+F) or Save Results As CSV.
SELECT f.bug_id, s.severity, s.severity_group, f.resolution_days,
       f.resolution_hours, c.component_name, d.year_month
FROM dbo.fact_bug f
JOIN dbo.dim_severity s ON s.severity_key=f.severity_key
JOIN dbo.dim_component c ON c.component_key=f.component_key
JOIN dbo.dim_date d ON d.date_key=f.created_date_key
ORDER BY f.bug_id;
