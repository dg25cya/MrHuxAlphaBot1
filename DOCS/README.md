# SMA Telebot - Advanced Solana Market Alpha Bot

## 🎯 Core Objective
SMA Telebot is an advanced Telegram bot designed to monitor, analyze, and validate Solana tokens in real-time. It aggregates data from multiple sources, performs comprehensive security checks, detects market patterns, and delivers verified alpha alerts to your Telegram channel.

## ✨ Key Features

### 🔍 Real-time Token Monitoring
- Price and volume tracking with multi-source validation
- Market cap and liquidity analysis
- Holder statistics and distribution tracking
- Advanced security score calculation
- Pattern and trend detection
- Smart money movement tracking

### 📊 Data Integration
- **Birdeye**: Real-time price and market data
- **Dexscreener**: Trading pair analysis
- **Rugcheck**: Security and contract analysis
- **Pump.fun**: Launch and IDO data
- **Bonk.fun**: Token metrics and social sentiment

### 🎯 Advanced Analysis
- Proprietary token scoring system
- Multi-factor risk assessment
- Technical pattern recognition
- Social sentiment analysis
- Whale wallet tracking

### ⚡ Alert System
- Customizable price movement alerts
- Volume spike detection
- Security risk warnings
- Smart money tracking
- Pattern-based notifications

### 🎛️ Admin Dashboard
- Real-time system monitoring
- Performance metrics and analytics
- Health status monitoring
- Configuration management
- Token blacklist management

## 🏗️ Architecture Overview

### 1. Core Components
- **Token Monitor**: Real-time market data processing
- **Alert Service**: Pattern detection and notification
- **Security Analyzer**: Risk assessment and validation
- **API Integration**: Multi-source data aggregation
  - Monitors multiple Telegram groups simultaneously
  - Covers private alpha groups, paid signal groups, and whale-tracking rooms
  - Extracts signals from Twitter-to-Telegram bot feeds
  - Configurable source list for maximum coverage

### 2. Token Detection System
- **Input Sources**:
  - Pump.fun links
  - Bonk.fun links
  - Raw Solana contract addresses
  - Context-aware mention detection
- **Processing**:
  - Advanced regex patterns for contract extraction
  - Link normalization
  - Context-based token mention detection
  - Image text extraction (OCR) for hidden drops

### 3. Cross-Platform Verification Engine
- **API Integrations**:
  ```python
  api_clients/
  ├── pumpfun.py      # Launch status, SOL raised
  ├── bonkfun.py      # Trending + new listings
  ├── dexscreener.py  # Price, volume, LP data
  ├── rugcheck.py     # Contract safety analysis
  ├── birdeye.py      # Secondary price verification
  └── social_data.py  # Social mentions and sentiment
  ```
- **Verification Steps**:
  1. Contract validation
  2. Liquidity checks
  3. Trading volume analysis
  4. Holder distribution scanning
  5. Social mention tracking and sentiment analysis
  6. Whale wallet tracking (optional)

### 4. Scoring & Analysis System
- **Safety Metrics** 🛡️:
  - Mint status (revoked/active)
  - LP status (locked/unlocked)
  - Tax configuration
  - Contract anomalies
  
- **Hype Indicators** 🔥:
  - Volume trends
  - Holder growth rate
  - Whale wallet activity
  - Social mention frequency
  - Cross-platform momentum

### 5. Alert Distribution System
- **Output Format**:
```
🚨 NEW TOKEN DETECTED: $SYMBOL
📜 Contract: [address]

📊 Market Stats:
- Volume: $XXX
- Liquidity: $XXX
- Holders: XXX

🛡️ Safety Check:
- Mint Status: [Revoked/Active]
- LP Status: [Locked/Unlocked]
- Tax: X%

� Social Stats:
- Mentions: XX in 24h
- Sentiment: [Positive/Neutral/Negative]
- Hype Score: XX/100

�📈 [View Chart](dexscreener_link)

🎯 Verdict: [HOT BUY 🔥 / CAUTION ⚠️ / AVOID ❌]
```

## 🔧 Technical Requirements

### Core Dependencies
- Python 3.10+
- Telethon (Telegram client)
- Async HTTP client (httpx/aiohttp)
- SQLite/Firestore (token tracking)
- Docker support

### File Structure
```bash
sma_telebot/
│
├── main.py                 # Bot entry point
├── config.py               # Configuration & API keys
├── runner.py               # Bot runner and utility script
├── modules/
│   ├── telegram_listener.py
│   ├── parser.py
│   ├── api_clients/        # API integrations
│   ├── scorer.py           # Token analysis
│   └── poster.py           # Alert formatting
├── scripts/                # Test and utility scripts
└── logs/                   # Activity logging
```

## ⚙️ Usage
### Setting Up
Set up the database:
```bash
python -m scripts.setup_database
```

### Starting the Bot
Run the bot using the runner script:
```bash
python runner.py start
```

### Running Tests
Test specific components:
```bash
# Test social integration
python runner.py test:social

# Test basic system
python runner.py test:basic

# Test integrated system
python runner.py test:integrated

# Run all tests
python runner.py test
```

### System Health Check
Verify system components are working:
```bash
python runner.py health
```

## 🔐 Security Features
- Admin-only message processing
- API rate limiting
- Duplicate token detection
- Historical rug tracking
- Configurable blocklist

## 🎛️ Customization Options
- Custom token filters
- Minimum liquidity thresholds
- Required safety checks
- Alert formatting
- Tracking duration
- Auto-blacklist rules

## 🚀 New Features
- **Social Media Integration**: Track and analyze mentions across Twitter, Telegram, and Discord
- **Sentiment Analysis**: Evaluate the sentiment of token mentions in social media
- **Enhanced Scoring**: Incorporate social metrics into token scoring
- **Real-time Monitoring**: Runner script for easy bot management and testing
- **Improved Error Handling**: Robust error recovery in API clients
- **Health Monitoring**: Track system health and API status

## ⚡ Competitive Advantages
1. Multi-source signal aggregation
2. Comprehensive safety validation
3. Real-time cross-platform verification
4. Custom filtering system
5. Expandable architecture
6. Single unified alpha feed

## 📝 Implementation Notes
1. Use async/await for API calls
2. Implement robust error handling
3. Cache frequent API requests
4. Log all operations for debugging
5. Include retry logic for API failures
6. Maintain test coverage

## 🔍 Monitoring & Maintenance
- API health checks
- Error rate monitoring
- Response time tracking
- Token validation success rate
- False positive tracking

Remember: The goal is to be 10 seconds ahead of retail, 10 moves ahead of rugs, and 10x closer to the next moonshot. Build accordingly.
