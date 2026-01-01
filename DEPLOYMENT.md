# 🚀 Hostinger Deployment Guide

## Pre-requisites on Hostinger
- **Hosting Plan:** VPS या Cloud Hosting (Python support चाहिए)
- **MySQL Database**
- **SSL Certificate** (free with Hostinger)

## Step 1: Environment Variables

Create `.env` file on server:
```
MYSQL_HOST=localhost
MYSQL_USER=your_hostinger_db_user
MYSQL_PASSWORD=your_hostinger_db_password
MYSQL_DATABASE=ai_voice_bot_new
MYSQL_PORT=3306
FLASK_ENV=production
API_URL=https://your-domain.com
```

## Step 2: Build Frontend

```bash
cd frontend
npm run build
```

This creates `frontend/build/` folder with production files.

## Step 3: Upload Files to Hostinger

Upload these folders/files:
- `backend/` (Python Flask app)
- `frontend/build/` (React production build)
- `requirements.txt`
- `.env`

## Step 4: Database Setup

Import the database schema on Hostinger MySQL.

## Step 5: Server Configuration

### For VPS (recommended):
Use Gunicorn + Nginx

### For Shared Hosting:
Use Passenger (if available)

---

## Quick Commands

### Build Production:
```powershell
.\deploy-build.ps1
```

### Test Production Build Locally:
```powershell
.\deploy-test.ps1
```
