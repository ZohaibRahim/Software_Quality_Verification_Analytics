-- =============================================================================
-- 01_create_staging.sql
-- Purpose: Create the staging table that preserves raw Bugzilla rows as-is.
-- Stage:   STEP 5 (master brief §9)
-- Notes:   Minimal transformation here. All business logic belongs in
--          02_clean_transform.sql and later.
-- =============================================================================

DROP TABLE IF EXISTS stg_bugs;

CREATE TABLE stg_bugs (
    bug_id              INTEGER     PRIMARY KEY,
    product             TEXT,
    component           TEXT,
    status              TEXT,
    resolution          TEXT,
    severity            TEXT,
    priority            TEXT,
    creation_time       TIMESTAMP,
    last_resolved_time  TIMESTAMP,
    target_milestone    TEXT,
    version             TEXT,
    summary             TEXT
);

-- Load via:
--   \copy stg_bugs FROM 'data/raw/firefox_bugs.csv' WITH (FORMAT csv, HEADER true);
