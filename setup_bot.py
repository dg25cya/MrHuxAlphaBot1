#!/usr/bin/env python3
MR HUX Alpha Bot Setup Script
This script helps you configure your bot for free deployment.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def create_env_file():
  Create a .env file with required configuration."
    env_content =# MR HUX Alpha Bot Environment Configuration
# Fill in your actual values below

# Telegram Bot Configuration (REQUIRED)
TELEGRAM_API_ID=your_telegram_api_id_here
TELEGRAM_API_HASH=your_telegram_api_hash_here
BOT_TOKEN=your_bot_token_here
OUTPUT_CHANNEL_ID=your_output_channel_id_here

# Admin Configuration
ADMIN_USER_IDS=123456789654321base Configuration
DATABASE_URL=sqlite:///mr_hux_alpha_bot.db

# Redis Configuration (optional, for caching and pub/sub)
REDIS_URL=redis://localhost:6379API Keys (optional but recommended for full functionality)
RUGCHECK_API_KEY=your_rugcheck_api_key
BIRDEYE_API_KEY=your_birdeye_api_key
DEXSCREENER_API_KEY=your_dexscreener_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key

# Social Media API Keys (optional)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=MR_HUX_Alpha_Bot/1DISCORD_TOKEN=your_discord_token
DISCORD_WEBHOOK_URL=your_discord_webhook_url
GITHUB_TOKEN=your_github_token

# X/Twitter API Keys (optional)
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_BEARER_TOKEN=your_twitter_bearer_token
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_SECRET=your_twitter_access_secret

# Application Settings
ENV=production
DEBUG=false
HOST=0.0ORT=800
LOG_LEVEL=INFO

# JWT Settings
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256WT_EXPIRATION_HOURS=24

# Rate Limiting
RATE_LIMIT_CALLS=100
RATE_LIMIT_PERIOD=60X_REQUESTS_PER_MINUTE=60AX_ALERTS_PER_HOUR=10

# Token Monitoring Thresholds
PRICE_ALERT_THRESHOLD=50VOLUME_ALERT_THRESHOLD=10HOLDER_ALERT_THRESHOLD=100SOCIAL_ALERT_THRESHOLD=200
MAX_ACCEPTABLE_TAX=100WHALE_HOLDER_THRESHOLD=5.0
MIN_LIQUIDITY_USD=500
MAX_PRICE_IMPACT=30
MIN_LP_LOCK_DAYS=180

# AI/ML Settings
MIN_CONFIDENCE_THRESHOLD=0.7ENTIMENT_THRESHOLD=0.3RISK_CACHE_MINUTES=30MAX_CACHE_SIZE=1000

# Output Settings
MAX_MESSAGE_LENGTH=200MAX_ATTACHMENTS=10base Pool Settings
DB_POOL_SIZE=20DB_MAX_OVERFLOW=10DB_POOL_TIMEOUT=30    
    with open('.env', w) asf:
        f.write(env_content)
    
    print("✅ Created .env file")
    print("📝 Please edit .env file with your actual credentials")

def create_railway_config():
    "Railway deployment configuration."""
    railway_config = [object Object]       $schema": "https://railway.app/railway.schema.json",
 build: {        builder": NIXPACKS"
        },
  deploy: {           startCommand": python web_server.py",
            restartPolicyType": "ON_FAILURE",
           restartPolicyMaxRetries": 10     }
    }
    
    with open(railway.json', was f:
        json.dump(railway_config, f, indent=2)
    
    print(✅ Created railway.json configuration)

def create_procfile():
  Create a Procfile for deployment."""
    procfile_content = "web: python web_server.py"
    
    with open('Procfile', w) asf:
        f.write(procfile_content)
    
    print("✅ Created Procfile")

def create_runtime_txt():
    "eate a runtime.txt for Python version."""
    runtime_content = "python-30.11    
    with open('runtime.txt', w) asf:
        f.write(runtime_content)
    
    print(✅ Created runtime.txt")

def check_dependencies():
    ""Check if required dependencies are installed.""
    try:
        import fastapi
        import telethon
        import sqlalchemy
        import loguru
        print("✅ All required dependencies are available")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False

def install_dependencies():
    "uired dependencies."""
    print("📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m,pip", install-r",requirements.txt"], check=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False
    returntruedef setup_database():nitialize database.print("🗄️ Setting up database...")
    try:
        from src.database import init_db
        import asyncio
        asyncio.run(init_db())
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False
    return True

def main():ain setup function.""    print("🚀 MR HUX Alpha Bot Setup)
    print(= * 50)
    
    # Create configuration files
    create_env_file()
    create_railway_config()
    create_procfile()
    create_runtime_txt()
    
    # Check and install dependencies
    if not check_dependencies():
        if not install_dependencies():
            print("❌ Setup failed - could not install dependencies")
            return
    
    # Setup database
    if not setup_database():
        print("❌ Setup failed - could not initialize database")
        return
    
    print("\n" + "=" * 50)
    print(✅ Setup completed successfully!") 
    print("\n📋 Next steps:")
    print(1. Edit .env file with your Telegram credentials")
    print("2. Get your Telegram API credentials from @BotFather")
    print("3. Deploy to Railway.app for free hosting")
    print(4. Run python bot.py to start the bot locally")
    print(5. Run python web_server.py to start the web server")
    
    print(n🔗 Useful links:")
    print("- Telegram Bot API: https://core.telegram.org/bots/api")
    print("- Railway.app: https://railway.app")
    print("- Project documentation: README.md)if __name__ == "__main__":
    main() 