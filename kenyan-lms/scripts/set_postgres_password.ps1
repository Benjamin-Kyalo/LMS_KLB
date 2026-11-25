#requires -RunAsAdministrator
# One-time local helper: align the PostgreSQL role with the owner-designated
# DB_PASSWORD already stored in the project-root .env. The password is never
# printed, stored in this script, or sent to chat/docs.
$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$envPath = Join-Path $projectRoot '.env'
$hbaPath = 'C:\Program Files\PostgreSQL\18\data\pg_hba.conf'
$serviceName = 'postgresql-x64-18'
$psql = 'C:\Program Files\PostgreSQL\18\bin\psql.exe'

$values = @{}
foreach ($line in Get-Content -LiteralPath $envPath) {
    if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$') {
        $values[$Matches[1]] = $Matches[2].Trim('"', "'")
    }
}

$dbUser = $values['DB_USER']
$dbHost = $values['DB_HOST']
$dbPort = $values['DB_PORT']
$dbName = $values['DB_NAME']
$dbPassword = $values['DB_PASSWORD']

if (-not $dbUser -or -not $dbHost -or -not $dbPort -or -not $dbName) {
    throw 'DB_USER, DB_HOST, DB_PORT and DB_NAME must be present in .env.'
}
if (-not $dbPassword) {
    throw 'DB_PASSWORD must be present in .env.'
}

$originalHba = [System.IO.File]::ReadAllBytes($hbaPath)
$originalText = [System.Text.Encoding]::UTF8.GetString($originalHba)
$pattern = '(?m)^(host\s+all\s+all\s+127\.0\.0\.1/32\s+)scram-sha-256[ \t]*(\r?)$'
if ($originalText -notmatch $pattern) {
    throw 'Expected localhost scram-sha-256 rule not found in pg_hba.conf.'
}
$trustText = [regex]::new($pattern).Replace($originalText, '${1}trust${2}', 1)

try {
    [System.IO.File]::WriteAllBytes(
        $hbaPath, [System.Text.Encoding]::UTF8.GetBytes($trustText)
    )
    Restart-Service -Name $serviceName

    $literalPassword = $dbPassword.Replace("'", "''")
    $sql = "ALTER ROLE `"$dbUser`" WITH PASSWORD '$literalPassword';"
    & $psql -h $dbHost -p $dbPort -U $dbUser -d 'postgres' -v ON_ERROR_STOP=1 -c $sql
    if ($LASTEXITCODE -ne 0) { throw 'ALTER ROLE failed.' }

    $env:PGPASSWORD = $dbPassword
    & $psql -h $dbHost -p $dbPort -U $dbUser -d $dbName -v ON_ERROR_STOP=1 `
        -c 'SELECT 1;' | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Verification connection failed.' }

    Write-Host 'ROLE_PASSWORD_SET_FROM_ENV: True'
    Write-Host 'ENV_PASSWORD_UNCHANGED: True'
    Write-Host 'VERIFY_CONNECTION: True'
}
finally {
    [System.IO.File]::WriteAllBytes($hbaPath, $originalHba)
    Restart-Service -Name $serviceName
    Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
    Write-Host 'HBA_RESTORED: True'
}
