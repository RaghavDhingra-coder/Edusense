# 🚀 Cloud Deployment Setup Guide

Complete guide for deploying EduSence AI with cloud storage (PostgreSQL + Cloudinary)

---

## 📋 Overview

EduSence AI now supports cloud-based storage architecture:
- **PostgreSQL (Neon)** - Database for students, sessions, analytics
- **Cloudinary** - Image and video storage
- **Backward Compatible** - Falls back to local storage if cloud not configured

---

## 🎯 Architecture

```
Frontend (Browser)
    ↓
Flask Backend (integrated_server.py)
    ↓
Storage Manager (storage_manager.py) ← Abstraction Layer
    ↓
├─→ PostgreSQL (Neon) ← Student data, sessions, analytics
└─→ Cloudinary ← Images, videos, face crops
```

---

## 📦 Prerequisites

### 1. Neon PostgreSQL Account
- Sign up: https://neon.tech
- Free tier: 10GB storage, 100 hours compute/month
- Get connection string

### 2. Cloudinary Account
- Sign up: https://cloudinary.com
- Free tier: 25GB storage, 25GB bandwidth/month
- Get API credentials

---

## 🔧 Step 1: Setup Neon PostgreSQL

### Create Database

1. **Sign up at Neon**
   - Visit: https://neon.tech
   - Click "Sign Up" (free account)

2. **Create New Project**
   - Click "New Project"
   - Name: `edusence-ai`
   - Region: Choose closest to your users
   - PostgreSQL version: 15 (recommended)

3. **Get Connection String**
   ```
   Format: postgresql://user:password@host/database?sslmode=require
   
   Example:
   postgresql://neondb_owner:abc123xyz@ep-cool-cloud-123456.us-east-2.aws.neon.tech/edusence_db?sslmode=require
   ```

4. **Copy Connection String**
   - Go to Dashboard → Connection Details
   - Copy "Connection string"
   - Save for later

### Test Connection (Optional)

```bash
# Install psql client
brew install postgresql  # macOS
# or
sudo apt-get install postgresql-client  # Linux

# Test connection
psql "postgresql://user:password@host/database?sslmode=require"
```

---

## 🔧 Step 2: Setup Cloudinary

### Create Account

1. **Sign up at Cloudinary**
   - Visit: https://cloudinary.com
   - Click "Sign Up Free"

2. **Get API Credentials**
   - Go to Dashboard
   - Find "Account Details" section
   - Copy:
     - Cloud Name
     - API Key
     - API Secret

3. **Configure Upload Presets (Optional)**
   - Go to Settings → Upload
   - Create preset: `edusence_images`
   - Folder: `edusence/`
   - Mode: Unsigned (for direct uploads)

---

## 🔧 Step 3: Configure Environment Variables

### Create .env File

```bash
# Copy template
cp .env.example .env

# Edit .env file
nano .env  # or use your preferred editor
```

### Fill in Credentials

```env
# ============================================================
# DATABASE CONFIGURATION (PostgreSQL - Neon)
# ============================================================
DATABASE_URL=postgresql://neondb_owner:YOUR_PASSWORD@ep-xxx-xxx.us-east-2.aws.neon.tech/edusence_db?sslmode=require

# ============================================================
# CLOUDINARY CONFIGURATION
# ============================================================
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=123456789012345
CLOUDINARY_API_SECRET=your_api_secret_here

# ============================================================
# APPLICATION CONFIGURATION
# ============================================================
FLASK_ENV=production
SECRET_KEY=change-this-to-random-secret-key

# Server Configuration
HOST=0.0.0.0
PORT=8080
```

### Generate Secret Key

```bash
# Python
python3 -c "import secrets; print(secrets.token_hex(32))"

# Or online
# https://randomkeygen.com/
```

---

## 🔧 Step 4: Install Dependencies

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Install new dependencies
pip install -r requirements.txt

# Verify installation
python3 -c "import sqlalchemy, cloudinary, psycopg2; print('✅ All cloud dependencies installed')"
```

---

## 🔧 Step 5: Initialize Database

### Create Tables

```bash
# Run database initialization
python3 -c "from database import init_database; init_database()"
```

### Verify Tables Created

```bash
# Connect to database
psql "YOUR_DATABASE_URL"

# List tables
\dt

# Expected tables:
# - students
# - student_images
# - sessions
# - session_images
# - analytics
# - recognition_logs
# - uploaded_videos
# - system_config

