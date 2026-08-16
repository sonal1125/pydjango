# ============================================================
# RESTORE LATEST ONLINE RENDER BACKUP -> LOCAL POSTGRESQL
# Jaipur Gems / pydjango
#
# WARNING:
# This will DELETE EVERYTHING in the public schema of the
# LOCAL target database only.
# It will NOT modify the Render/online database.
# ============================================================

$ErrorActionPreference = "Stop"

# PostgreSQL tools
$Psql = "C:\Program Files\PostgreSQL\18\bin\psql.exe"
$PgRestore = "C:\Program Files\PostgreSQL\18\bin\pg_restore.exe"

# LOCAL PostgreSQL
$LocalHost = "localhost"
$LocalPort = "5433"
$LocalUser = "postgres"
$LocalDatabase = "pydijango_render_restore"

# Project backup folder
$ProjectRoot = "G:\Self made Projects\html5\pydjango"
$Year = Get-Date -Format "yyyy"
$BackupFolder = Join-Path $ProjectRoot "backup\render_master\$Year"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " ONLINE -> LOCAL DATABASE RESTORE" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "LOCAL target database:" -ForegroundColor Yellow
Write-Host "  $LocalDatabase" -ForegroundColor White
Write-Host ""
Write-Host "WARNING: The LOCAL database public schema will be emptied." -ForegroundColor Red
Write-Host "The Render/online database will NOT be changed." -ForegroundColor Green
Write-Host ""

if (-not (Test-Path $Psql)) {
    throw "psql.exe was not found at: $Psql"
}

if (-not (Test-Path $PgRestore)) {
    throw "pg_restore.exe was not found at: $PgRestore"
}

if (-not (Test-Path $BackupFolder)) {
    throw "Backup folder was not found: $BackupFolder"
}

# Find the newest .dump backup
$LatestBackup = Get-ChildItem -Path $BackupFolder -Filter "*.dump" -File |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if ($null -eq $LatestBackup) {
    throw "No .dump backup was found in: $BackupFolder"
}

Write-Host "Latest backup selected:" -ForegroundColor Green
Write-Host "  $($LatestBackup.FullName)" -ForegroundColor White
Write-Host "  Created: $($LatestBackup.LastWriteTime)" -ForegroundColor Gray
Write-Host ""

$Confirm = Read-Host "Type RESTORE to continue"

if ($Confirm -ne "RESTORE") {
    Write-Host ""
    Write-Host "Restore cancelled. Nothing was changed." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Step 1/2 - Emptying LOCAL public schema..." -ForegroundColor Cyan
Write-Host "You will be asked for the LOCAL PostgreSQL password." -ForegroundColor Gray
Write-Host ""

& $Psql `
    --host=$LocalHost `
    --port=$LocalPort `
    --username=$LocalUser `
    --dbname=$LocalDatabase `
    --command="DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "FAILED while cleaning the local database." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Step 2/2 - Restoring backup into LOCAL database..." -ForegroundColor Cyan
Write-Host ""

& $PgRestore `
    --host=$LocalHost `
    --port=$LocalPort `
    --username=$LocalUser `
    --dbname=$LocalDatabase `
    --no-owner `
    --no-privileges `
    --exit-on-error `
    "$($LatestBackup.FullName)"

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "RESTORE FAILED." -ForegroundColor Red
    Write-Host "The local database may be partially restored." -ForegroundColor Yellow
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host " RESTORE COMPLETED SUCCESSFULLY" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Local database: $LocalDatabase" -ForegroundColor White
Write-Host "Backup used   : $($LatestBackup.Name)" -ForegroundColor White
Write-Host ""
Write-Host "Next recommended command:" -ForegroundColor Cyan
Write-Host "  python manage.py migrate" -ForegroundColor White
Write-Host ""
