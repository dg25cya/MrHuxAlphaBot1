# 🔑 MR HUX ALPHA BOT - COMPLETE API SETUP GUIDE

## 🚀 **QUICK START - ESSENTIAL SETUP**

### **1. TELEGRAM BOT SETUP (REQUIRED)**
This is the **most important** setup - your bot won't work without it!

#### **Step 1: Create Telegram Bot**
1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Choose a name: `MR HUX ALPHA BOT`
4. Choose a username: `MrHuAlphaBotPlays` (or your choice)
5. **Save the bot token** - it looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

#### **Step 2: Get Telegram API Credentials**
1. Go to https://my.telegram.org/
2. Log in with your phone number
3. Go to "API Development Tools"
4. Create a new application:
   - **App title:** MR HUX ALPHA BOT
   - **Short name:** mrhuxbot
   - **Platform:** Desktop
   - **Description:** Alpha hunting bot for crypto monitoring
5. **Save both API ID and API Hash**

#### **Step 3: Set Environment Variables**
Create a `.env` file in your project root:

```env
# TELEGRAM (REQUIRED)
BOT_TOKEN=your_bot_token_here
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here

# Optional: Session name
TELEGRAM_SESSION_NAME=mrhux_session
```

---

## 🔗 **EXTERNAL API SETUP (OPTIONAL BUT RECOMMENDED)**

### **2. REDDIT API SETUP**
For monitoring Reddit crypto communities.

#### **Step 1: Create Reddit App**
1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Fill in:
   - **Name:** MR HUX Alpha Bot
   - **Type:** Script
   - **Description:** Crypto alpha hunting bot
   - **About URL:** (leave blank)
   - **Redirect URI:** http://localhost:8080
4. **Save the credentials**

#### **Step 2: Add to Environment**
```env
# REDDIT API
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=MR_HUX_Alpha_Bot/1.0
```

---

### **3. X/TWITTER API SETUP**
For posting alerts to X/Twitter.

#### **Step 1: Apply for Twitter API**
1. Go to https://developer.twitter.com/
2. Sign up for a developer account
3. Apply for API access (Basic or Pro)
4. Create a new app

#### **Step 2: Get API Keys**
1. In your Twitter app dashboard, go to "Keys and Tokens"
2. Generate:
   - **API Key and Secret**
   - **Bearer Token**
   - **Access Token and Secret**

#### **Step 3: Add to Environment**
```env
# X/TWITTER API
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_BEARER_TOKEN=your_bearer_token_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_SECRET=your_access_secret_here
```

---

### **4. DISCORD WEBHOOK SETUP**
For sending alerts to Discord channels.

#### **Step 1: Create Discord Webhook**
1. Go to your Discord server
2. Right-click on the channel you want alerts in
3. Select "Edit Channel" → "Integrations" → "Webhooks"
4. Click "New Webhook"
5. Name it: "MR HUX Alpha Bot"
6. **Copy the webhook URL**

#### **Step 2: Add to Environment**
```env
# DISCORD WEBHOOK
DISCORD_WEBHOOK_URL=your_webhook_url_here
```

---

### **5. GITHUB API SETUP**
For monitoring crypto project repositories.

#### **Step 1: Create GitHub Token**
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes:
   - `repo` (for private repos)
   - `public_repo` (for public repos)
   - `read:org` (for organization repos)
4. **Copy the token**

#### **Step 2: Add to Environment**
```env
# GITHUB API
GITHUB_TOKEN=your_github_token_here
```

---

### **6. SOLANA/BONK API SETUP**
For monitoring Solana tokens and Bonk activity.

#### **Step 1: Get API Keys**
1. **Birdeye API** (for Solana data):
   - Go to https://birdeye.so/
   - Sign up for API access
   - Get your API key

2. **Bonk API** (if available):
   - Check Bonk documentation for API access

#### **Step 2: Add to Environment**
```env
# SOLANA/BONK APIs
BIRDEYE_API_KEY=your_birdeye_api_key_here
BONK_API_KEY=your_bonk_api_key_here
```

---

### **7. RSS FEED SETUP**
For monitoring crypto news feeds.

#### **Step 1: Popular RSS Feeds**
Add these to your bot configuration:
- CoinDesk: `https://coindesk.com/arc/outboundfeeds/rss/`
- CoinTelegraph: `https://cointelegraph.com/rss`
- CryptoSlate: `https://cryptoslate.com/feed/`
- Decrypt: `https://decrypt.co/feed`

