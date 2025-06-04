# SMA Telebot - Advanced Crypto Alpha Scraping Bot

## 🎯 Core Objective
SMA Telebot is an advanced Telegram bot designed to aggregate and validate crypto alpha from multiple sources. It scrapes token mentions across multiple Telegram groups, performs comprehensive safety checks, and delivers verified alpha to a single destination group.

## 🏗️ Architecture Overview

### 1. Multi-Source Intelligence (MSI) Scraper
- **Technology**: Telethon library
- **Capabilities**:
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
  └── birdeye.py      # Secondary price verification
  ```
- **Verification Steps**:
  1. Contract validation
  2. Liquidity checks
  3. Trading volume analysis
  4. Holder distribution scanning
  5. Whale wallet tracking (optional)

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

📈 [View Chart](dexscreener_link)

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
├── modules/
│   ├── telegram_listener.py
│   ├── parser.py
│   ├── api_clients/        # API integrations
│   ├── scorer.py           # Token analysis
│   └── poster.py           # Alert formatting
└── logs/                   # Activity logging
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

## 🚀 Future Expansion
- AI-powered token scoring
- Smart wallet tracking
- Time-based alerts
- Data export (Google Sheets/Notion)
- Daily summary reports
- BubbleMap integration

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
