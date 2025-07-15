"""Simple test file for Telegram bot."""
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, cast, NoReturn, TYPE_CHECKING
import signal

from loguru import logger
from telethon import TelegramClient, events, sync
from prometheus_client import start_http_server, Counter, Gauge, Histogram
from sqlalchemy.orm import Session

from src.config.settings import get_settings
from src.core.services.parser import TokenParser
from src.core.services.scorer import TokenScorer
from src.models.group import MonitoredGroup
from src.models.token_metrics import TokenMetrics
from src.database import SessionLocal, init_db
from src.core.telegram.listener import handle_new_message, setup_message_handler

if TYPE_CHECKING:
    from telethon import TelegramClient as TelegramClientType
else:
    TelegramClientType = TelegramClient

settings = get_settings()

# Metrics
TEST_COMMANDS = Counter(
    'test_bot_commands_total',
    'Number of test commands executed',
    ['command']
)

PARSER_TESTS = Counter(
    'token_parser_tests_total',
    'Number of token parser tests executed',
    ['status']
)

SCORER_TESTS = Counter(
    'token_scorer_tests_total',
    'Number of token scoring tests executed',
    ['status']
)

BOT_UPTIME = Gauge(
    'test_bot_uptime_seconds',
    'How long the test bot has been running'
)

TEST_LATENCY = Histogram(
    'test_bot_latency_seconds',
    'Response time for test commands'
)

# Test tokens for verification
TEST_TOKENS = {
    "valid": [
        "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",  # USDC
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDT
        "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",  # BONK
    ],
    "invalid": [
        "invalid_address_123",
        "not_a_token",
    ]
}

class TestBot:
    """Test bot implementation."""
    
    def __init__(self, client: TelegramClientType) -> None:
        """Initialize test bot."""
        self.client = client
        self.parser = TokenParser()
        self.scorer = TokenScorer()
        self.start_time = datetime.now()
        self.db_session: Optional[Session] = None
        
        # Test settings
        self.test_group_id = getattr(settings, 'test_group_id', settings.output_channel_id)
        self.metrics_port = getattr(settings, 'metrics_port', 9091)
        
    async def setup(self):
        """Setup test bot and database."""
        # Initialize database
        await init_db()
        
        # Create test session
        self.db_session = SessionLocal()
        
        # Ensure we have a test group
        await self._ensure_test_group()
        
        # Setup message handler
        await setup_message_handler(self.client)
        
        # Start metrics server on test port
        try:
            start_http_server(self.metrics_port)
            logger.info(f"Started metrics server on port {self.metrics_port}")
        except Exception as e:
            logger.warning(f"Could not start metrics server: {e}")
        
        # Start uptime tracking
        asyncio.create_task(self._track_uptime())
        
    async def _track_uptime(self):
        """Update bot uptime metric."""
        while True:
            BOT_UPTIME.set((datetime.now() - self.start_time).total_seconds())
            await asyncio.sleep(1)
            
    async def _ensure_test_group(self):
        """Ensure test group exists in database."""
        if not self.db_session:
            logger.error("No database session available")
            return
            
        try:
            group = self.db_session.query(MonitoredGroup).filter(
                MonitoredGroup.group_id == self.test_group_id
            ).first()
            
            if not group:
                group = MonitoredGroup(
                    group_id=self.test_group_id,
                    name="Test Group",
                    is_active=True
                )
                self.db_session.add(group)
                self.db_session.commit()
                logger.info(f"Created test group {self.test_group_id}")
        except Exception as e:
            logger.error(f"Error ensuring test group: {e}")
            if self.db_session:
                self.db_session.rollback()
                
    async def _test_token_parser(self, text: str) -> Dict[str, Any]:
        """Test token parser with given text."""
        try:
            tokens = await self.parser.parse_message(
                text=text,
                channel_id=self.test_group_id,
                message_id=0,
                source="test"
            )
            PARSER_TESTS.labels(status="success").inc()
            return {
                "success": True,
                "tokens": tokens,
                "count": len(tokens)
            }
        except Exception as e:
            PARSER_TESTS.labels(status="error").inc()
            return {
                "success": False,
                "error": str(e)
            }

    async def _test_token_scorer(self, token_address: str) -> Dict[str, Any]:
        """Test token scoring for a given address."""
        try:
            # Create test metrics
            metrics = TokenMetrics(
                token_id=1,  # Dummy ID
                timestamp=datetime.utcnow(),
                price=1.0,
                volume_24h=100000.0,
                market_cap=1000000.0,
                liquidity=50000.0,
                holder_count=1000,
                buy_count_24h=500,
                sell_count_24h=300,
                safety_score=None,
                hype_score=None
            )

            score = await self.scorer.get_token_score(token_address, metrics)
            SCORER_TESTS.labels(status="success").inc()
            
            return {
                "success": True,
                "safety_score": score.safety_score,
                "hype_score": score.hype_score,
                "risk_factors": score.risk_factors,
                "verdict": score.verdict,
                "confidence": score.confidence
            }
        except Exception as e:
            SCORER_TESTS.labels(status="error").inc()
            return {
                "success": False,
                "error": str(e)
            }
            
    def register_handlers(self) -> None:
        """Register message handlers."""
        
        @self.client.on(events.NewMessage(pattern='/ping'))
        async def ping_handler(event):
            """Handle /ping command."""
            with TEST_LATENCY.time():
                TEST_COMMANDS.labels(command="ping").inc()
                await event.reply('Pong!')
                
        @self.client.on(events.NewMessage(pattern='/test_parser'))
        async def test_parser_handler(event):
            """Test token parser with valid and invalid tokens."""
            with TEST_LATENCY.time():
                TEST_COMMANDS.labels(command="test_parser").inc()
                
                results = []
                
                # Test valid tokens
                for token in TEST_TOKENS["valid"]:
                    text = f"Testing valid token: {token}"
                    result = await self._test_token_parser(text)
                    results.append({
                        "token": token,
                        "type": "valid",
                        "result": result
                    })
                
                # Test invalid tokens
                for token in TEST_TOKENS["invalid"]:
                    text = f"Testing invalid token: {token}"
                    result = await self._test_token_parser(text)
                    results.append({
                        "token": token,
                        "type": "invalid",
                        "result": result
                    })
                
                # Format response
                response = "Token Parser Test Results:\n\n"
                for r in results:
                    response += f"Token: {r['token']}\n"
                    response += f"Type: {r['type']}\n"
                    response += f"Success: {r['result']['success']}\n"
                    if r['result']['success']:
                        response += f"Tokens found: {r['result']['count']}\n"
                    else:
                        response += f"Error: {r['result'].get('error', 'Unknown')}\n"
                    response += "\n"
                
                await event.reply(response)

        @self.client.on(events.NewMessage(pattern='/test_scorer'))
        async def test_scorer_handler(event):
            """Test token scorer with valid tokens."""
            with TEST_LATENCY.time():
                TEST_COMMANDS.labels(command="test_scorer").inc()
                
                results = []
                
                # Test scoring for valid tokens
                for token in TEST_TOKENS["valid"]:
                    result = await self._test_token_scorer(token)
                    results.append({
                        "token": token,
                        "result": result
                    })
                
                # Format response
                response = "Token Scorer Test Results:\n\n"
                for r in results:
                    response += f"Token: {r['token']}\n"
                    if r['result']['success']:
                        response += f"Safety Score: {r['result']['safety_score']:.2f}/100\n"
                        response += f"Hype Score: {r['result']['hype_score']:.2f}/100\n"
                        response += f"Verdict: {r['result']['verdict']}\n"
                        response += f"Confidence: {r['result']['confidence']:.2f}\n"
                        if r['result']['risk_factors']:
                            response += f"Risk Factors: {', '.join(r['result']['risk_factors'])}\n"
                    else:
                        response += f"Error: {r['result'].get('error', 'Unknown')}\n"
                    response += "\n"
                
                await event.reply(response)
                
        @self.client.on(events.NewMessage(pattern='/stats'))
        async def stats_handler(event):
            """Show bot statistics."""
            with TEST_LATENCY.time():
                TEST_COMMANDS.labels(command="stats").inc()
                
                uptime = (datetime.now() - self.start_time).total_seconds()
                
                stats = {
                    "uptime": f"{uptime:.2f} seconds",
                    "command_counts": {
                        "ping": int(TEST_COMMANDS.labels(command="ping")._value.get()),
                        "test_parser": int(TEST_COMMANDS.labels(command="test_parser")._value.get()),
                        "test_scorer": int(TEST_COMMANDS.labels(command="test_scorer")._value.get()),
                        "stats": int(TEST_COMMANDS.labels(command="stats")._value.get())
                    },
                    "tests": {
                        "parser": {
                            "success": int(PARSER_TESTS.labels(status="success")._value.get()),
                            "error": int(PARSER_TESTS.labels(status="error")._value.get())
                        },
                        "scorer": {
                            "success": int(SCORER_TESTS.labels(status="success")._value.get()),
                            "error": int(SCORER_TESTS.labels(status="error")._value.get())
                        }
                    }
                }
                
                response = "Bot Statistics:\n\n"
                response += f"Uptime: {stats['uptime']}\n\n"
                
                response += "Command Counts:\n"
                for cmd, count in stats["command_counts"].items():
                    response += f"- {cmd}: {count}\n"
                
                response += "\nParser Tests:\n"
                for status, count in stats["tests"]["parser"].items():
                    response += f"- {status}: {count}\n"
                
                response += "\nScorer Tests:\n"
                for status, count in stats["tests"]["scorer"].items():
                    response += f"- {status}: {count}\n"
                
                await event.reply(response)