#### **Step 2: Add to Environment**
```env
# RSS FEEDS (comma-separated)
RSS_FEEDS=https://coindesk.com/arc/outboundfeeds/rss/,https://cointelegraph.com/rss,https://cryptoslate.com/feed/
```

---

## ⚙️ **ADVANCED CONFIGURATION**

### **8. DATABASE CONFIGURATION**
```env
# DATABASE (SQLite by default)
DATABASE_URL=sqlite:///./mrhux_bot.db

# Optional: PostgreSQL for production
# DATABASE_URL=postgresql://user:password@localhost/mrhux_bot
```

### **9. LOGGING CONFIGURATION**
```env
# LOGGING
LOG_LEVEL=INFO
LOG_FILE=logs/mrhux_bot.log
```

### **10. PERFORMANCE SETTINGS**
```env
# PERFORMANCE
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=30
CACHE_TTL=300
```

---

## 🚀 **COMPLETE ENVIRONMENT FILE**

Create a `.env` file with all your configurations:

```env
# ========================================
# MR HUX ALPHA BOT - COMPLETE CONFIGURATION
# ========================================

# TELEGRAM (REQUIRED)
BOT_TOKEN=your_bot_token_here
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_SESSION_NAME=mrhux_session

# REDDIT API
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=MR_HUX_Alpha_Bot/1.0

# X/TWITTER API
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_BEARER_TOKEN=your_bearer_token_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_SECRET=your_access_secret_here

# DISCORD WEBHOOK
DISCORD_WEBHOOK_URL=your_webhook_url_here

# GITHUB API
GITHUB_TOKEN=your_github_token_here

# SOLANA/BONK APIs
BIRDEYE_API_KEY=your_birdeye_api_key_here
BONK_API_KEY=your_bonk_api_key_here

# RSS FEEDS
RSS_FEEDS=https://coindesk.com/arc/outboundfeeds/rss/,https://cointelegraph.com/rss,https://cryptoslate.com/feed/

# DATABASE
DATABASE_URL=sqlite:///./mrhux_bot.db

# LOGGING
LOG_LEVEL=INFO
LOG_FILE=logs/mrhux_bot.log

# PERFORMANCE
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=30
CACHE_TTL=300

# WEB DASHBOARD
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8000
```

---

## 🔧 **SETUP SCRIPT**

I'll create a setup script to help you configure everything:

