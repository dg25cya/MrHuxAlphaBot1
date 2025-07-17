#!/usr/bin/env python3
MR HUX Alpha Bot - Real-time Setup Script
Configure your bot for real-time operation with all API keys.
"""

import os
import json

def create_env_file():
    """Create .env file with all configuration."""
    env_content = # Application Environment
ENV=production
DEBUG=false
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# Telegram Configuration
TELEGRAM_API_ID=21258315
TELEGRAM_API_HASH=9554fd10ebb0c5f2ed1a0c129dc93acc
BOT_TOKEN=7869865637:AAEP0uBKLS1Z1UcxfsK9ADuGVf0pi5e7zpE
OUTPUT_CHANNEL_ID=-1001947726359
ADMIN_USER_IDS=1234567890,987654321

# Database Configuration
DATABASE_URL=sqlite:///mr_hux_alpha_bot.db
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30

# API Keys
RUGCHECK_API_KEY=rc_live_sB4tPx9mJkL5nQ7v
BIRDEYE_API_KEY=be_live_fH2jN8wRtY6mX4cV
PUMPFUN_API_KEY=pf_live_kR9vB4nM7wL2sX5j
BONKFUN_API_KEY=bf_live_tG5hP8mK3nJ6wQ9x
DEEPSEEK_API_KEY=sk-261ba78ca31c494c96b09c0981976b2f

# Real-time Configuration
MONITORING_INTERVAL=30
ALERT_COOLDOWN=60
MAX_DAILY_ALERTS=1000
ENABLE_REALTIME=true
WEBSOCKET_ENABLED=true

# JWT Settings
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Rate Limiting
RATE_LIMIT_CALLS=100
RATE_LIMIT_PERIOD=60
MAX_REQUESTS_PER_MINUTE=60
MAX_ALERTS_PER_HOUR=10

# Token Monitoring Thresholds
PRICE_ALERT_THRESHOLD=5.0
VOLUME_ALERT_THRESHOLD=100.0
HOLDER_ALERT_THRESHOLD=10.0
SOCIAL_ALERT_THRESHOLD=200.0
MAX_ACCEPTABLE_TAX=10.0
WHALE_HOLDER_THRESHOLD=5.0
MIN_LIQUIDITY_USD=50000
MAX_PRICE_IMPACT=3.0
MIN_LP_LOCK_DAYS=180

# AI/ML Settings
MIN_CONFIDENCE_THRESHOLD=0.7
SENTIMENT_THRESHOLD=0.3
RISK_CACHE_MINUTES=30
MAX_CACHE_SIZE=1000

# Output Settings
MAX_MESSAGE_LENGTH=2000
MAX_ATTACHMENTS=10

# Real-time Monitoring
ENABLE_LIVE_SCANNING=true
SCAN_INTERVAL_SECONDS=30
MAX_CONCURRENT_SCANS=5
ENABLE_PUSH_NOTIFICATIONS=true
ENABLE_WEBSOCKET_UPDATES=true
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env file with real-time configuration")

def update_railway_config():
    """Update Railway configuration for real-time deployment."""
    railway_config = [object Object]       $schema": "https://railway.app/railway.schema.json",
 build: {        builder": NIXPACKS"
        },
  deploy: {           startCommand": python start_bot_and_web.py",
            restartPolicyType": "ON_FAILURE",
           restartPolicyMaxRetries": 10     }
    }
    
    with open(railway.json', was f:
        json.dump(railway_config, f, indent=2)
    
    print("✅ Updated railway.json for real-time deployment")

def create_procfile():
    """Create Procfile for real-time deployment."""
    procfile_content = "web: python start_bot_and_web.py"
    
    with open('Procfile', w) asf:
        f.write(procfile_content)
    
    print("✅ Created Procfile for real-time deployment")

def test_configuration():
    """Test the configuration."""
    print("🧪 Testing configuration...")
    try:
        from src.config.settings import get_settings
        settings = get_settings()
        print(f"✅ Settings loaded: {settings.env}")
        print(f"✅ Bot token: {settings.bot_token[:10]}...")
        print(f"✅ API ID: {settings.telegram_api_id}")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 MR HUX Alpha Bot - Real-time Setup")
    print("=" * 50)
    
    # Create configuration files
    create_env_file()
    update_railway_config()
    create_procfile()
    
    print("\n" + "=" * 50)
    print("✅ Real-time setup completed!")
    print("\n📋 Next steps:")
    print("1. Commit and push to GitHub")
    print("2. Deploy to Railway.app")
    print("3. Your bot will be live and real-time!")
    
    # Test configuration
    if test_configuration():
        print("\n🎉 Everything is ready for real-time deployment!")
    else:
        print("\n⚠️  Some configuration issues found. Please check the errors above.")

if __name__ == "__main__":
    main() 