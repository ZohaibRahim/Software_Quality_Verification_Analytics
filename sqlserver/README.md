# SQL Server port of Software Quality Verification Analytics

**Scope:** Add a Microsoft SQL Server / T-SQL implementation of your original PostgreSQL project, while leaving all original PostgreSQL, R and Power BI files untouched. Based on the public repository files reviewed November 11, 2026. The SQL scripts have **not been executed on a SQL Server instance** in this environment; follow the run steps and record real outputs before claiming success.

## Prerequisites (Windows)

1. Download **Microsoft SQL Server 2025 Developer** (free for non-production development) from https://www.microsoft.com/en-us/sql-server/sql-server-downloads and install the **Database Engine**. SQL Server Express also works for this 3,000-row project. Enable Windows Authentication and add your Windows account as an administrator during setup.
2. Install **SQL Server Management Studio 22** from https://learn.microsoft.com/en-us/sql/ssms/download-sql-server-management-studio-ssms.
3. Open SSMS. Under **Connect > Database Engine**, use the local instance name displayed by the installer (often `localhost` for the default instance or `localhost\SQLEXPRESS` for Express). **Authentication: Windows Authentication.** Confirm the connection works before continuing.
4. In PowerShell: `python --version`, then `python -m pip install pyodbc`. If the import reports `ODBC Driver 18 for SQL Server` missing, install it from https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server and retry. You can inspect installed drivers by running `python -c "import pyodbc; print(pyodbc.drivers())"`.
5. Use your **existing** `data/raw/firefox_bugs.csv` from this GitHub repo. Do not rerun the API fetcher: the live source would change the project snapshot and could invalidate your baseline results.

## Run order: about one evening once SQL Server is installed

Copy this `sqlserver/` folder into the root of `Software_Quality_Verification_Analytics`, alongside `sql/`, `data/` and `powerbi/`.

1. In SSMS, use **File > Open > File** to open `sqlserver/00_create_database.sql` and click **Execute** (F5).
2. Execute `sqlserver/01_create_staging.sql`.
3. In PowerShell from the repository root:

   ```powershell
   python sqlserver/import_csv.py --server 'localhost\SQLEXPRESS'
   ```

   Replace the server name with the one you successfully connected to in SSMS. Default instances often use `--server localhost`.
4. Execute scripts **02**, **03**, **04**, **05**, then **06**, in that order (open each in SSMS and press F5). Script 05 outputs QA1-5 anomaly counts, QA6 row reconciliation, and QA7 metrics; script 06 outputs analytical queries and an R-export-shaped dataset.
5. Take screenshots of SSMS showing `(a)` your connected SQL Server instance, `(b)` row counts, and `(c)` QA outputs, and note any mismatch for debugging.

**Expected snapshot benchmarks** (from original project, not measured for this port):

| Measure | Expected |
| --- | ---: |
| `stg_bugs` | 3,000 |
| `v_bugs_clean` | 3,000 |
| `fact_bug` | 3,000 |
| Distinct quarantined IDs | 0 |
| QA1–QA5 anomalies | 0 each |
| QA6 | PASS (3000 = 3000 + 0) |
| High severity (S1 + S2) | 139 |
| Lower severity (S3 + S4) | 1,034 |
| High severity percent (of classified) | 11.85% |

If **any** expected count is different, investigate before updating your resume. Do not label QA7 as passed until the SQL Server output agrees with the original Power BI card values and their filters.

## Important database differences demonstrated

| PostgreSQL | SQL Server (T-SQL) |
| --- | --- |
| `SERIAL` | `IDENTITY(1,1)` |
| `TEXT` | `NVARCHAR(...)` / `NVARCHAR(MAX)` |
| `EXTRACT(EPOCH FROM end - start)` | `DATEDIFF_BIG(SECOND, start, end)` |
| `generate_series()` | Recursive common table expression for calendar dates |
| `TO_CHAR(date,...)` | `CONVERT(...,style)` / `DATENAME()` |
| `PERCENTILE_CONT(...)` aggregate | `PERCENTILE_CONT(...) OVER (...)` window function |
| `COUNT(*) FILTER (WHERE ...)` | `SUM(CASE WHEN ... THEN 1 ELSE 0 END)` |
| `LIMIT 10` | `TOP (10)` |
| `TRUNCATE ... CASCADE` | Ordered `DELETE` respecting SQL Server foreign keys |

