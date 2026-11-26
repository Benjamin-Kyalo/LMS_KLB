# Back up the LMS PostgreSQL database.
# Usage:
#   .\scripts\backup_postgres.ps1
#   .\scripts\backup_postgres.ps1 -Output C:\backups\lms.dump
param(
    [string]$Output = "C:\Users\Admin IT\AppData\Local\Temp\opencode\lms-backup.dump"
)

$ErrorActionPreference = "Stop"
if (-not $env:DB_NAME) { $env:DB_NAME = "lms" }
if (-not $env:DB_USER) { $env:DB_USER = "postgres" }
if (-not $env:DB_HOST) { $env:DB_HOST = "127.0.0.1" }
if (-not $env:DB_PORT) { $env:DB_PORT = "5432" }

$pgDump = "pg_dump"
& $pgDump --format=custom --file=$Output --host=$env:DB_HOST --port=$env:DB_PORT --username=$env:DB_USER $env:DB_NAME
Write-Host "Backup written to $Output"