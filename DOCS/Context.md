# SMA Telebot Development Contract
> Solana Market Alpha Telegram Bot

## Project Overview
**Client:** [Your Organization]  
**Version:** 1.0  
**Start Date:** [Date]


## Tech Stack
Category	Tech / Tool
Programming Language	Python 3.x
Telegram API Integration	Telethon
Bot Framework	python-telegram-bot
Data Parsing & Extraction	Regex, BeautifulSoup
API Integration	Dexscreener, RugCheck, Pump.fun, Bonk.fun, Birdeye
Database	SQLite (default), Firebase Firestore (optional)
Async Operations	Asyncio, aiohttp / httpx
Hosting	Heroku, AWS Lambda, VPS (DigitalOcean, EC2)
Containerization	Docker (optional)
Logging	Loguru, Python logging
Task Scheduler	Celery (optional)
Frontend (Optional)	Flask / FastAPI (admin dashboard)
Security	Environment variables for API keys

### Core Mission
Build an elite Telegram bot that monitors multiple alpha groups, validates new token launches, and posts verified opportunities to a single destination channel. The bot combines real-time market data, contract analysis, and momentum signals to identify high-quality Solana token plays.

## 🎯 Key Objectives
- Monitor multiple Telegram sources for token mentions
- Validate contracts using Rugcheck, Dexscreener, etc.
- Score tokens based on safety + hype metrics
- Post clean, actionable alerts to output channel

## 📋 Technical Requirements

### Core Stack
- Python 3.10+
- Telethon for Telegram API
- Async HTTP client (aiohttp/httpx)
- SQLite/Firestore for caching
- Docker-ready deployment

### API Integrations
- Pump.fun (unofficial)
- Bonk.fun 
- Dexscreener
- Rugcheck.xyz
- Birdeye (optional)

### Project Structure
```
sma_telebot/
├── main.py          # Bot entry point
├── config.py        # Settings & API keys
├── modules/
│   ├── telegram_listener.py
│   ├── parser.py    
│   ├── api_clients/
│   │   ├── pumpfun.py
│   │   ├── bonkfun.py
│   │   ├── dexscreener.py
│   │   ├── rugcheck.py
│   │   └── birdeye.py
│   ├── scorer.py
│   └── poster.py
└── logs/
```

## 📁 Extended Project Structure
```
sma_telebot/
├── alembic/                    # Database migrations
├── docker/                     # Docker configuration
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── nginx/
├── src/
│   ├── main.py                # Application entry point
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py        # Configuration management
│   │   └── logging.py         # Logging configuration
│   ├── core/
│   │   ├── __init__.py
│   │   ├── telegram/          # Telegram core functionality
│   │   │   ├── listener.py    # Message monitoring
│   │   │   └── poster.py      # Alert posting
│   │   └── services/          # Core business logic
│   │       ├── parser.py      # Token parsing
│   │       └── scorer.py      # Token scoring
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── admin.py      # Admin panel routes
│   │   │   └── metrics.py    # Monitoring endpoints
│   │   └── clients/          # External API clients
│   │       ├── pumpfun.py
│   │       ├── bonkfun.py
│   │       ├── dexscreener.py
│   │       ├── rugcheck.py
│   │       └── birdeye.py
│   ├── models/               # Database models
│   │   ├── __init__.py
│   │   ├── token.py
│   │   ├── alert.py
│   │   └── group.py
│   ├── schemas/             # Pydantic schemas
│   │   ├── __init__.py
│   │   └── responses.py
│   └── utils/              # Helper utilities
│       ├── __init__.py
│       ├── cache.py
│       └── formatters.py
├── tests/                  # Test suite
│   ├── conftest.py
│   ├── unit/
│   └── integration/
├── scripts/               # Utility scripts
├── logs/                 # Log files
└── docs/                # Documentation
    └── api.md
```

## 💾 Database Schema

### Tables

#### tokens
```sql
CREATE TABLE tokens (
    id SERIAL PRIMARY KEY,
    address VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(100),
    symbol VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    first_seen_at TIMESTAMP WITH TIME ZONE,
    last_updated_at TIMESTAMP WITH TIME ZONE,
    mint_authority VARCHAR(64),
    total_supply NUMERIC(20,0),
    decimals INTEGER,
    is_mint_disabled BOOLEAN,
    is_blacklisted BOOLEAN DEFAULT FALSE,
    metadata JSONB
);
```

