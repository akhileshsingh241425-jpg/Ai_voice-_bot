# =====================================================
# 📤 UPLOAD & SETUP - Run this from Windows PowerShell
# This will upload files and run setup on VPS
# =====================================================

# ⚠️ CHANGE THESE VALUES
$VPS_IP = "YOUR_VPS_IP_HERE"
$VPS_USER = "root"
$APP_NAME = "ai-training-voice-bot"
$LOCAL_PATH = $PSScriptRoot

Write-Host "🚀 AI Training Voice Bot - Upload & Deploy" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# Check if VPS_IP is set
if ($VPS_IP -eq "YOUR_VPS_IP_HERE") {
    Write-Host "❌ ERROR: Please edit this script and set your VPS_IP!" -ForegroundColor Red
    Write-Host "   Open upload_and_setup.ps1 and change VPS_IP" -ForegroundColor Yellow
    exit 1
}

Write-Host "📤 Uploading files to ${VPS_USER}@${VPS_IP}..." -ForegroundColor Green

# Create directory on VPS
ssh ${VPS_USER}@${VPS_IP} "mkdir -p /root/$APP_NAME"

# List of folders/files to exclude
$excludes = @(
    "node_modules",
    ".venv",
    "__pycache__",
    ".git",
    "frontend/build"
)

# Build exclude string for scp
$excludeArgs = $excludes | ForEach-Object { "--exclude='$_'" }

# Use rsync if available (Git Bash), otherwise use scp
Write-Host "Uploading backend..." -ForegroundColor Yellow
scp -r "$LOCAL_PATH\backend" "${VPS_USER}@${VPS_IP}:/root/$APP_NAME/"

Write-Host "Uploading frontend..." -ForegroundColor Yellow
scp -r "$LOCAL_PATH\frontend" "${VPS_USER}@${VPS_IP}:/root/$APP_NAME/"

Write-Host "Uploading config files..." -ForegroundColor Yellow
scp "$LOCAL_PATH\setup.sh" "${VPS_USER}@${VPS_IP}:/root/$APP_NAME/"
scp "$LOCAL_PATH\ecosystem.config.json" "${VPS_USER}@${VPS_IP}:/root/$APP_NAME/"

Write-Host ""
Write-Host "✅ Files uploaded!" -ForegroundColor Green
Write-Host ""
Write-Host "🔧 Running setup script on VPS..." -ForegroundColor Yellow

# Run setup script
ssh ${VPS_USER}@${VPS_IP} "cd /root/$APP_NAME && chmod +x setup.sh && ./setup.sh"

Write-Host ""
Write-Host "🎉 Done! Your app should be running at:" -ForegroundColor Green
Write-Host "   http://${VPS_IP}:9000" -ForegroundColor Cyan
