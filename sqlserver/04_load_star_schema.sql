-- T-SQL equivalent of sql/04_load_star_schema.sql.
-- Run AFTER importing the CSV and creating the clean view and dimensions.
USE SQVA_SQLServer;
GO
SET NOCOUNT ON;
SET XACT_ABORT ON;
BEGIN TRY
    BEGIN TRANSACTION;
    IF NOT EXISTS (SELECT 1 FROM dbo.v_bugs_clean)
        THROW 50001, 'Clean view is empty: import the CSV and run script 02 first.', 1;
    -- Original model assumes populated components. Fail instead of silently losing rows.
    IF EXISTS (SELECT 1 FROM dbo.v_bugs_clean WHERE component IS NULL OR LTRIM(RTRIM(component)) = N'')
        THROW 50002, 'Clean rows with missing component: resolve before model load.', 1;

    DELETE FROM dbo.fact_bug;
    DELETE FROM dbo.dim_component;
    DELETE FROM dbo.dim_severity;
    DELETE FROM dbo.dim_priority;
    DELETE FROM dbo.dim_date;

    INSERT INTO dbo.dim_component(component_name)
    SELECT DISTINCT component FROM dbo.v_bugs_clean WHERE component IS NOT NULL;
    INSERT INTO dbo.dim_severity(severity, severity_group)
    SELECT DISTINCT severity, severity_group FROM dbo.v_bugs_clean WHERE severity IS NOT NULL;
    INSERT INTO dbo.dim_priority(priority)
    SELECT DISTINCT priority FROM dbo.v_bugs_clean;

    DECLARE @start DATE = (SELECT MIN(created_date) FROM dbo.v_bugs_clean);
    DECLARE @finish DATE = (SELECT MAX(created_date) FROM dbo.v_bugs_clean);
    ;WITH dates AS (
        SELECT @start AS d
        UNION ALL
        SELECT DATEADD(DAY, 1, d) FROM dates WHERE d < @finish
    )
    INSERT INTO dbo.dim_date(date_key, full_date, [year], [quarter], month_number, month_name, year_month)
    SELECT CONVERT(INT, CONVERT(CHAR(8), d, 112)), d,
           YEAR(d), DATEPART(QUARTER, d), MONTH(d), DATENAME(MONTH, d), CONVERT(CHAR(7), d, 126)
    FROM dates OPTION (MAXRECURSION 0);

    INSERT INTO dbo.fact_bug(bug_id, component_key, severity_key, priority_key, created_date_key,
                             resolution_hours, resolution_days)
    SELECT c.bug_id, dc.component_key, ds.severity_key, dp.priority_key, dd.date_key,
           c.resolution_hours, c.resolution_days
    FROM dbo.v_bugs_clean AS c
    INNER JOIN dbo.dim_component AS dc ON dc.component_name = c.component
    INNER JOIN dbo.dim_severity AS ds ON ds.severity = c.severity
    INNER JOIN dbo.dim_priority AS dp ON dp.priority = c.priority
    INNER JOIN dbo.dim_date AS dd ON dd.full_date = c.created_date;

    IF (SELECT COUNT(*) FROM dbo.fact_bug) <> (SELECT COUNT(*) FROM dbo.v_bugs_clean)
        THROW 50003, 'Fact rows do not match clean rows: inspect joins for missing dimension values.', 1;
    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
GO
SELECT (SELECT COUNT(*) FROM dbo.dim_date) AS calendar_days,
       (SELECT COUNT(*) FROM dbo.fact_bug) AS fact_rows;