#### token_metrics
```sql
CREATE TABLE token_metrics (
    id SERIAL PRIMARY KEY,
    token_id INTEGER REFERENCES tokens(id),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    price NUMERIC(20,10),
    volume_24h NUMERIC(20,2),
    market_cap NUMERIC(20,2),
    liquidity NUMERIC(20,2),
    holder_count INTEGER,
    buy_count_24h INTEGER,
    sell_count_24h INTEGER,
    safety_score INTEGER,
    hype_score INTEGER,
    UNIQUE(token_id, timestamp)
);
```

#### alerts
```sql
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    token_id INTEGER REFERENCES tokens(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    message_id INTEGER,
    channel_id BIGINT,
    alert_type VARCHAR(20),
    verdict VARCHAR(20),
    metrics_snapshot JSONB,
    is_deleted BOOLEAN DEFAULT FALSE
);
```

#### monitored_groups
```sql
CREATE TABLE monitored_groups (
    id SERIAL PRIMARY KEY,
    group_id BIGINT NOT NULL UNIQUE,
    name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    weight FLOAT DEFAULT 1.0,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_processed_message_id BIGINT,
    metadata JSONB
);
```

#### token_mentions
```sql
CREATE TABLE token_mentions (
    id SERIAL PRIMARY KEY,
    token_id INTEGER REFERENCES tokens(id),
    group_id INTEGER REFERENCES monitored_groups(id),
    message_id BIGINT,
    message_text TEXT,
    mentioned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sentiment FLOAT,
    metadata JSONB
);
```

### Indices
```sql
-- Performance indices
CREATE INDEX idx_tokens_address ON tokens(address);
CREATE INDEX idx_token_metrics_timestamp ON token_metrics(timestamp);
CREATE INDEX idx_alerts_created_at ON alerts(created_at);
CREATE INDEX idx_token_mentions_mentioned_at ON token_mentions(mentioned_at);

-- Foreign key indices
CREATE INDEX idx_token_metrics_token_id ON token_metrics(token_id);
CREATE INDEX idx_alerts_token_id ON alerts(token_id);
CREATE INDEX idx_token_mentions_token_id ON token_mentions(token_id);
CREATE INDEX idx_token_mentions_group_id ON token_mentions(group_id);
```

### Views
```sql
-- Token performance view
CREATE VIEW token_performance AS
SELECT 
    t.address,
    t.symbol,
    tm.price,
    tm.volume_24h,
    tm.liquidity,
    tm.holder_count,
    tm.safety_score,
    tm.hype_score
FROM tokens t
JOIN token_metrics tm ON t.id = tm.token_id
WHERE tm.timestamp = (
    SELECT MAX(timestamp)
    FROM token_metrics
    WHERE token_id = t.id
);

-- Alert summary view
CREATE VIEW alert_summary AS
SELECT 
    t.symbol,
    COUNT(*) as alert_count,
    MAX(a.created_at) as last_alert,
    MODE() WITHIN GROUP (ORDER BY a.verdict) as common_verdict
FROM alerts a
JOIN tokens t ON a.token_id = t.id
GROUP BY t.symbol;
```

## 🎯 Deliverable Milestones

### 1. Telegram Monitor (25%)
- Multi-group message tracking
- Token/link detection system
- Basic filtering logic

### 2. Data Pipeline (25%) 
- Contract parsing & validation
- Multi-API integration
- Data normalization

### 3. Scoring Engine (25%)
- Safety score (mint, LP, tax)
- Hype score (volume, holders, buys)
- Alert formatting & posting

### 4. Production Release (25%)
- Admin controls
- Rate limiting
- Final testing & deployment

## 📊 Output Format Example
```
🚨 NEW TOKEN DETECTED: $TOKEN
📜 Contract: [address]
📊 Volume: $123K | LP: $45K
👥 Holders: 398
🔥 3 whale buys detected

🛡️ Safety: Mint revoked, LP locked
📈 Chart: [Dexscreener link]

Verdict: 🔥 HOT PLAY
```

## 🛠️ Implementation Guide

### Step 1: Project Setup & Environment (2 days)

1. Initialize Project Structure
```bash
sma_telebot/
├── src/
├── tests/
├── alembic/
└── docker/
```

2. Create Core Configuration Files
- `pyproject.toml` for Poetry
- `.env` template for environment variables
- `docker-compose.yml` for local development
- `alembic.ini` for database migrations

3. Essential Dependencies
```toml
[tool.poetry.dependencies]
python = "^3.10"
telethon = "^1.28.0"
fastapi = "^0.95.0"
sqlalchemy = "^2.0.0"
alembic = "^1.11.0"
pydantic = "^1.10.0"
httpx = "^0.24.0"
redis = "^4.5.0"
loguru = "^0.7.0"
```

