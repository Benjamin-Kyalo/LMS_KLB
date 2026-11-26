# Restore the LMS PostgreSQL database from a custom-format dump.
# Usage:
#   .\scripts\restore_postgres.ps1 -Input C:\backups\lms.dump
param(
    [Parameter(Mandatory = $true)]
    [string]$Input
)

$ErrorActionPreference = "Stop"
if (-not $env:DB_NAME) { $env:DB_NAME = "lms" }
if (-not $env:DB_USER) { $env:DB_USER = "postgres" }
if (-not $env:DB_HOST) { $env:DB_HOST = "127.0.0.1" }
if (-not $env:DB_PORT) { $env:DB_PORT = "5432" }

$pgRestore = "pg_restore"
& $pgRestore --clean --if-exists --host=$env:DB_HOST --port=$env:DB_PORT --username=$env:DB_USER --dbname=$env:DB_NAME $Input
Write-Host "Restore completed from $Input"