-- Run once in SSMS, connected to your local SQL Server Database Engine.
-- This creates a separate database; your PostgreSQL project is untouched.
USE master;
GO
IF DB_ID(N'SQVA_SQLServer') IS NULL
    CREATE DATABASE SQVA_SQLServer;
GO
USE SQVA_SQLServer;
GO
SELECT DB_NAME() AS active_database, @@VERSION AS sql_server_version;
