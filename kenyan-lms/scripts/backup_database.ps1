# Safe PostgreSQL backup. Run from the project root in PowerShell.
# Reads connection details from .env so no password is typed here.
param([string]$OutDir = ".\backups")

$envFile = Join-Path (Get-Location) ".env"
if (-not (Test-Path $envFile)) { Write-Error "No .env file found."; exit 1 }
$values = @{}
Get-Content $envFile | ForEach-Object {
    if ($_ -match '^([A-Z_]+)=(.*)$') { $values[$matches[1]] = $matches[2] }
}

$pgBin = "C:\Program Files\PostgreSQL\18\bin"
if (-not (Test-Path $pgBin)) { Write-Error "PostgreSQL bin not found at $pgBin"; exit 1 }

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outFile = Join-Path $OutDir "$($values['DB_NAME'])_$stamp.sql"

$env:PGPASSWORD = $values['DB_PASSWORD']
& "$pgBin\pg_dump.exe" -w -h $values['DB_HOST'] -p $values['DB_PORT'] -U $values['DB_USER'] -d $values['DB_NAME'] -f $outFile
if ($LASTEXITCODE -eq 0) { Write-Output "Backup written to $outFile" } else { Write-Error "Backup failed."; exit 1 }
