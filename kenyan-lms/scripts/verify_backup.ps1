# Verify a PostgreSQL dump by restoring it into a throwaway database.
# The production database is never modified.
#
# Usage:
#   .\scripts\verify_backup.ps1 -Input C:\backups\lms.dump
param(
    [Parameter(Mandatory = $true)]
    [string]$Input,
    [string]$BackendDir = (Join-Path $PSScriptRoot '..\backend'),
    [string]$TestDatabase = 'lms_restore_test'
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path -LiteralPath $Input)) { throw "Dump not found: $Input" }
if (-not (Test-Path -LiteralPath $BackendDir)) { throw "Backend not found: $BackendDir" }

if (-not $env:DB_NAME) { $env:DB_NAME = "lms" }
if (-not $env:DB_USER) { $env:DB_USER = "postgres" }
if (-not $env:DB_HOST) { $env:DB_HOST = "127.0.0.1" }
if (-not $env:DB_PORT) { $env:DB_PORT = "5432" }

$testDb = "{0}_{1}" -f $TestDatabase, (Get-Date -Format yyyyMMddHHmmss)
if ($testDb -eq $env:DB_NAME) { throw "Test database name collides with the live database." }

$python = Join-Path $BackendDir '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { $python = 'python' }

& createdb --host=$env:DB_HOST --port=$env:DB_PORT --username=$env:DB_USER $testDb
if ($LASTEXITCODE -ne 0) { throw "Could not create temporary database $testDb" }

try {
    & pg_restore --exit-on-error --host=$env:DB_HOST --port=$env:DB_PORT --username=$env:DB_USER --dbname=$testDb $Input
    if ($LASTEXITCODE -ne 0) { throw "Restore into $testDb failed" }

    $env:DB_NAME = $testDb
    Push-Location $BackendDir
    try {
        & $python manage.py check
        if ($LASTEXITCODE -ne 0) { throw "Django check failed against restored data" }

        & $python manage.py shell -c "from django.contrib.auth import get_user_model; from apps.learners.models import Learner; print('restored users:', get_user_model().objects.count(), 'learners:', Learner.objects.count())"
        if ($LASTEXITCODE -ne 0) { throw "Restored data could not be read" }
    }
    finally {
        Pop-Location
    }
    Write-Host "Backup verified by restoring into $testDb (now removing it)."
}
finally {
    & dropdb --if-exists --host=$env:DB_HOST --port=$env:DB_PORT --username=$env:DB_USER $testDb
    if ($LASTEXITCODE -ne 0) { Write-Warning "Could not drop temporary database $testDb" }
}