The Python loader parses the original `2024-01-01T...Z` timestamps as UTC and writes them to `DATETIME2(0)` in **UTC without a timezone suffix**. This preserves source wall-clock timestamps for difference calculations, rather than letting a local-PC timezone change dashboard values. It also handles quoted commas in Bugzilla summary fields.

## Power BI connection: do after QA checks

1. **Save a copy** of the existing `powerbi/quality_verification_dashboard.pbix` as `quality_verification_dashboard_sqlserver.pbix`. Keep the PostgreSQL file as the baseline.
2. Open the copy in Power BI Desktop > **Transform data**. For each table/query that currently uses PostgreSQL, open **Advanced Editor** and change the *Source* step to `Sql.Database("localhost\SQLEXPRESS", "SQVA_SQLServer")` using your actual server name, and change schema navigation to `dbo` (instead of `public`). A common two-step pattern is:

   ```powerquery
   let
       Source = Sql.Database("localhost\SQLEXPRESS", "SQVA_SQLServer"),
       Fact = Source{[Schema="dbo", Item="fact_bug"]}[Data]
   in
       Fact
   ```

   Use analogous navigation for `dim_component`, `dim_severity`, `dim_priority`, `dim_date`. You may have extra transformation steps in the original PBIX; **keep those** and replace only the connection/navigation portions. If your original uses hand-written SQL queries instead of navigation, share the Power Query Advanced Editor text before replacing it.
3. Use Windows credentials for the local SQL connection. **Close & Apply** and Refresh. Recheck relationships, data types, the six DAX measures, slicers, and all four original headline KPIs. Compare with QA7 from SQL Server **using identical filters**.
4. Do not overwrite the original `.pbix`; show both PostgreSQL and SQL Server variants in the project README.

## CV and GitHub evidence (only after successful local execution)

A defensible resume skills line is:

> **Databases:** Microsoft SQL Server (T-SQL, SSMS; staging, star-schema modelling, data-quality queries), PostgreSQL, SQL

A defensible project line is:

> **Software Quality Verification Analytics:** Ported a 3,000-record defect analytics pipeline from PostgreSQL to Microsoft SQL Server, implementing T-SQL staging, a dimensional star schema, and seven validation checks; verified outputs against the original PostgreSQL and Power BI baseline.

Only claim Power BI **connected to SQL Server** after successfully completing the Power BI steps. You can truthfully describe T-SQL and SQL Server after running 00–06 and documenting the results; do not present a short portfolio port as professional on-the-job SQL Server experience.

## Git commands (after testing)

```powershell
git add sqlserver/
git commit -m "Add SQL Server T-SQL port and QA verification"
git push
```

Tip: in your main README, add a small **SQL Server port** section linking to `sqlserver/README.md` after verification. Keep the original 7 PostgreSQL checks and existing reports intact.

## Troubleshooting

- **Cannot connect / server not found:** Check the SQL Server service in Windows Services (`SQL Server (MSSQLSERVER)` or `SQL Server (SQLEXPRESS)`). Use the same instance name in SSMS and the Python command.
- **`Login failed` / permissions:** Windows Authentication needs a database-level login with write permissions; on a local developer instance your account can be added as sysadmin through setup or an administrator.
- **`Data source name not found` from pyodbc:** Install ODBC Driver 18; it is not the same thing as SSMS or the SQL Server engine.
- **A package error for pyodbc:** Check Python architecture (64-bit) and supported Windows install.
- **QA6 FAIL / facts lower than clean:** Inspect null components or dimension joins; the port includes a fail-fast check to prevent silent row loss.
- **Power BI metrics differ slightly:** Compare timestamp interpretation, SQL Server rounding to `DECIMAL(12,4)`, R/DAX filters and whether unclassified severities were included in denominators. The correct high-severity share divides by High+Lower, not all 3,000 rows.
- **R script:** The existing R tests can stay PostgreSQL-based; `06_analysis_queries.sql` includes a query with equivalent export columns if you want to export SQL Server rows and rerun the test.