### Step 2: Database Setup (2 days)

1. Initialize Database
```bash
# In docker-compose.yml
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: sma_telebot
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

2. Create Initial Migration
```bash
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

### Step 3: Telegram Integration (3 days)

1. Core Telegram Client Setup (`src/core/telegram/client.py`):
```python
from telethon import TelegramClient
from src.config import settings

client = TelegramClient(
    'sma_bot',
    settings.TELEGRAM_API_ID,
    settings.TELEGRAM_API_HASH
)

async def initialize_client():
    await client.start(bot_token=settings.BOT_TOKEN)
    return client
```

2. Message Listener Implementation (`src/core/telegram/listener.py`):
```python
from telethon import events
from src.core.telegram.client import client
from src.services.parser import TokenParser

@client.on(events.NewMessage(chats=MONITORED_GROUPS))
async def handle_new_message(event):
    if not event.message.text:
        return
        
    tokens = await TokenParser.extract_tokens(event.message.text)
    if not tokens:
        return
        
    for token in tokens:
        await process_token(token, event)
```

### Step 4: Token Parser Implementation (3 days)

1. Create Parser Service (`src/services/parser.py`):
```python
import re
from src.models.token import Token

class TokenParser:
    SPL_ADDRESS_PATTERN = r'[1-9A-HJ-NP-Za-km-z]{32,44}'
    
    @staticmethod
    async def extract_tokens(text: str) -> list[str]:
        # Extract SPL addresses
        addresses = re.findall(TokenParser.SPL_ADDRESS_PATTERN, text)
        
        # Extract Pump.fun and Bonk.fun links
        pump_tokens = re.findall(r'pump\.fun/token/(.*?)(?:\s|$)', text)
        bonk_tokens = re.findall(r'bonk\.fun/token/(.*?)(?:\s|$)', text)
        
        return list(set(addresses + pump_tokens + bonk_tokens))
```

### Step 5: API Client Integration (4 days)

1. Base API Client (`src/api/clients/base.py`):
```python
from httpx import AsyncClient, Response
from src.config import settings

class BaseAPIClient:
    def __init__(self):
        self.client = AsyncClient(timeout=10.0)
        
    async def _get(self, url: str, **kwargs) -> Response:
        return await self.client.get(url, **kwargs)
```

2. Implement Specific Clients:
- DexscreenerClient
- RugcheckClient
- PumpfunClient
- BonkfunClient
- BirdeyeClient

### Step 6: Scoring System (3 days)

1. Create Scoring Service (`src/services/scorer.py`):
```python
class TokenScorer:
    async def calculate_safety_score(self, token_data: dict) -> int:
        score = 0
        
        # Mint authority check
        if token_data['is_mint_disabled']:
            score += 3
            
        # LP check
        if token_data['is_lp_locked']:
            score += 2
            
        return min(score, 10)  # Cap at 10

    async def calculate_hype_score(self, metrics: dict) -> int:
        score = 0
        
        # Volume score
        volume_24h = metrics['volume_24h']
        if volume_24h > 100000:  # $100k
            score += 3
            
        # Holder growth
        if metrics['holder_growth_24h'] > 100:
            score += 2
            
        return min(score, 10)  # Cap at 10
```

### Step 7: Alert System (2 days)

1. Create Alert Service (`src/services/alerts.py`):
```python
from src.models import Alert
from src.core.telegram.poster import send_alert

class AlertService:
    def __init__(self):
        self.min_score_threshold = 6
        
    async def process_token_alert(self, token: dict, scores: dict):
        if scores['total'] < self.min_score_threshold:
            return
            
        alert = Alert(
            token_id=token['id'],
            alert_type='new_token',
            verdict=self._get_verdict(scores),
            metrics_snapshot=scores
        )
        
        await send_alert(alert)
```

### Step 8: Testing & Deployment (4 days)

1. Unit Tests Setup (`tests/unit/`):
- Test token parser
- Test scoring system
- Test alert generation

2. Integration Tests (`tests/integration/`):
- Test full token processing flow
- Test API client integration
- Test database operations

3. Deployment Configuration:
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  bot:
    build:.
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/sma_telebot
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
  redis:
    image: redis:alpine
    volumes:
      - redis_data:/data
```

Each step builds upon the previous one, creating a robust and maintainable system. The implementation times are estimates and may vary based on complexity and requirements.

Would you like to start with any particular step or need more details about any part?