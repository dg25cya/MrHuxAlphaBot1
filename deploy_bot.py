#!/usr/bin/env python3pha Bot Deployment Script
Simple script to get your bot running for free.
"""

import os
import sys
import subprocess
import json

def create_env_template():
  te a .env template file."
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

# Application Settings
ENV=production
DEBUG=false
HOST=0.0ORT=800
LOG_LEVEL=INFO

# JWT Settings
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256WT_EXPIRATION_HOURS=24    
    with open('.env', w) asf:
        f.write(env_content)
    
    print("✅ Created .env file")
    print("📝 Please edit .env file with your actual credentials")

def update_railway_config():
   lway configuration for deployment."""
    railway_config = [object Object]       $schema": "https://railway.app/railway.schema.json",
 build: {        builder": NIXPACKS"
        },
  deploy: {           startCommand": python web_server.py",
            restartPolicyType": "ON_FAILURE",
           restartPolicyMaxRetries": 10     }
    }
    
    with open(railway.json', was f:
        json.dump(railway_config, f, indent=2)
    
    print(✅ Updated railway.json configuration)

def update_procfile():
    pdate Procfile for deployment."""
    procfile_content = "web: python web_server.py"
    
    with open('Procfile', w) asf:
        f.write(procfile_content)
    
    print("✅ Updated Procfile")

def update_runtime():
   Update runtime.txt for Python version."""
    runtime_content = "python-30.11    
    with open('runtime.txt', w) asf:
        f.write(runtime_content)
    
    print(✅ Updated runtime.txt)def check_telegram_credentials():
    ""Check if Telegram credentials are set.
    required_vars =TELEGRAM_API_ID,TELEGRAM_API_HASH', 'BOT_TOKEN']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)})
        print("📝 Please set these in your .env file or environment")
        return False
    
    print("✅ All required Telegram credentials are set)
    return True

def run_local_test():
un a local test to check if everything works."""
    print("🧪 Running local test...")
    try:
        # Test database initialization
        from src.database import init_db
        import asyncio
        asyncio.run(init_db())
        print("✅ Database test passed")
        
        # Test settings loading
        from src.config.settings import get_settings
        settings = get_settings()
        print(f✅ Settings loaded: {settings.env}")
        
        return True
    except Exception as e:
        print(f"❌ Local test failed: {e}")
        return False

def main():
    n deployment setup function.""    print("🚀 MR HUX Alpha Bot Deployment Setup)
    print(= * 50)
    
    # Create/update configuration files
    create_env_template()
    update_railway_config()
    update_procfile()
    update_runtime()
    
    print("\n" + "=" *50    print(📋 Next steps:")
    print(1. Edit .env file with your Telegram credentials")
    print("2. Get your Telegram API credentials from @BotFather")
    print("3. Deploy to Railway.app for free hosting")
    print("4python web_server.py to start locally")
    
    print(n🔗 Useful links:")
    print("- Telegram Bot API: https://core.telegram.org/bots/api")
    print("- Railway.app: https://railway.app")
    
    # Check if credentials are set
    if check_telegram_credentials():
        print("\n🧪 Running local test...")
        if run_local_test():
            print("✅ Everything looks good! Your bot is ready to deploy.")
        else:
            print("❌ Some issues found. Please check the errors above.")
    else:
        print("\n⚠️  Please set your Telegram credentials before deploying.)if __name__ == "__main__":
    main() 