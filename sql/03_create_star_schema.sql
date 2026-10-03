-- =============================================================================
-- 03_create_star_schema.sql
-- Purpose: DDL for the dimensional model (fact_bug + dim_component +
--          dim_severity + dim_priority + dim_date).
-- Stage:   STEP 9 (master brief §12, §13)
-- Notes:   Keep this small. No vanity dimensions.
-- =============================================================================

DROP TABLE IF EXISTS fact_bug      CASCADE;
DROP TABLE IF EXISTS dim_component CASCADE;
DROP TABLE IF EXISTS dim_severity  CASCADE;
DROP TABLE IF EXISTS dim_priority  CASCADE;
DROP TABLE IF EXISTS dim_date      CASCADE;

CREATE TABLE dim_component (
    component_key   SERIAL PRIMARY KEY,
    component_name  TEXT UNIQUE NOT NULL
);

CREATE TABLE dim_severity (
    severity_key    SERIAL PRIMARY KEY,
    severity        TEXT UNIQUE NOT NULL,
    severity_group  TEXT NOT NULL
);

CREATE TABLE dim_priority (
    priority_key    SERIAL PRIMARY KEY,
    priority        TEXT UNIQUE NOT NULL
);

CREATE TABLE dim_date (
    date_key        INTEGER PRIMARY KEY,  -- yyyymmdd
    full_date       DATE NOT NULL,
    year            INTEGER,
    quarter         INTEGER,
    month_number    INTEGER,
    month_name      TEXT,
    year_month      TEXT                   -- e.g. '2024-03'
);

CREATE TABLE fact_bug (
    bug_id            INTEGER PRIMARY KEY,
    component_key     INTEGER NOT NULL REFERENCES dim_component(component_key),
    severity_key      INTEGER NOT NULL REFERENCES dim_severity(severity_key),
    priority_key      INTEGER NOT NULL REFERENCES dim_priority(priority_key),
    created_date_key  INTEGER NOT NULL REFERENCES dim_date(date_key),
    resolution_hours  NUMERIC(12,4) NOT NULL CHECK (resolution_hours >= 0),
    resolution_days   NUMERIC(12,4) NOT NULL CHECK (resolution_days  >= 0)
);

CREATE INDEX idx_fact_bug_component ON fact_bug(component_key);
CREATE INDEX idx_fact_bug_severity  ON fact_bug(severity_key);
CREATE INDEX idx_fact_bug_date      ON fact_bug(created_date_key);