def signal_handler(signum, frame) -> None:
    """Handle termination signals."""
    logger.info(f"Received signal {signum}")
    raise KeyboardInterrupt

async def main() -> None:
    """Main test function."""
    logger.info("Starting test bot...")
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize the client
    client = TelegramClient(
        'test_mr_hux_alpha_bot',
        settings.telegram_api_id,
        settings.telegram_api_hash
    )
    
    # Create test bot instance
    bot = None
    
    try:
        # Connect to Telegram
        logger.info("Connecting to Telegram...")
        await client.connect()
        if not await client.is_user_authorized():
            await client.sign_in(bot_token=settings.bot_token)
        logger.info("Successfully connected to Telegram!")
        
        # Create and setup test bot
        bot = TestBot(client)
        await bot.setup()
        bot.register_handlers()
          # Run until signal received
        try:
            logger.info("Bot is running. Press Ctrl+C to stop.")
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as main_err:
            logger.error(f"Error in main loop: {str(main_err)}")
            raise
    except Exception as init_err:
        logger.error(f"Error initializing bot: {str(init_err)}")
        raise
    finally:
        # Cleanup database
        if bot is not None and bot.db_session is not None:
            try:
                bot.db_session.close()
                logger.info("Database session closed")
            except Exception as db_err:
                logger.error(f"Error closing database session: {db_err}")
                
        # Cleanup Telegram client
        if client is not None:
            try:
                if client.is_connected():
                    client.disconnect()  # Synchronous in newer Telethon versions
                    logger.info("Disconnected from Telegram")
            except Exception as disconnect_err:
                logger.error(f"Error disconnecting from Telegram: {disconnect_err}")
        
        logger.info("Test bot shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
