#!/bin/bash
# =====================================================
# 📤 UPLOAD & SETUP - Run this from your LOCAL machine
# This will upload files and run setup on VPS
# =====================================================

# ⚠️ CHANGE THESE VALUES
VPS_IP="YOUR_VPS_IP_HERE"
VPS_USER="root"
APP_NAME="ai-training-voice-bot"

echo "🚀 AI Training Voice Bot - Upload & Deploy"
echo "==========================================="
echo ""

# Check if VPS_IP is set
if [ "$VPS_IP" = "YOUR_VPS_IP_HERE" ]; then
    echo "❌ ERROR: Please edit this script and set your VPS_IP!"
    echo "   Open upload_and_setup.sh and change VPS_IP"
    exit 1
fi

echo "📤 Uploading files to $VPS_USER@$VPS_IP..."

# Create directory on VPS
ssh $VPS_USER@$VPS_IP "mkdir -p /root/$APP_NAME"

# Upload all files (excluding node_modules and .venv)
rsync -avz --progress \
    --exclude 'node_modules' \
    --exclude '.venv' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.git' \
    --exclude 'frontend/build' \
    ./ $VPS_USER@$VPS_IP:/root/$APP_NAME/

echo ""
echo "✅ Files uploaded!"
echo ""
echo "🔧 Running setup script on VPS..."

# Run setup script
ssh $VPS_USER@$VPS_IP "cd /root/$APP_NAME && chmod +x setup.sh && ./setup.sh"

echo ""
echo "🎉 Done! Your app should be running at:"
echo "   http://$VPS_IP:9000"