# Exit
\q
```

---

## 🔧 Step 6: Test Cloud Storage

### Test Database Connection

```bash
python3 -c "
from database import test_database_connection
if test_database_connection():
    print('✅ Database connection successful')
else:
    print('❌ Database connection failed')
"
```

### Test Cloudinary Connection

```bash
python3 -c "
from cloudinary_manager import cloudinary_manager
if cloudinary_manager.is_available():
    print('✅ Cloudinary connection successful')
    print(f'   Cloud Name: {cloudinary_manager.cloud_name}')
else:
    print('❌ Cloudinary connection failed')
"
```

### Test Storage Manager

```bash
python3 -c "
from storage_manager import storage_manager
if storage_manager.is_cloud_enabled():
    print('✅ Cloud storage enabled')
else:
    print('⚠️  Running in local mode')
"
```

---

## 🚀 Step 7: Run Application

### Start Server

```bash
# Start integrated server
python3 integrated_server.py

# Wait for initialization
# You should see:
# ✅ Database connection established
# ✅ Cloudinary initialized successfully
# ✅ Storage Manager: Cloud mode enabled
# * Running on http://127.0.0.1:8080
```

### Test Application

1. **Open Dashboard**
   ```
   http://localhost:8080
   ```

2. **Register a Student**
   - Go to: http://localhost:8080/register.html
   - Register test student
   - Check Cloudinary dashboard for uploaded images
   - Check Neon dashboard for database records

3. **Start Camera/Upload Video**
   - Test webcam monitoring
   - Upload test video
   - Verify images uploaded to Cloudinary
   - Verify session data in PostgreSQL

---

## 🌐 Step 8: Deploy to Cloud Platform

### Option A: Deploy to Render

1. **Create Render Account**
   - Visit: https://render.com
   - Sign up (free tier available)

2. **Create Web Service**
   - Click "New +" → "Web Service"
   - Connect GitHub repository
   - Settings:
     - Name: `edusence-ai`
     - Environment: `Python 3`
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `python3 integrated_server.py`

3. **Add Environment Variables**
   - Go to Environment tab
   - Add all variables from .env file:
     - `DATABASE_URL`
     - `CLOUDINARY_CLOUD_NAME`
     - `CLOUDINARY_API_KEY`
     - `CLOUDINARY_API_SECRET`
     - `SECRET_KEY`

4. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment
   - Access at: `https://edusence-ai.onrender.com`

### Option B: Deploy to Railway

1. **Create Railway Account**
   - Visit: https://railway.app
   - Sign up with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Add Environment Variables**
   - Go to Variables tab
   - Add all variables from .env file

4. **Deploy**
   - Railway auto-deploys
   - Get public URL from Settings

### Option C: Deploy to Heroku

1. **Create Heroku Account**
   - Visit: https://heroku.com
   - Sign up (free tier available)

2. **Install Heroku CLI**
   ```bash
   # macOS
   brew tap heroku/brew && brew install heroku
   
   # Or download from: https://devcenter.heroku.com/articles/heroku-cli
   ```

3. **Login and Create App**
   ```bash
   heroku login
   heroku create edusence-ai
   ```

4. **Add Environment Variables**
   ```bash
   heroku config:set DATABASE_URL="your_database_url"
   heroku config:set CLOUDINARY_CLOUD_NAME="your_cloud_name"
   heroku config:set CLOUDINARY_API_KEY="your_api_key"
   heroku config:set CLOUDINARY_API_SECRET="your_api_secret"
   heroku config:set SECRET_KEY="your_secret_key"
   ```

5. **Deploy**
   ```bash
   git push heroku main
   heroku open
   ```

---

## 🔍 Troubleshooting

### Database Connection Issues

**Error: "could not connect to server"**
```bash
# Check DATABASE_URL format
echo $DATABASE_URL

# Should include ?sslmode=require
# Correct: postgresql://user:pass@host/db?sslmode=require
```

**Error: "password authentication failed"**
```bash
# Verify credentials in Neon dashboard
# Reset password if needed
# Update DATABASE_URL in .env
```

### Cloudinary Upload Issues

**Error: "Invalid API credentials"**
```bash
# Verify credentials
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('Cloud Name:', os.getenv('CLOUDINARY_CLOUD_NAME'))
print('API Key:', os.getenv('CLOUDINARY_API_KEY'))
print('API Secret:', os.getenv('CLOUDINARY_API_SECRET')[:5] + '...')
"
```

**Error: "Upload failed"**
```bash
# Check Cloudinary usage limits
# Free tier: 25GB storage, 25GB bandwidth/month
# Upgrade if exceeded
```

