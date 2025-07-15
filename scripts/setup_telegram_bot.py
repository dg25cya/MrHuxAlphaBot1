#!/usr/bin/env python3
"""
Telegram Bot Setup Script
=========================

This script helps you set up your Telegram bot token and API credentials.

Steps to get your bot token:
1. Open Telegram and search for @BotFather
2. Send /newbot command
3. Follow the instructions to create your bot
4. Copy the bot token (looks like: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)
5. Get your API credentials from https://my.telegram.org/apps

"""

import os
import sys
import asyncio
from pathlib import Path
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.settings import get_settings

def print_setup_instructions():
    """Print setup instructions."""
    print("=" * 60)
    print("🤖 TELEGRAM BOT SETUP GUIDE")
    print("=" * 60)
    print()
    print("📋 STEP 1: Create a Bot with @BotFather")
    print("   1. Open Telegram and search for @BotFather")
    print("   2. Send /newbot command")
    print("   3. Choose a name for your bot (e.g., 'MR HUX Alpha Bot')")
    print("   4. Choose a username (must end with 'bot', e.g., 'mrhux_alpha_bot')")
    print("   5. Copy the bot token (looks like: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)")
    print()
    print("📋 STEP 2: Get API Credentials")
    print("   1. Go to https://my.telegram.org/apps")
    print("   2. Log in with your phone number")
    print("   3. Create a new application")
    print("   4. Copy the API ID and API Hash")
    print()
    print("📋 STEP 3: Update Your Configuration")
    print("   You need to create a .env file with these values:")
    print()
    print("   TELEGRAM_API_ID=your_api_id_here")
    print("   TELEGRAM_API_HASH=your_api_hash_here")
    print("   BOT_TOKEN=your_bot_token_here")
    print()
    print("=" * 60)

async def test_current_credentials():
    """Test current credentials if they exist."""
    settings = get_settings()
    
    print("🔍 Testing current credentials...")
    print(f"   API ID: {settings.telegram_api_id}")
    print(f"   API Hash: {settings.telegram_api_hash[:10] if settings.telegram_api_hash else 'None'}...")
    print(f"   Bot Token: {settings.bot_token[:10] if settings.bot_token else 'None'}...")
    print()
    
    if not all([settings.telegram_api_id, settings.telegram_api_hash, settings.bot_token]):
        print("❌ Missing credentials! Please follow the setup guide above.")
        return False
    
    try:
        from telethon import TelegramClient
        from telethon.sessions import StringSession
        
        # Create client
        client = TelegramClient(
            StringSession(),
            settings.telegram_api_id,
            settings.telegram_api_hash
        )
        
        # Test connection
        print("🔄 Testing connection...")
        await client.start(bot_token=settings.bot_token)
        
        # Get bot info
        me = await client.get_me()
        print(f"✅ Successfully connected as: @{me.username}")
        print(f"   Bot ID: {me.id}")
        print(f"   Bot Name: {me.first_name}")
        
        await client.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print()
        print("🔧 This usually means:")
        print("   - Bot token is invalid or expired")
        print("   - API credentials are incorrect")
        print("   - Bot was deleted or banned")
        print()
        print("💡 Solution: Create a new bot with @BotFather")
        return False

def create_env_template():
    """Create a .env template file."""
    env_template = """# Telegram Bot Configuration
# ===========================

# Get these from https://my.telegram.org/apps
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here

# Get this from @BotFather on Telegram
BOT_TOKEN=your_bot_token_here

# Optional: Output channel ID (where bot will post alerts)
OUTPUT_CHANNEL_ID=your_channel_id_here

# Optional: Admin user IDs (comma-separated)
ADMIN_USER_IDS=your_user_id_here

# Database Configuration
DATABASE_URL=sqlite:///mr_hux_alpha_bot.db

# Application Settings
ENV=development
DEBUG=false
LOG_LEVEL=INFO
"""
    
    env_file = Path(".env")
    if env_file.exists():
        print("⚠️  .env file already exists!")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            return
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_template)
        print("✅ Created .env template file")
        print("📝 Please edit .env with your actual credentials")
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")

def main():
    """Main setup function."""
    print_setup_instructions()
    
    # Test current credentials
    asyncio.run(test_current_credentials())
    
    print()
    print("📝 Would you like to create a .env template file?")
    response = input("Create .env template? (Y/n): ")
    if response.lower() != 'n':
        create_env_template()
    
    print()
    print("🎯 Next steps:")
    print("   1. Follow the setup guide above")
    print("   2. Update your .env file with real credentials")
    print("   3. Run: python scripts/test_telegram.py")
    print("   4. If successful, run: python -m src.main")
    print()
    print("📞 Need help? Check the documentation in DOCS/ folder")

if __name__ == "__main__":
    main() 