```python
# setup_apis.py
import os
import sys
from pathlib import Path

def setup_environment():
    """Interactive setup for all API keys."""
    
    print("🚀 MR HUX ALPHA BOT - API SETUP WIZARD")
    print("=" * 50)
    
    env_content = []
    
    # Telegram (Required)
    print("\n📱 TELEGRAM SETUP (REQUIRED)")
    print("-" * 30)
    bot_token = input("Enter your Telegram Bot Token: ").strip()
    api_id = input("Enter your Telegram API ID: ").strip()
    api_hash = input("Enter your Telegram API Hash: ").strip()
    
    env_content.extend([
        "# TELEGRAM (REQUIRED)",
        f"BOT_TOKEN={bot_token}",
        f"TELEGRAM_API_ID={api_id}",
        f"TELEGRAM_API_HASH={api_hash}",
        "TELEGRAM_SESSION_NAME=mrhux_session",
        ""
    ])
    
    # Reddit (Optional)
    print("\n🌐 REDDIT SETUP (OPTIONAL)")
    print("-" * 25)
    reddit_setup = input("Do you want to set up Reddit API? (y/n): ").lower().strip()
    
    if reddit_setup == 'y':
        client_id = input("Enter Reddit Client ID: ").strip()
        client_secret = input("Enter Reddit Client Secret: ").strip()
        env_content.extend([
            "# REDDIT API",
            f"REDDIT_CLIENT_ID={client_id}",
            f"REDDIT_CLIENT_SECRET={client_secret}",
            "REDDIT_USER_AGENT=MR_HUX_Alpha_Bot/1.0",
            ""
        ])
    
    # Twitter (Optional)
    print("\n🐦 X/TWITTER SETUP (OPTIONAL)")
    print("-" * 28)
    twitter_setup = input("Do you want to set up X/Twitter API? (y/n): ").lower().strip()
    
    if twitter_setup == 'y':
        api_key = input("Enter Twitter API Key: ").strip()
        api_secret = input("Enter Twitter API Secret: ").strip()
        bearer_token = input("Enter Twitter Bearer Token: ").strip()
        access_token = input("Enter Twitter Access Token: ").strip()
        access_secret = input("Enter Twitter Access Secret: ").strip()
        
        env_content.extend([
            "# X/TWITTER API",
            f"TWITTER_API_KEY={api_key}",
            f"TWITTER_API_SECRET={api_secret}",
            f"TWITTER_BEARER_TOKEN={bearer_token}",
            f"TWITTER_ACCESS_TOKEN={access_token}",
            f"TWITTER_ACCESS_SECRET={access_secret}",
            ""
        ])
    
    # Discord (Optional)
    print("\n💬 DISCORD SETUP (OPTIONAL)")
    print("-" * 25)
    discord_setup = input("Do you want to set up Discord webhook? (y/n): ").lower().strip()
    
    if discord_setup == 'y':
        webhook_url = input("Enter Discord Webhook URL: ").strip()
        env_content.extend([
            "# DISCORD WEBHOOK",
            f"DISCORD_WEBHOOK_URL={webhook_url}",
            ""
        ])
    
    # GitHub (Optional)
    print("\n🐙 GITHUB SETUP (OPTIONAL)")
    print("-" * 24)
    github_setup = input("Do you want to set up GitHub API? (y/n): ").lower().strip()
    
    if github_setup == 'y':
        token = input("Enter GitHub Token: ").strip()
        env_content.extend([
            "# GITHUB API",
            f"GITHUB_TOKEN={token}",
            ""
        ])
    
    # Solana/Bonk (Optional)
    print("\n🔥 SOLANA/BONK SETUP (OPTIONAL)")
    print("-" * 29)
    solana_setup = input("Do you want to set up Solana/Bonk APIs? (y/n): ").lower().strip()
    
    if solana_setup == 'y':
        birdeye_key = input("Enter Birdeye API Key: ").strip()
        bonk_key = input("Enter Bonk API Key (if available): ").strip()
        env_content.extend([
            "# SOLANA/BONK APIs",
            f"BIRDEYE_API_KEY={birdeye_key}",
            f"BONK_API_KEY={bonk_key}",
            ""
        ])
    
    # Default configurations
    env_content.extend([
        "# RSS FEEDS",
        "RSS_FEEDS=https://coindesk.com/arc/outboundfeeds/rss/,https://cointelegraph.com/rss,https://cryptoslate.com/feed/",
        "",
        "# DATABASE",
        "DATABASE_URL=sqlite:///./mrhux_bot.db",
        "",
        "# LOGGING",
        "LOG_LEVEL=INFO",
        "LOG_FILE=logs/mrhux_bot.log",
        "",
        "# PERFORMANCE",
        "MAX_CONCURRENT_REQUESTS=10",
        "REQUEST_TIMEOUT=30",
        "CACHE_TTL=300",
        "",
        "# WEB DASHBOARD",
        "DASHBOARD_HOST=0.0.0.0",
        "DASHBOARD_PORT=8000"
    ])
    
    # Write .env file
    env_file = Path(".env")
    with open(env_file, "w") as f:
        f.write("\n".join(env_content))
    
    print(f"\n✅ Environment file created: {env_file}")
    print("🚀 Your bot is ready to launch!")

if __name__ == "__main__":
    setup_environment()
```

---

## 🎯 **PRIORITY SETUP ORDER**

### **1. ESSENTIAL (Bot won't work without these)**
- ✅ Telegram Bot Token
- ✅ Telegram API ID & Hash

### **2. RECOMMENDED (For full functionality)**
- 🔄 Reddit API (for monitoring crypto communities)
- 🔄 Discord Webhook (for alert delivery)
- 🔄 RSS Feeds (for news monitoring)

### **3. OPTIONAL (Advanced features)**
- 🔄 X/Twitter API (for social media posting)
- 🔄 GitHub API (for project monitoring)
- 🔄 Solana/Bonk APIs (for token monitoring)

---

## 🚀 **NEXT STEPS**

1. **Set up Telegram first** - This is required for the bot to work
2. **Add other APIs gradually** - Start with Reddit and Discord
3. **Test each integration** - Use the bot's test features
4. **Monitor performance** - Check the bot's statistics

---

## 💡 **TIPS**

- **Start small**: Begin with just Telegram, then add APIs one by one
- **Test thoroughly**: Use the bot's built-in test features
- **Keep secrets safe**: Never share your API keys
- **Monitor usage**: Check API rate limits and usage
- **Backup configuration**: Keep a copy of your `.env` file

---

**Ready to set up your APIs? Let me know which ones you want to configure first! 🚀** 