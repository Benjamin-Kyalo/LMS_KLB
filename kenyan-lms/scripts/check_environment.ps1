# Quick environment check. Run from the project root in PowerShell.
Write-Output "=== Python ==="; python --version
Write-Output "=== Node ==="; node --version
Write-Output "=== npm ==="; npm --version
Write-Output "=== Git ==="; git --version
Write-Output "=== PostgreSQL service ==="
Get-Service -Name '*postgres*' -ErrorAction SilentlyContinue | Select-Object Name, Status
Write-Output "=== Port 5432 ==="
Get-NetTCPConnection -LocalPort 5432 -State Listen -ErrorAction SilentlyContinue | Select-Object LocalAddress, LocalPort
Write-Output "=== .env present? ==="
Test-Path ".\.env"
