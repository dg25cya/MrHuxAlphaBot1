@echo off
echo Creating .env file for MR HUX Alpha Bot...

echo # Application Environment > .env
echo ENV=production >> .env
echo DEBUG=false >> .env
echo HOST=0.0.0.0 >> .env
echo PORT=8000 >> .env
echo LOG_LEVEL=INFO >> .env
echo. >> .env
echo # Telegram Configuration >> .env
echo TELEGRAM_API_ID=21258315 >> .env
echo TELEGRAM_API_HASH=9554fd10ebb0c5f2ed1a0c129dc93acc >> .env
echo BOT_TOKEN=7869865637:AAEP0uBKLS1Z1UcxfsK9ADuGVf0pi5e7zpE >> .env
echo OUTPUT_CHANNEL_ID=-1001947726359 >> .env
echo ADMIN_USER_IDS=1234567890,987654321 >> .env
echo. >> .env
echo # API Keys >> .env
echo RUGCHECK_API_KEY=rc_live_sB4tPx9mJkL5nQ7v >> .env
echo BIRDEYE_API_KEY=be_live_fH2jN8wRtY6mX4cV >> .env
echo PUMPFUN_API_KEY=pf_live_kR9vB4nM7wL2sX5j >> .env
echo BONKFUN_API_KEY=bf_live_tG5hP8mK3nJ6wQ9x >> .env
echo DEEPSEEK_API_KEY=sk-261ba78ca31c494c96b09c0981976b2f >> .env
echo. >> .env
echo # Real-time Configuration >> .env
echo MONITORING_INTERVAL=30 >> .env
echo ALERT_COOLDOWN=60 >> .env
echo MAX_DAILY_ALERTS=1000 >> .env
echo ENABLE_REALTIME=true >> .env
echo WEBSOCKET_ENABLED=true >> .env
echo. >> .env
echo # JWT Settings >> .env
echo JWT_SECRET=your-super-secret-jwt-key-change-this-in-production >> .env
echo JWT_ALGORITHM=HS256 >> .env
echo JWT_EXPIRATION_HOURS=24 >> .env

echo ✅ .env file created successfully!
echo.
echo 🚀 Your bot is now configured for real-time operation!
echo 📋 Next steps:
echo 1. Commit and push to GitHub
echo 2. Deploy to Railway.app
echo 3. Your bot will be live and real-time!
pause 