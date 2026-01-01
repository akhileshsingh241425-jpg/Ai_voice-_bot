# 🚀 AI Training Voice Bot - Hostinger Deployment Guide

## Port: 9000 (Frontend + Backend together)

---

## Step 1: Upload Files to Hostinger VPS

### Option A: Using SCP
```bash
# From your local machine
scp -r "C:\Users\hp\Desktop\AI traning voice boot\*" root@your-vps-ip:/root/ai-training-voice-bot/
```

### Option B: Using FileZilla/SFTP
1. Connect to VPS using SFTP
2. Upload entire folder to `/root/ai-training-voice-bot/`

---

## Step 2: SSH into VPS
```bash
ssh root@your-vps-ip
```

---

## Step 3: Install Dependencies

### Python Setup
```bash
cd /root/ai-training-voice-bot/backend
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

### Node.js Setup (for building frontend)
```bash
cd /root/ai-training-voice-bot/frontend
npm install
```

---

## Step 4: Build Frontend
```bash
cd /root/ai-training-voice-bot/frontend
npm run build

# Copy build to backend folder
mkdir -p /root/ai-training-voice-bot/frontend_build
cp -r build/* /root/ai-training-voice-bot/frontend_build/
```

---

## Step 5: Setup Database

### Create Database
```bash
mysql -u root -p
```

```sql
CREATE DATABASE ai_voice_bot_new;
USE ai_voice_bot_new;

-- Import your SQL file
SOURCE /root/ai-training-voice-bot/database/schema.sql;
```

---

## Step 6: Test Application
```bash
cd /root/ai-training-voice-bot/backend
python3 app_production.py
```
Visit: `http://your-vps-ip:9000`

---

## Step 7: Setup PM2 (Production)
```bash
cd /root/ai-training-voice-bot
mkdir -p logs

# Start with PM2
pm2 start ecosystem.config.json
pm2 save
pm2 startup
```

---

## Step 8: Configure Nginx (Optional - for domain)

### Create Nginx config
```bash
nano /etc/nginx/sites-available/ai-training-voice-bot
```

### Add this config:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:9000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_cache_bypass $http_upgrade;
        client_max_body_size 100M;
    }
}
```

### Enable site
```bash
ln -s /etc/nginx/sites-available/ai-training-voice-bot /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

---

## 📋 Quick Commands

| Command | Description |
|---------|-------------|
| `pm2 status` | Check app status |
| `pm2 logs ai-training-voice-bot` | View logs |
| `pm2 restart ai-training-voice-bot` | Restart app |
| `pm2 stop ai-training-voice-bot` | Stop app |

---

## 🔧 Troubleshooting

### Port already in use
```bash
lsof -i :9000
kill -9 <PID>
```

### Check if running
```bash
curl http://localhost:9000/api/health
```

### View errors
```bash
pm2 logs ai-training-voice-bot --err
```

---

## 📁 File Structure on Server

```
/root/ai-training-voice-bot/
├── backend/
│   ├── app_production.py    # Main production server
│   ├── app/                  # Flask app
│   ├── viva_videos/          # Video recordings
│   └── requirements.txt
├── frontend_build/           # React build files
├── ecosystem.config.json     # PM2 config
├── logs/                     # Application logs
└── deploy.sh                 # Deployment script
```

---

## ✅ Checklist

- [ ] Files uploaded to VPS
- [ ] Python dependencies installed
- [ ] Frontend built and copied
- [ ] Database created and imported
- [ ] App tested on port 9000
- [ ] PM2 configured
- [ ] Nginx configured (if using domain)
