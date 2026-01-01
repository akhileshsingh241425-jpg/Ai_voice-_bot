# Database Export Script for Hostinger
# Run: .\export-database.ps1

Write-Host "📦 Exporting Database Schema and Data..." -ForegroundColor Cyan

$mysqlPath = "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe"
$exportDir = "database_export"

# Create export directory
if (!(Test-Path $exportDir)) {
    New-Item -ItemType Directory -Path $exportDir | Out-Null
}

# Export schema only
Write-Host "Exporting schema..." -ForegroundColor Yellow

& "$mysqlPath" -u root -proot --no-data ai_voice_bot_new > "$exportDir\schema.sql"

# Export full data (if needed)
Write-Host "Exporting full database with data..." -ForegroundColor Yellow

& "$mysqlPath" -u root -proot ai_voice_bot_new > "$exportDir\full_database.sql"

# Export specific tables
Write-Host "Exporting specific tables..." -ForegroundColor Yellow

& "$mysqlPath" -u root -proot ai_voice_bot_new training_topics qa_bank_new employee > "$exportDir\essential_tables.sql"

Write-Host "`n✅ Database exported to $exportDir/" -ForegroundColor Green
Write-Host "Files created:" -ForegroundColor Cyan
Get-ChildItem $exportDir | ForEach-Object { Write-Host "  - $($_.Name) ($([math]::Round($_.Length/1KB, 2)) KB)" }

Write-Host "`n📋 Import on Hostinger:" -ForegroundColor Yellow
Write-Host "mysql -u your_user -p your_database < schema.sql" -ForegroundColor White