### Application Issues

**App runs but uses local storage**
```bash
# Check if cloud is enabled
python3 -c "
from storage_manager import storage_manager
print('Cloud enabled:', storage_manager.is_cloud_enabled())
print('DB available:', storage_manager.cloud_enabled)
"

# If False, check:
# 1. DATABASE_URL is set
# 2. Cloudinary credentials are set
# 3. No connection errors in logs
```

**Slow uploads**
```bash
# Enable async uploads in .env
ENABLE_ASYNC_UPLOAD=True

# Reduce image quality
# Edit cloudinary_manager.py upload_image():
# Add: quality='auto:low'
```

---

## 📊 Monitoring

### Check Database Usage

```bash
# Connect to Neon
psql "YOUR_DATABASE_URL"

# Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

# Check record counts
SELECT 'students' as table, COUNT(*) FROM students
UNION ALL
SELECT 'sessions', COUNT(*) FROM sessions
UNION ALL
SELECT 'analytics', COUNT(*) FROM analytics;
```

### Check Cloudinary Usage

```bash
# Get usage stats
python3 -c "
from cloudinary_manager import cloudinary_manager
stats = cloudinary_manager.get_usage_stats()
if stats:
    print(f'Storage: {stats[\"storage_used_mb\"]:.2f} MB')
    print(f'Bandwidth: {stats[\"bandwidth_used_mb\"]:.2f} MB')
    print(f'Credits: {stats[\"credits_used\"]}/{stats[\"credits_limit\"]}')
"
```

---

## 🔄 Migration from Local to Cloud

### Migrate Existing Data

If you have existing local data, migrate it:

```bash
# Create migration script
python3 migrate_to_cloud.py

# This will:
# 1. Read local student registry
# 2. Upload images to Cloudinary
# 3. Create database records
# 4. Migrate session data
# 5. Preserve analytics
```

### Backup Before Migration

```bash
# Backup local data
tar -czf backup_$(date +%Y%m%d).tar.gz \
    registered_students/ \
    sessions/ \
    uploads/

# Verify backup
tar -tzf backup_*.tar.gz | head -20
```

---

## 🛡️ Security Best Practices

### 1. Environment Variables

```bash
# NEVER commit .env file
echo ".env" >> .gitignore

# Use different credentials for:
# - Development
# - Staging
# - Production
```

### 2. Database Security

```bash
# Use strong passwords
# Enable SSL (already in connection string)
# Restrict IP access in Neon dashboard
# Regular backups
```

### 3. Cloudinary Security

```bash
# Use signed URLs for sensitive content
# Set upload restrictions
# Enable moderation
# Monitor usage
```

---

## 📈 Performance Optimization

### 1. Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX idx_students_student_id ON students(student_id);
CREATE INDEX idx_sessions_session_id ON sessions(session_id);
CREATE INDEX idx_analytics_student_session ON analytics(student_id, session_id);
CREATE INDEX idx_recognition_logs_timestamp ON recognition_logs(recognized_at);
```

### 2. Cloudinary Optimization

```python
# Use transformations for thumbnails
# Enable auto format and quality
# Use responsive images
# Implement lazy loading
```

### 3. Application Optimization

```bash
# Enable async uploads
ENABLE_ASYNC_UPLOAD=True

# Smart saving (reduce redundant uploads)
ENABLE_SMART_SAVING=True
MIN_FRAMES_BETWEEN_SAVES=30

# Auto cleanup
AUTO_CLEANUP_TEMP_FILES=True
```

---

## 📞 Support

### Neon Support
- Docs: https://neon.tech/docs
- Discord: https://discord.gg/neon
- Email: support@neon.tech

### Cloudinary Support
- Docs: https://cloudinary.com/documentation
- Support: https://support.cloudinary.com
- Community: https://community.cloudinary.com

---

## ✅ Checklist

- [ ] Neon PostgreSQL account created
- [ ] Database connection string obtained
- [ ] Cloudinary account created
- [ ] API credentials obtained
- [ ] .env file configured
- [ ] Dependencies installed
- [ ] Database tables created
- [ ] Connections tested
- [ ] Application running
- [ ] Student registration tested
- [ ] Session processing tested
- [ ] Cloud storage verified
- [ ] Deployed to production (optional)

---

**🎉 Congratulations! Your EduSence AI is now running on cloud infrastructure!**

For questions or issues, check the troubleshooting section or open an issue on GitHub.
