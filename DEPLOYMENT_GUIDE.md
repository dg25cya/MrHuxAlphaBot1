# MR HUX Alpha Bot - Free Deployment Guide

## 🚀 Quick Start (5nutes)

### 1. Get Telegram Bot Credentials
1*Create a bot with @BotFather on Telegram**
   - Message @BotFather on Telegram
   - Send `/newbot`
   - Choose a name and username for your bot
   - Save the bot token

2. **Get API credentials**
   - Go to https://my.telegram.org/apps
   - Create a new application
   - Save the `api_id` and `api_hash`

### 2. Set Up Environment Variables

Create a `.env` file in your project root:

```bash
# Telegram Bot Configuration (REQUIRED)
TELEGRAM_API_ID=your_telegram_api_id_here
TELEGRAM_API_HASH=your_telegram_api_hash_here
BOT_TOKEN=your_bot_token_here
OUTPUT_CHANNEL_ID=your_output_channel_id_here

# Admin Configuration
ADMIN_USER_IDS=123456789654321base Configuration
DATABASE_URL=sqlite:///mr_hux_alpha_bot.db

# Application Settings
ENV=production
DEBUG=false
HOST=0.0ORT=800
LOG_LEVEL=INFO

# JWT Settings
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256WT_EXPIRATION_HOURS=24
```

### 3. Deploy to Railway (Free)1ign up for Railway.app**
   - Go to https://railway.app
   - Sign up with GitHub2 **Deploy your bot**
   - Connect your GitHub repository
   - Railway will automatically detect the configuration
   - Add your environment variables in Railway dashboard
3**Get your bot URL**
   - Railway will provide a public URL
   - Your bot will be accessible at that URL

## 🔧 Local Development

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Locally

```bash
# Start the web server
python web_server.py

# Start the bot (in another terminal)
python bot.py

# Or run both together
python start_bot_and_web.py
```

## 📊 Bot Features

### Commands Available

- `/start` - Welcome message and main menu
- `/sources` - View monitored sources
- `/scanners` - Check scanner health
- `/status` - Bot status and uptime
- `/whereami` - Show current configuration

### Monitoring Sources

- **Telegram Groups** - Monitor specific groups for token mentions
- **Pump.fun** - Track new token launches
- **Dexscreener** - Monitor trading activity
- **Birdeye** - Price and volume data
- **Bonkfun** - Social sentiment analysis

### Alert Types

- 🚨 **Price Alerts** - Significant price movements
- 📈 **Volume Spikes** - Unusual trading volume
- 👥 **Holder Changes** - New holders joining
- 💬 **Social Mentions** - Increased social activity
- ⚠️ **Risk Warnings** - Potential rug pulls

## 🛠️ Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_API_ID` | Yes | Your Telegram API ID |
| `TELEGRAM_API_HASH` | Yes | Your Telegram API Hash |
| `BOT_TOKEN` | Yes | Your bot token from @BotFather |
| `OUTPUT_CHANNEL_ID` | Yes | Channel ID for alerts |
| `ADMIN_USER_IDS` | No | Comma-separated admin user IDs |
| `DATABASE_URL` | No | Database connection string |
| `REDIS_URL` | No | Redis for caching (optional) |

### API Keys (Optional)

For full functionality, add these API keys:

- `RUGCHECK_API_KEY` - Token safety analysis
- `BIRDEYE_API_KEY` - Market data
- `DEXSCREENER_API_KEY` - Trading data
- `DEEPSEEK_API_KEY` - AI analysis

## 🔍 Troubleshooting

### Common Issues

1. **Bot not responding**
   - Check if bot token is correct
   - Verify API credentials
   - Check bot permissions

2. **Database errors**
   - Ensure database file is writable
   - Check database URL format
   - Run database migrations

3. **Deployment issues**
   - Verify environment variables in Railway
   - Check build logs for errors
   - Ensure all dependencies are in requirements.txt

### Logs

Check logs for debugging:

```bash
# Local logs
tail -f logs/sma_telebot.log

# Railway logs
# Check in Railway dashboard
```

## 📈 Monitoring & Analytics

### Built-in Metrics

- Message processing rate
- Token detection accuracy
- Alert generation statistics
- System uptime and health

### Dashboard

Access the web dashboard at your deployment URL for:
- Real-time monitoring
- Source management
- Alert configuration
- System statistics

## 🔒 Security

### Best Practices
1 **Never commit `.env` files**2. **Use strong JWT secrets**
3. **Limit admin access**
4. **Regular security updates**
5. **Monitor for unusual activity**

### Rate Limiting

The bot includes built-in rate limiting:
- 60 requests per minute per API
- 10lerts per hour per source
- Automatic backoff on errors

## 🚀 Advanced Features

### Custom Alerts

Configure custom alert thresholds:

```bash
PRICE_ALERT_THRESHOLD=50VOLUME_ALERT_THRESHOLD=1000HOLDER_ALERT_THRESHOLD=100SOCIAL_ALERT_THRESHOLD=200.0
```

### AI Analysis

Enable AI-powered analysis:

```bash
MIN_CONFIDENCE_THRESHOLD=0.7ENTIMENT_THRESHOLD=0.3### Multi-language Support

The bot supports multiple languages for token analysis and alerts.

## 📞 Support

### Getting Help

1. **Check the logs** for error messages
2. **Review this guide** for common solutions
3. **Check the documentation** in the DOCS/ folder
4 **Open an issue** on GitHub

### Community

- Join our Telegram community for support
- Share your bot configurations
- Get help from other users

## 🎯 Next Steps1 **Deploy your bot** using this guide
2. **Add monitoring sources** via the bot commands
3. **Configure alerts** for your needs
4. **Monitor and optimize** based on usage
5ale up** as needed

---

**Happy hunting! 🚀**

Your MR HUX Alpha Bot is now ready to catch those alpha signals! 