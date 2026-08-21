# ============================================================
# BACKUP ONLINE DATABASE
# Jaipur Gems / pydjango
# ============================================================

$ErrorActionPreference = "Stop"

# PostgreSQL tools
$PgDump = "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe"

# ONLINE / RENDER DATABASE
<# $RenderHost = "dpg-d9eb2p3rjlhs73c34i20-a.oregon-postgres.render.com"
$RenderPort = "5432"
$RenderUser = "pydijango_user"
$RenderDatabase = "pydijango" #>

# ONLINE / Neon DATABASE
$RenderHost = "ep-hidden-grass-axswx6uw-pooler.c-4.us-east-2.aws.neon.tech"
$RenderPort = "5432"
$RenderUser = "neondb_owner"
$RenderDatabase = "neondb"

# Project backup folder
$ProjectRoot = "G:\Self made Projects\html5\pydjango"
$Year = Get-Date -Format "yyyy"
$BackupFolder = Join-Path $ProjectRoot "backup\render_master\$Year"

# Create folder if it does not exist
New-Item -ItemType Directory -Force -Path $BackupFolder | Out-Null

# Timestamped backup filename
$Timestamp = Get-Date -Format "yyyy_MM_dd_HHmmss"
$BackupFile = Join-Path $BackupFolder "render_master_$Timestamp.dump"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " ONLINE DATABASE BACKUP" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Database : $RenderDatabase" -ForegroundColor Yellow
Write-Host "Host     : $RenderHost" -ForegroundColor Yellow
Write-Host "Backup   : $BackupFile" -ForegroundColor Yellow
Write-Host ""

if (-not (Test-Path $PgDump)) {
    throw "pg_dump.exe was not found at: $PgDump"
}

Write-Host "Starting backup..." -ForegroundColor Green
Write-Host "You will be asked for the Render PostgreSQL password." -ForegroundColor Gray
Write-Host ""

& $PgDump `
    --host=$RenderHost `
    --port=$RenderPort `
    --username=$RenderUser `
    --dbname=$RenderDatabase `
    --format=custom `
    --file=$BackupFile

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "BACKUP FAILED." -ForegroundColor Red
    exit $LASTEXITCODE
}

if (-not (Test-Path $BackupFile)) {
    Write-Host ""
    Write-Host "BACKUP FAILED: dump file was not created." -ForegroundColor Red
    exit 1
}

$SizeMB = [math]::Round((Get-Item $BackupFile).Length / 1MB, 2)

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host " BACKUP COMPLETED SUCCESSFULLY" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host "File : $BackupFile" -ForegroundColor White
Write-Host "Size : $SizeMB MB" -ForegroundColor White
Write-Host ""
