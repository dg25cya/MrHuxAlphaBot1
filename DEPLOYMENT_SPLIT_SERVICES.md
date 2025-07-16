# MR HUX Alpha Bot - Split Services Deployment Guide

## Overview

The application has been split into two separate services:

1. **Bot Service** (`bot.py`) - Handles Telegram bot functionality, message monitoring, and alerts
2. **Web Server Service** (`web_server.py`) - Handles the web dashboard and API endpoints

## Deployment Options

### Option 1: Render.com (Recommended)

#### Web Server Service
1. Create a new Web Service on Render
2. Connect your GitLab repository
3. Set the following environment variables:
   - `PORT` (Render will set this automatically)
   - `BOT_TOKEN` - Your Telegram bot token
   - `TELEGRAM_API_ID` - Your Telegram API ID
   - `TELEGRAM_API_HASH` - Your Telegram API hash
   - `OUTPUT_CHANNEL_ID` - Your output channel ID
   - All other API keys as needed

4. Build Command: `pip install -r requirements.txt`
5. Start Command: `python web_server.py`

#### Bot Service
1. Create a new Background Worker on Render
2. Connect the same GitLab repository
3. Set the same environment variables as above
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `python bot.py`

### Option 2: Railway.app

#### Web Server Service
1. Create a new service on Railway
2. Connect your GitLab repository
3. The `railway.json` file is already configured for the web server
4. Set environment variables in Railway dashboard
5. Deploy

#### Bot Service
1. Create a second service on Railway
2. Connect the same repository
3. Override the start command to: `python bot.py`
4. Set environment variables
5. Deploy

### Option 3: Local Development

#### Running Both Services Locally

Terminal 1 (Web Server):
```bash
python web_server.py
```

Terminal 2 (Bot Service):
```bash
python bot.py
```

## Environment Variables

Both services need the same environment variables:

```bash
# Telegram Configuration
BOT_TOKEN=your_bot_token_here
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here
OUTPUT_CHANNEL_ID=your_channel_id_here

# Database
DATABASE_URL=sqlite:///mr_hux_alpha_bot.db

# API Keys (optional)
BIRDEYE_API_KEY=your_birdeye_key
DEXSCREENER_API_KEY=your_dexscreener_key
RUGCHECK_API_KEY=your_rugcheck_key

# Other settings
LOG_LEVEL=INFO
ENV=production
```

## Service Communication

- Both services share the same SQLite database
- The bot service monitors Telegram groups and writes alerts to the database
- The web server reads from the database to display the dashboard
- No direct communication between services is needed

## Monitoring

### Web Server Health Check
- Endpoint: `GET /health`
- Returns service status and database connectivity

### Bot Service Monitoring
- Check logs for bot activity
- Monitor database for new alerts
- Verify Telegram client connection

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   - Ensure only one service is using the web port
   - Check for conflicting processes

2. **Database Locked**
   - SQLite may lock if both services access simultaneously
   - Consider using PostgreSQL for production

3. **Telegram Session Issues**
   - Delete session files if authentication fails
   - Ensure API credentials are correct

4. **Missing Dependencies**
   - Run `pip install -r requirements.txt` for both services

### Logs

- Web Server: Check Render/Railway logs for web service
- Bot Service: Check Render/Railway logs for bot service
- Both services log to stdout/stderr

## Benefits of Split Services

1. **Independent Scaling** - Scale web and bot separately
2. **Better Resource Management** - Each service uses only what it needs
3. **Easier Debugging** - Isolate issues to specific services
4. **Improved Reliability** - One service failure doesn't affect the other
5. **Render Compatibility** - Proper port detection for web service

## Migration from Single Service

If migrating from the single service setup:

1. Stop the old service
2. Deploy both new services
3. Verify both services are running
4. Test bot functionality and web dashboard
5. Monitor logs for any issues 