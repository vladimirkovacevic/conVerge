# ConVerge Deployment Guide

Complete guide for deploying ConVerge to production:
- **Frontend**: Vercel
- **Backend**: DigitalOcean Droplet (Ubuntu)

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Backend Deployment (DigitalOcean)](#backend-deployment-digitalocean)
3. [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
4. [Post-Deployment Configuration](#post-deployment-configuration)
5. [Monitoring & Maintenance](#monitoring--maintenance)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Accounts
- ✅ DigitalOcean account with billing enabled
- ✅ Vercel account (free tier works)
- ✅ Domain name (optional but recommended)
- ✅ OpenRouter API key

### Local Tools
```bash
# Install required CLI tools
npm install -g vercel    # Vercel CLI
# SSH client (pre-installed on Mac/Linux)
```

---

## Backend Deployment (DigitalOcean)

### Step 1: Create DigitalOcean Droplet

1. **Log in to DigitalOcean** → Create → Droplets

2. **Configure Droplet:**
   - **Image**: Ubuntu 22.04 LTS
   - **Plan**: Basic ($6/month - 1 GB RAM, 1 vCPU)
   - **Datacenter**: Choose closest to your users
   - **Authentication**: SSH keys (recommended) or Password
   - **Hostname**: `converge-api`

3. **Create Droplet** and note the IP address

### Step 2: Initial Server Setup

```bash
# SSH into your droplet
ssh root@YOUR_DROPLET_IP

# Update system packages
apt update && apt upgrade -y

# Install required packages
apt install -y python3.11 python3.11-venv python3-pip nginx certbot python3-certbot-nginx git

# Create application user
useradd -m -s /bin/bash converge
usermod -aG sudo converge

# Create application directory
mkdir -p /var/www/converge
chown -R converge:converge /var/www/converge
```

### Step 3: Clone and Setup Application

```bash
# Switch to application user
su - converge

# Navigate to application directory
cd /var/www/converge

# Clone repository
git clone https://github.com/vladimirkovacevic/conVerge.git .

# Create Python virtual environment
cd backend
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

```bash
# Create .env file in project root (/var/www/converge/.env)
cd /var/www/converge
nano .env
```

Add the following:
```bash
# OpenRouter API Configuration
OPENROUTER_API_KEY=sk-or-v1-your-actual-api-key-here

# Default LLM Model
DEFAULT_MODEL=meta-llama/llama-3.2-3b-instruct:free

# CORS Origins (IMPORTANT: Add your Vercel domain)
CORS_ORIGINS=https://your-app.vercel.app,https://your-app-vladimirkovacevic.vercel.app
```

**Save and exit** (Ctrl+X, Y, Enter)

### Step 5: Setup Systemd Service

```bash
# Exit from converge user back to root
exit

# Copy systemd service file
cp /var/www/converge/backend/converge.service /etc/systemd/system/

# Edit the service file if needed (check paths)
nano /etc/systemd/system/converge.service

# Reload systemd
systemctl daemon-reload

# Enable and start service
systemctl enable converge
systemctl start converge

# Check status
systemctl status converge
```

**Expected output**: Service should be `active (running)`

### Step 6: Configure Nginx Reverse Proxy

```bash
# Copy nginx configuration
cp /var/www/converge/backend/nginx-converge.conf /etc/nginx/sites-available/converge

# Edit configuration
nano /etc/nginx/sites-available/converge
```

**Update these lines:**
- Replace `api.yourdomain.com` with your actual domain
- Replace `https://your-app.vercel.app` with your Vercel URL

```bash
# Test nginx configuration
nginx -t

# If you DON'T have a domain yet, use IP-only config:
nano /etc/nginx/sites-available/converge-ip
```

**IP-only configuration** (temporary, until you get SSL):
```nginx
server {
    listen 80;
    server_name YOUR_DROPLET_IP;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # CORS headers
        add_header Access-Control-Allow-Origin "*" always;
        add_header Access-Control-Allow-Methods "GET, POST, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type" always;
    }
}
```

```bash
# Enable site
ln -s /etc/nginx/sites-available/converge-ip /etc/nginx/sites-enabled/

# Remove default site
rm /etc/nginx/sites-enabled/default

# Restart nginx
systemctl restart nginx

# Check nginx status
systemctl status nginx
```

### Step 7: Setup SSL (Optional but Recommended)

**Only if you have a domain:**

```bash
# Point your domain's A record to your droplet IP first!
# Then run:

certbot --nginx -d api.yourdomain.com

# Follow the prompts
# Certbot will automatically configure SSL
```

### Step 8: Configure Firewall

```bash
# Allow OpenSSH
ufw allow OpenSSH

# Allow HTTP and HTTPS
ufw allow 'Nginx Full'

# Enable firewall
ufw enable

# Check status
ufw status
```

### Step 9: Verify Backend is Running

```bash
# Check service status
systemctl status converge

# Check if port 8001 is listening
ss -tlnp | grep 8001

# Test API endpoint
curl http://localhost:8001/health

# Expected response: {"status":"healthy"}

# Test from outside (replace with your IP or domain)
curl http://YOUR_DROPLET_IP/health
```

---

## Frontend Deployment (Vercel)

### Step 1: Install Vercel CLI

```bash
# On your local machine
npm install -g vercel
```

### Step 2: Configure Environment Variables

1. Create `.env.production` in `frontend/` directory:

```bash
cd frontend
nano .env.production
```

Add:
```bash
# Use your DigitalOcean IP or domain
VITE_API_URL=http://YOUR_DROPLET_IP

# OR with SSL:
# VITE_API_URL=https://api.yourdomain.com
```

### Step 3: Deploy to Vercel

```bash
# Navigate to frontend directory
cd frontend

# Login to Vercel
vercel login

# Deploy (first time)
vercel

# Follow prompts:
# - Link to existing project? No
# - Project name: converge (or your choice)
# - Directory: ./ (current directory)
# - Override settings? No

# Deploy to production
vercel --prod
```

### Step 4: Configure Environment Variables in Vercel Dashboard

1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Select your `converge` project
3. Go to **Settings** → **Environment Variables**
4. Add:
   - **Name**: `VITE_API_URL`
   - **Value**: `http://YOUR_DROPLET_IP` or `https://api.yourdomain.com`
   - **Environments**: Production ✅

5. Click **Save**

6. **Redeploy** from Deployments tab

### Step 5: Update CORS Origins

After deployment, Vercel will give you a URL like `https://converge-abc123.vercel.app`

**Update backend CORS settings:**

```bash
# SSH into your droplet
ssh root@YOUR_DROPLET_IP

# Edit .env file
nano /var/www/converge/.env
```

Update CORS_ORIGINS:
```bash
CORS_ORIGINS=https://converge-abc123.vercel.app,https://converge-vladimirkovacevic.vercel.app
```

```bash
# Restart backend service
systemctl restart converge
```

---

## Post-Deployment Configuration

### Update Nginx CORS Headers

```bash
# Edit nginx config
nano /etc/nginx/sites-available/converge

# Update CORS origin to match your Vercel URL:
add_header Access-Control-Allow-Origin "https://your-actual-vercel-url.vercel.app" always;

# Reload nginx
nginx -t && systemctl reload nginx
```

### Custom Domain Setup (Optional)

**For Vercel:**
1. Go to Project Settings → Domains
2. Add your custom domain (e.g., `app.yourdomain.com`)
3. Follow DNS configuration instructions

**Update environment variables:**
- Backend `.env`: Add new domain to `CORS_ORIGINS`
- Frontend: Update `VITE_API_URL` if using custom backend domain

---

## Monitoring & Maintenance

### Check Backend Logs

```bash
# View service logs
journalctl -u converge -f

# View nginx access logs
tail -f /var/log/nginx/converge-access.log

# View nginx error logs
tail -f /var/log/nginx/converge-error.log
```

### Restart Services

```bash
# Restart backend
systemctl restart converge

# Restart nginx
systemctl restart nginx
```

### Update Application

```bash
# SSH into droplet
ssh root@YOUR_DROPLET_IP

# Switch to converge user
su - converge

# Navigate to project
cd /var/www/converge

# Pull latest changes
git pull origin main

# Update Python dependencies
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Exit and restart service
exit
systemctl restart converge
```

### Monitor Resources

```bash
# Check memory usage
free -h

# Check disk usage
df -h

# Check CPU and processes
htop
```

---

## Troubleshooting

### Backend Issues

**Service won't start:**
```bash
# Check detailed logs
journalctl -u converge -n 50 --no-pager

# Common issues:
# 1. Port 8001 already in use
sudo lsof -i :8001
# Kill the process or change port in converge.service

# 2. Missing environment variables
cat /var/www/converge/.env
# Ensure OPENROUTER_API_KEY is set

# 3. Python dependencies missing
cd /var/www/converge/backend
source venv/bin/activate
pip install -r requirements.txt
```

**CORS errors in browser:**
```bash
# Check backend CORS settings
grep CORS_ORIGINS /var/www/converge/.env

# Must include your Vercel URL
# Update and restart:
systemctl restart converge
```

**WebSocket connection fails:**
```bash
# Check nginx WebSocket configuration
nginx -t

# Ensure these are present in nginx config:
# proxy_http_version 1.1;
# proxy_set_header Upgrade $http_upgrade;
# proxy_set_header Connection "upgrade";
```

### Frontend Issues

**API calls fail:**
1. Check browser console for errors
2. Verify `VITE_API_URL` in Vercel environment variables
3. Test backend directly: `curl https://api.yourdomain.com/health`
4. Check CORS headers in browser Network tab

**Environment variable not updating:**
```bash
# Redeploy on Vercel
cd frontend
vercel --prod
```

### Network Issues

**Can't reach backend from frontend:**
```bash
# Test from your local machine
curl http://YOUR_DROPLET_IP/health

# Check firewall
ufw status

# Check nginx is running
systemctl status nginx

# Check backend is running
systemctl status converge
```

---

## Quick Reference

### Important URLs

- **Backend Health**: `http://YOUR_DROPLET_IP/health`
- **Backend API Docs**: `http://YOUR_DROPLET_IP/docs`
- **Frontend**: `https://your-app.vercel.app`

### Important Files

- Backend env: `/var/www/converge/.env`
- Systemd service: `/etc/systemd/system/converge.service`
- Nginx config: `/etc/nginx/sites-available/converge`
- Application logs: `journalctl -u converge`

### Port Configuration

- **Backend HTTP**: 8001 (changed from 8000)
- **Nginx HTTP**: 80
- **Nginx HTTPS**: 443

### Restart Commands

```bash
# Restart backend
systemctl restart converge

# Restart nginx
systemctl restart nginx

# Restart both
systemctl restart converge nginx
```

---

## Security Best Practices

1. **Never commit `.env` files** - They're in `.gitignore`
2. **Use SSH keys** instead of passwords for droplet access
3. **Enable firewall** with `ufw`
4. **Setup SSL certificates** with Let's Encrypt (free)
5. **Keep system updated**: `apt update && apt upgrade`
6. **Monitor logs** regularly for suspicious activity
7. **Backup environment variables** in a secure password manager

---

## Cost Estimate

- **DigitalOcean Droplet**: $6/month (Basic - 1GB RAM)
- **Vercel**: Free (Hobby tier)
- **Domain**: ~$12/year (optional)
- **SSL Certificate**: Free (Let's Encrypt)

**Total**: ~$6-7/month

---

## Support & Resources

- [DigitalOcean Documentation](https://docs.digitalocean.com/)
- [Vercel Documentation](https://vercel.com/docs)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [Let's Encrypt](https://letsencrypt.org/)

---

**Deployment checklist:**
- [ ] DigitalOcean droplet created
- [ ] Backend service running on port 8001
- [ ] Nginx configured and running
- [ ] SSL certificate installed (if using domain)
- [ ] Frontend deployed to Vercel
- [ ] Environment variables configured
- [ ] CORS origins updated
- [ ] Test API connection from frontend
- [ ] Test WebSocket streaming
- [ ] Monitor logs for errors

**Your deployment is complete! 🚀**
