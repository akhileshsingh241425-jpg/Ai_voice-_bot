#!/bin/bash
# =====================================================
# 🚀 AI Training Voice Bot - AUTO SETUP SCRIPT
# Run this single script and everything will be set up!
# =====================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="ai-training-voice-bot"
APP_DIR="/root/$APP_NAME"
PORT=9000
DB_NAME="ai_voice_bot_new"
DB_USER="root"
DB_PASS="Aborefm@2024"

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   🚀 AI Training Voice Bot - Auto Setup Script        ║${NC}"
echo -e "${BLUE}║   Port: $PORT                                          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_step() {
    echo -e "\n${BLUE}📌 Step $1: $2${NC}"
    echo "────────────────────────────────────────"
}

# ============ STEP 1: System Update ============
print_step "1/10" "Updating System Packages"
apt-get update -qq
print_status "System updated"

# ============ STEP 2: Install Python ============
print_step "2/10" "Installing Python 3 & pip"
apt-get install -y python3 python3-pip python3-venv -qq
print_status "Python installed: $(python3 --version)"

# ============ STEP 3: Install Node.js ============
print_step "3/10" "Installing Node.js"
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt-get install -y nodejs -qq
fi
print_status "Node.js installed: $(node --version)"

# ============ STEP 4: Install PM2 ============
print_step "4/10" "Installing PM2"
npm install -g pm2 -q
print_status "PM2 installed"

# ============ STEP 5: Create Directories ============
print_step "5/10" "Creating Directories"
mkdir -p $APP_DIR/logs
mkdir -p $APP_DIR/frontend_build
mkdir -p $APP_DIR/backend/viva_videos
print_status "Directories created"

# ============ STEP 6: Install Python Dependencies ============
print_step "6/10" "Installing Python Dependencies"
cd $APP_DIR/backend

# Create requirements if not exists
if [ ! -f "requirements.txt" ]; then
    cat > requirements.txt << 'EOF'
flask==2.3.3
flask-cors==4.0.0
pymysql==1.1.0
python-dotenv==1.0.0
requests==2.31.0
werkzeug==2.3.7
numpy==1.24.3
pandas==2.0.3
openpyxl==3.1.2
scipy==1.11.2
scikit-learn==1.3.0
sentence-transformers==2.2.2
faster-whisper==0.9.0
gunicorn==21.2.0
EOF
fi

pip3 install -r requirements.txt -q
print_status "Python dependencies installed"

# ============ STEP 7: Build Frontend ============
print_step "7/10" "Building React Frontend"
cd $APP_DIR/frontend

# Install npm packages
npm install --silent 2>/dev/null

# Build for production
npm run build --silent 2>/dev/null

# Copy build files
cp -r build/* $APP_DIR/frontend_build/
print_status "Frontend built and copied"

# ============ STEP 8: Setup Database ============
print_step "8/10" "Setting up Database"
mysql -u$DB_USER -p$DB_PASS -e "CREATE DATABASE IF NOT EXISTS $DB_NAME;" 2>/dev/null || print_warning "Database may already exist"

# Check if schema file exists and import
if [ -f "$APP_DIR/database/schema.sql" ]; then
    mysql -u$DB_USER -p$DB_PASS $DB_NAME < $APP_DIR/database/schema.sql 2>/dev/null || print_warning "Schema may already be imported"
fi
print_status "Database setup complete"

# ============ STEP 9: Create PM2 Config ============
print_step "9/10" "Creating PM2 Configuration"
cat > $APP_DIR/ecosystem.config.js << EOF
module.exports = {
  apps: [{
    name: '$APP_NAME',
    script: 'app_production.py',
    interpreter: 'python3',
    cwd: '$APP_DIR/backend',
    env: {
      PORT: $PORT,
      FLASK_ENV: 'production',
      DB_HOST: 'localhost',
      DB_USER: '$DB_USER',
      DB_PASSWORD: '$DB_PASS',
      DB_NAME: '$DB_NAME',
      DB_PORT: '3306'
    },
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '500M',
    error_file: '$APP_DIR/logs/error.log',
    out_file: '$APP_DIR/logs/output.log'
  }]
};
EOF
print_status "PM2 config created"

# ============ STEP 10: Start Application ============
print_step "10/10" "Starting Application"

# Stop if already running
pm2 delete $APP_NAME 2>/dev/null || true

# Start with PM2
cd $APP_DIR
pm2 start ecosystem.config.js
pm2 save
pm2 startup 2>/dev/null || true

print_status "Application started!"

# ============ Final Summary ============
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          🎉 SETUP COMPLETE! 🎉                         ║${NC}"
echo -e "${GREEN}╠════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  App URL: http://$(hostname -I | awk '{print $1}'):$PORT            ${NC}"
echo -e "${GREEN}║  Port: $PORT                                            ${NC}"
echo -e "${GREEN}║  PM2 Name: $APP_NAME                          ${NC}"
echo -e "${GREEN}╠════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  Useful Commands:                                      ║${NC}"
echo -e "${GREEN}║  • pm2 status           - Check app status             ║${NC}"
echo -e "${GREEN}║  • pm2 logs $APP_NAME   - View logs        ║${NC}"
echo -e "${GREEN}║  • pm2 restart $APP_NAME - Restart app    ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"

# Test if running
sleep 3
if curl -s http://localhost:$PORT/api/health > /dev/null 2>&1; then
    echo -e "\n${GREEN}✅ Health Check PASSED - App is running!${NC}"
else
    echo -e "\n${YELLOW}⚠️  App may still be starting. Check: pm2 logs $APP_NAME${NC}"
fi
