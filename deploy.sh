#!/bin/bash
# =====================================================
# AI Training Voice Bot - Deployment Script
# Run this on Hostinger VPS
# =====================================================

echo "🚀 Starting AI Training Voice Bot Deployment..."

# Variables
APP_DIR="/root/ai-training-voice-bot"
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"
BUILD_DIR="$APP_DIR/frontend_build"
PORT=9000

# Step 1: Create directories
echo "📁 Creating directories..."
mkdir -p $APP_DIR
mkdir -p $APP_DIR/logs
mkdir -p $BUILD_DIR

# Step 2: Install Python dependencies
echo "📦 Installing Python dependencies..."
cd $BACKEND_DIR
python3 -m pip install -r requirements.txt

# Step 3: Build React frontend
echo "⚛️ Building React frontend..."
cd $FRONTEND_DIR
npm install
npm run build

# Step 4: Copy build files
echo "📋 Copying build files..."
cp -r $FRONTEND_DIR/build/* $BUILD_DIR/

# Step 5: Start with PM2
echo "🎯 Starting application with PM2..."
cd $APP_DIR
pm2 delete ai-training-voice-bot 2>/dev/null || true
pm2 start ecosystem.config.json --name ai-training-voice-bot
pm2 save

# Step 6: Setup Nginx (if not already configured)
echo "🌐 Configuring Nginx..."
cat > /etc/nginx/sites-available/ai-training-voice-bot << 'EOF'
server {
    listen 80;
    server_name your-domain.com;  # Change this to your domain

    location / {
        proxy_pass http://127.0.0.1:9000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
        
        # Increase timeouts for long operations
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Allow large file uploads (for video)
        client_max_body_size 100M;
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/ai-training-voice-bot /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

echo "✅ Deployment Complete!"
echo "📍 App running on: http://localhost:$PORT"
echo "🌐 Access via Nginx on port 80"
echo ""
echo "Useful commands:"
echo "  pm2 logs ai-training-voice-bot  - View logs"
echo "  pm2 restart ai-training-voice-bot - Restart app"
echo "  pm2 status - Check status"
