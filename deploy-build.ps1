# Production Build Script for Hostinger Deployment
# Run: .\deploy-build.ps1

Write-Host "🚀 Starting Production Build..." -ForegroundColor Cyan

# Step 1: Build React Frontend
Write-Host "`n📦 Building React Frontend..." -ForegroundColor Yellow
Set-Location "frontend"

# Set production API URL
$envContent = @"
REACT_APP_API_URL=https://your-domain.com/api
REACT_APP_ENV=production
"@
$envContent | Out-File -FilePath ".env.production" -Encoding UTF8

npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Frontend build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Frontend build complete!" -ForegroundColor Green

Set-Location ".."

# Step 2: Create deployment package
Write-Host "`n📁 Creating Deployment Package..." -ForegroundColor Yellow

$deployDir = "deploy_package"
if (Test-Path $deployDir) {
    Remove-Item $deployDir -Recurse -Force
}
New-Item -ItemType Directory -Path $deployDir | Out-Null

# Copy backend
Copy-Item -Path "backend" -Destination "$deployDir/backend" -Recurse -Exclude @("__pycache__", "*.pyc", "instance", "temp_audio", "viva_videos")

# Copy frontend build
Copy-Item -Path "frontend/build" -Destination "$deployDir/frontend" -Recurse

# Create production requirements
Copy-Item -Path "backend/requirements.txt" -Destination "$deployDir/requirements.txt"

# Create .env template
$envTemplate = @"
# Hostinger Database Configuration
MYSQL_HOST=localhost
MYSQL_USER=YOUR_DB_USER
MYSQL_PASSWORD=YOUR_DB_PASSWORD
MYSQL_DATABASE=ai_voice_bot_new
MYSQL_PORT=3306

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-secret-key-change-this

# API Configuration
API_URL=https://your-domain.com
CORS_ORIGINS=https://your-domain.com
"@
$envTemplate | Out-File -FilePath "$deployDir/.env.template" -Encoding UTF8

# Create Gunicorn config
$gunicornConfig = @"
# Gunicorn configuration for production
bind = "0.0.0.0:5000"
workers = 2
threads = 4
worker_class = "sync"
timeout = 120
keepalive = 5
errorlog = "logs/error.log"
accesslog = "logs/access.log"
loglevel = "info"
"@
$gunicornConfig | Out-File -FilePath "$deployDir/gunicorn.conf.py" -Encoding UTF8

# Create startup script
$startScript = @"
#!/bin/bash
# Start production server
source venv/bin/activate
cd backend
gunicorn -c ../gunicorn.conf.py app:create_app()
"@
$startScript | Out-File -FilePath "$deployDir/start.sh" -Encoding UTF8 -NoNewline

Write-Host "✅ Deployment package created at: $deployDir/" -ForegroundColor Green

# Step 3: Create ZIP
Write-Host "`n📦 Creating ZIP archive..." -ForegroundColor Yellow
$zipPath = "ai_voice_bot_deploy.zip"
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}
Compress-Archive -Path "$deployDir/*" -DestinationPath $zipPath

Write-Host "`n✅ Deployment package ready!" -ForegroundColor Green
Write-Host "📁 ZIP file: $zipPath" -ForegroundColor Cyan
Write-Host "`n📋 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Upload $zipPath to Hostinger" -ForegroundColor White
Write-Host "2. Extract on server" -ForegroundColor White
Write-Host "3. Configure .env file with database credentials" -ForegroundColor White
Write-Host "4. Setup Python virtual environment" -ForegroundColor White
Write-Host "5. Install dependencies: pip install -r requirements.txt" -ForegroundColor White
Write-Host "6. Import database schema" -ForegroundColor White
Write-Host "7. Start server with Gunicorn" -ForegroundColor White
