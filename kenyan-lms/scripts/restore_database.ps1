# Restore a backup into a NEW database (never overwrites an existing one).
# Usage: .\scripts\restore_database.ps1 -BackupFile .\backups\lms_xxx.sql -NewDbName lms_restored
param(
    [Parameter(Mandatory=$true)][string]$BackupFile,
    [Parameter(Mandatory=$true)][string]$NewDbName
)

$envFile = Join-Path (Get-Location) ".env"
$values = @{}
Get-Content $envFile | ForEach-Object {
    if ($_ -match '^([A-Z_]+)=(.*)$') { $values[$matches[1]] = $matches[2] }
}
$pgBin = "C:\Program Files\PostgreSQL\18\bin"
$env:PGPASSWORD = $values['DB_PASSWORD']

$exists = & "$pgBin\psql.exe" -w -h $values['DB_HOST'] -p $values['DB_PORT'] -U $values['DB_USER'] -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$NewDbName';"
if ($exists -eq "1") { Write-Error "Database '$NewDbName' already exists. Choose a different name. Nothing was changed."; exit 1 }

& "$pgBin\createdb.exe" -w -h $values['DB_HOST'] -p $values['DB_PORT'] -U $values['DB_USER'] $NewDbName
& "$pgBin\psql.exe" -w -h $values['DB_HOST'] -p $values['DB_PORT'] -U $values['DB_USER'] -d $NewDbName -f $BackupFile
Write-Output "Restored into '$NewDbName'. Point DB_NAME in .env at it to use."
