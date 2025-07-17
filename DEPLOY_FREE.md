# 🆓 FREE Deployment Guide for MR HUX Alpha Bot

## 🚀 **Option 1: Render.com (RECOMMENDED - 100% FREE)**

### Step 1: Sign up for Render
1. Go to https://render.com
2. Sign up with your GitHub account
3. **FREE tier includes:**
   - 750 hours/month
   - Auto-deploy from GitHub
   - Custom domains
   - SSL certificates

### Step 2: Deploy Your Bot
1. Click "New +" → "Web Service"
2. Connect your GitHub repository: `dg25cya/MrHuxAlphaBot1`
3. Configure:
   - **Name**: `mr-hux-alpha-bot`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python start_bot_and_web.py`

### Step 3: Add Environment Variables
In Render dashboard, add these variables:
```
ENV=production
DEBUG=false
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
TELEGRAM_API_ID=21258315
TELEGRAM_API_HASH=9554fd10ebb0c5f2ed1a0c129dc93acc
BOT_TOKEN=7869865637:AAEP0uBKLS1Z1UcxfsK9ADuGVf0pi5e7zpE
OUTPUT_CHANNEL_ID=-1001947726359
ADMIN_USER_IDS=1234567890,987654321
RUGCHECK_API_KEY=rc_live_sB4tPx9mJkL5nQ7v
BIRDEYE_API_KEY=be_live_fH2jN8wRtY6mX4cV
PUMPFUN_API_KEY=pf_live_kR9vB4nM7wL2sX5j
BONKFUN_API_KEY=bf_live_tG5hP8mK3nJ6wQ9x
DEEPSEEK_API_KEY=sk-261ba78ca31c494c96b09c0981976b2f
MONITORING_INTERVAL=30
ALERT_COOLDOWN=60
MAX_DAILY_ALERTS=1000
ENABLE_REALTIME=true
WEBSOCKET_ENABLED=true
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

### Step 4: Deploy!
- Click "Create Web Service"
- Render will build and deploy automatically
- Your bot will be live at: `https://your-app-name.onrender.com`

---

## 🚀 **Option 2: Railway with Free Credits**

### Step 1: Get Free Credits
1. Go to https://railway.app
2. Sign up with GitHub
3. **You get $5 free credits** (about 500 hours)
4. Enough to run your bot for weeks!

### Step 2: Deploy
1. Click "New Project" → "Deploy from GitHub repo"
2. Select: `dg25cya/MrHuxAlphaBot1`
3. Add environment variables (same as above)
4. Deploy!

---

## 🚀 **Option 3: Local Development (FREE)**

### Run Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Start the bot
python start_bot_and_web.py
```

Your bot will run on: `http://localhost:8000`

---

## 🎯 **Your Bot Features (All FREE):**

- ⚡ **Real-time monitoring** (30-second intervals)
- 🤖 **Telegram bot** with button interface
- 📊 **Web dashboard** for monitoring
- 🔍 **Multi-source scanning** (Pump.fun, Dexscreener, etc.)
- 🧠 **AI analysis** and sentiment detection
- 📈 **Advanced analytics** and risk assessment
- 🌐 **WebSocket support** for live updates

## 🔧 **Troubleshooting**

### If Render fails:
1. Check build logs
2. Ensure all dependencies are in `requirements.txt`
3. Verify environment variables are set correctly

### If Railway fails:
1. Use the free credits wisely
2. Check the deployment logs
3. Verify your API keys are valid

## 📞 **Support**

- **Render Support**: https://render.com/docs
- **Railway Support**: https://docs.railway.app
- **Bot Documentation**: Check the DOCS/ folder

---

**🎉 Your bot will be live and real-time for FREE!** 