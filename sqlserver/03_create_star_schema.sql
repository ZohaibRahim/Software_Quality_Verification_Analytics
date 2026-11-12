-- T-SQL equivalent of sql/03_create_star_schema.sql.
-- CAUTION: Re-running removes fact and dimension tables, not staging data.
USE SQVA_SQLServer;
GO
IF OBJECT_ID(N'dbo.fact_bug',N'U') IS NOT NULL DROP TABLE dbo.fact_bug;
IF OBJECT_ID(N'dbo.dim_component',N'U') IS NOT NULL DROP TABLE dbo.dim_component;
IF OBJECT_ID(N'dbo.dim_severity',N'U') IS NOT NULL DROP TABLE dbo.dim_severity;
IF OBJECT_ID(N'dbo.dim_priority',N'U') IS NOT NULL DROP TABLE dbo.dim_priority;
IF OBJECT_ID(N'dbo.dim_date',N'U') IS NOT NULL DROP TABLE dbo.dim_date;
GO
CREATE TABLE dbo.dim_component (
    component_key INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    component_name NVARCHAR(255) NOT NULL UNIQUE
);
CREATE TABLE dbo.dim_severity (
    severity_key INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    severity NVARCHAR(20) NOT NULL UNIQUE,
    severity_group NVARCHAR(20) NOT NULL
);
CREATE TABLE dbo.dim_priority (
    priority_key INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    priority NVARCHAR(20) NOT NULL UNIQUE
);
CREATE TABLE dbo.dim_date (
    date_key INT NOT NULL PRIMARY KEY, -- YYYYMMDD
    full_date DATE NOT NULL UNIQUE,
    [year] INT NULL,
    [quarter] INT NULL,
    month_number INT NULL,
    month_name NVARCHAR(20) NULL,
    year_month CHAR(7) NULL
);
CREATE TABLE dbo.fact_bug (
    bug_id INT NOT NULL PRIMARY KEY,
    component_key INT NOT NULL REFERENCES dbo.dim_component(component_key),
    severity_key INT NOT NULL REFERENCES dbo.dim_severity(severity_key),
    priority_key INT NOT NULL REFERENCES dbo.dim_priority(priority_key),
    created_date_key INT NOT NULL REFERENCES dbo.dim_date(date_key),
    resolution_hours DECIMAL(12,4) NOT NULL CHECK (resolution_hours >= 0),
    resolution_days DECIMAL(12,4) NOT NULL CHECK (resolution_days >= 0)
);
CREATE INDEX IX_fact_bug_component ON dbo.fact_bug(component_key);
CREATE INDEX IX_fact_bug_severity ON dbo.fact_bug(severity_key);
CREATE INDEX IX_fact_bug_date ON dbo.fact_bug(created_date_key);
GO
