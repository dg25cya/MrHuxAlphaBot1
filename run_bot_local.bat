@echo off
echo 🚀 MR HUX Alpha Bot - Local FREE Setup
echo ======================================

echo.
echo 📦 Installing dependencies...
pip install -r requirements.txt

echo.
echo 🗄️ Setting up database...
python -c "from src.database import init_db; import asyncio; asyncio.run(init_db())"

echo.
echo 🤖 Starting your bot locally (FREE)...
echo.
echo ✅ Your bot will be available at:
echo    - Web Dashboard: http://localhost:8000
echo    - Telegram Bot: Check your bot token
echo.
echo ⚡ Real-time monitoring is ACTIVE
echo 🔍 Scanning every 30 seconds
echo 📊 All API keys are configured
echo.
echo Press Ctrl+C to stop the bot
echo.

python start_bot_and_web.py

pause 