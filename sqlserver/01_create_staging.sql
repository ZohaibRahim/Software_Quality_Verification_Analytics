-- T-SQL equivalent of sql/01_create_staging.sql.
-- CAUTION: Re-running drops previously imported staging data.
USE SQVA_SQLServer;
GO
IF OBJECT_ID(N'dbo.v_bugs_clean', N'V') IS NOT NULL DROP VIEW dbo.v_bugs_clean;
IF OBJECT_ID(N'dbo.stg_bugs', N'U') IS NOT NULL DROP TABLE dbo.stg_bugs;
GO
CREATE TABLE dbo.stg_bugs (
    bug_id              INT NOT NULL PRIMARY KEY,
    product             NVARCHAR(255) NULL,
    component           NVARCHAR(255) NULL,
    status              NVARCHAR(80) NULL,
    resolution          NVARCHAR(80) NULL,
    severity            NVARCHAR(20) NULL,
    priority            NVARCHAR(20) NULL,
    creation_time       DATETIME2(0) NULL, -- import script normalizes UTC/Z to naive UTC
    last_resolved_time  DATETIME2(0) NULL,
    target_milestone    NVARCHAR(255) NULL,
    version             NVARCHAR(255) NULL,
    summary             NVARCHAR(MAX) NULL
);
GO
SELECT TOP (0) * FROM dbo.stg_bugs;
