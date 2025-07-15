"""Token monitoring service for real-time tracking and analysis."""
from typing import Dict, Any, List, Optional, Set, AsyncGenerator
import asyncio
import psutil
from datetime import datetime, timedelta
import time
from contextlib import asynccontextmanager
from loguru import logger
from sqlalchemy.orm import Session
from decimal import Decimal
import threading

# Using absolute imports to avoid circular references
from src.api.clients import (
    BirdeyeClient,
    DexscreenerClient,
    RugcheckClient,
    PumpfunClient,
    BonkfunClient,
    SocialDataClient
)
from src.models import (
    Token,
    TokenMetrics,
    TokenScore as TokenScoreModel,
    Alert
)
from src.models.mention import TokenMention
from src.utils.db import db_session
from src.utils.async_db import async_db_session, async_get, async_filter, async_count, async_commit, run_db_query
from src.config.settings import get_settings
from src.core.services.scorer import TokenScorer, TokenScore
from src.core.services.token_patterns import PatternDetector
from src.core.services.token_validation import TokenValidationService
from src.core.services.token_analysis import TokenAnalysisService
# Optional websocket import - handle gracefully if not available
try:
    from src.api.websocket import ws_manager
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    ws_manager = None

# Import metrics from central registry
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry

# Create a registry for our metrics
registry = CollectorRegistry()

from src.utils.metrics_registry import metrics

# Public API - use centralized metrics
def update_token_count(value: float = 1.0) -> None:
    """Update token count."""
    metrics.update_token_count(value)

def log_token_update(status: str) -> None:
    """Log token update status."""
    metrics.log_token_update(status)

def observe_monitor_latency(operation: str, duration: float) -> None:
    """Record monitor latency."""
    metrics.observe_monitor_latency(operation, duration)

def record_price_change(token_address: str, change: float) -> None:
    """Record token price change."""
    metrics.record_price_change(token_address, change)

def record_momentum_score(score: float) -> None:
    """Record token momentum score."""
    metrics.record_momentum_score(score)

@asynccontextmanager
async def monitor_latency(operation: str) -> AsyncGenerator[None, None]:
    """Async context manager for monitoring operation latency."""
    start = time.time()
    try:
        yield
    finally:
        duration = time.time() - start
        observe_monitor_latency(operation, duration)

# Utility functions for price tracking
def calculate_price_change(old_price: float, new_price: float) -> float:
    """Calculate percentage change between old and new price."""
    if old_price == 0:
        return 0.0
    return ((new_price - old_price) / old_price) * 100

def track_price_change(token_address: str, old_price: float, new_price: float) -> float:
    """Track price changes for a token and record metrics."""
    try:
        change = calculate_price_change(old_price, new_price)
        record_price_change(token_address, abs(change))
        
        # Log significant price movements
        if abs(change) >= 5.0:  # 5% or more change
            logger.info(f"Significant price movement for {token_address}: {change:+.2f}%")
            
        return change
    except Exception as e:
        logger.warning(f"Error tracking price change for {token_address}: {e}")
        return 0.0

def track_market_update(
    token_address: str,
    market_data: Dict[str, Any],
    previous_data: Optional[Dict[str, Any]] = None
) -> Dict[str, float | bool]:
    """Track and analyze market data updates."""
    result = {
        "price_change": 0.0,
        "volume_change": 0.0,
        "significant_movement": False
    }
    
    try:
        if not previous_data:
            return result
            
        # Track price changes if data available
        if "price" in market_data and "price" in previous_data:
            price_change = track_price_change(
                token_address,
                float(previous_data["price"]),
                float(market_data["price"])
            )
            result["price_change"] = price_change
            
        # Track volume changes if data available
        if "volume_24h" in market_data and "volume_24h" in previous_data:
            volume_change = calculate_price_change(
                float(previous_data["volume_24h"]),
                float(market_data["volume_24h"])
            )
            result["volume_change"] = volume_change
            
        # Detect significant movements
        result["significant_movement"] = (
            abs(result["price_change"]) >= 5.0 or  # 5% price change
            abs(result["volume_change"]) >= 20.0    # 20% volume change
        )
        
        return result
    except Exception as e:
        logger.warning(f"Error tracking market update for {token_address}: {e}")
        return result

# Public API
# No need to redefine these functions as they are imported from metrics_registry

class TokenMonitor:
    """Service for monitoring and analyzing tokens in real-time."""
    
    def __init__(self) -> None:
        """Initialize the token monitor service."""
        self.settings = get_settings()
        self.scorer = TokenScorer()
        self.pattern_detector = PatternDetector()
        self.validator = TokenValidationService()
        self.analyzer = TokenAnalysisService()
        
        # Initialize API clients
        self.birdeye = BirdeyeClient()
        self.dexscreener = DexscreenerClient()
        self.rugcheck = RugcheckClient()
        self.pumpfun = PumpfunClient()
        self.bonkfun = BonkfunClient()
        self.social_data = SocialDataClient()
        
        # Track monitored tokens and their market data
        self.monitored_tokens: Set[str] = set()
        self.previous_market_data: Dict[str, Dict[str, Any]] = {}
        self._running = False
        self._monitoring_task = None
        
        # System metrics
        self.start_time = datetime.utcnow()
        self.messages_processed = 0
        self.errors_last_hour = 0
        
        # Aliases for health check
        self.birdeye_client = self.birdeye
        self.dexscreener_client = self.dexscreener
        self.rugcheck_client = self.rugcheck
        self.pumpfun_client = self.pumpfun
        self.bonkfun_client = self.bonkfun
        
        # System status
        self.is_running = False        
    async def start(self):
        """Start the token monitoring service."""
        if self._running:
            return
        
        self._running = True
        self.is_running = True
        self._monitoring_task = asyncio.create_task(self._monitor_loop())
        logger.info("Token monitoring service started")
    
    async def stop(self):
        """Stop the token monitoring service."""
        if not self._running:
            return
        
        self._running = False
        self.is_running = False
        if self._monitoring_task:
            await self._monitoring_task
        
        # Clear market data tracking
        self.previous_market_data.clear()
        
        logger.info("Token monitoring service stopped")
    
    async def add_token(self, token_address: str, initial_data: Optional[Dict] = None, db: Optional[Session] = None):
        """Add a new token for monitoring with enhanced validation and analysis."""
        if token_address in self.monitored_tokens:
            return
        try:
            # Validate token first
            validation_results = await self.validator.validate_token(token_address)
            if not validation_results["is_valid"]:
                logger.warning(
                    f"Token {token_address} failed validation: {validation_results}"
                )
                log_token_update("validation_failed")
                return
            # Get momentum and analysis data
            momentum_data = await self.analyzer.get_token_momentum(token_address)
            if momentum_data and 'momentum_score' in momentum_data:
                record_momentum_score(momentum_data['momentum_score'])
            # Initialize token data
            token_data = initial_data or {}
            token_data.update({
                "address": token_address,
                "validation": validation_results,
                "momentum": momentum_data
            })
            # Create metrics for scoring
            metrics = TokenMetrics()
            # Fill metrics with data from token_data
            if 'price' in token_data:
                metrics.price = token_data['price']
            if 'market_cap' in token_data:
                metrics.market_cap = token_data['market_cap']
            if 'volume_24h' in token_data:
                metrics.volume_24h = token_data['volume_24h']
            if 'liquidity' in token_data:
                metrics.liquidity = token_data['liquidity']
            if 'holder_count' in token_data:
                metrics.holder_count = token_data['holder_count']
            # Calculate initial score using our proper metrics object
            score = await self.scorer.get_token_score(token_address, metrics)
            token_data["score"] = score.to_dict()
            # Add to monitoring set and initialize market data tracking
            self.monitored_tokens.add(token_address)
            if "price" in token_data or "volume_24h" in token_data:
                self.previous_market_data[token_address] = {
                    "price": token_data.get("price", 0),
                    "volume_24h": token_data.get("volume_24h", 0)
                }
            # Store in database and broadcast update
            if db is not None:
                await self._store_token_data(db, token_data)
            else:
                async with async_db_session() as session:
                    await self._store_token_data(session, token_data)
            # Broadcast via WebSocket if available
            if WEBSOCKET_AVAILABLE and ws_manager:
                try:
                    await ws_manager.broadcast_token_update(token_data)
                except Exception as e:
                    logger.warning(f"Failed to broadcast token update: {e}")
            log_token_update("added")
            update_token_count()
            logger.info(f"Started monitoring token: {token_address}")
        except Exception as e:
            logger.exception(f"Error adding token {token_address}: {e}")
            log_token_update("error")

    async def _monitor_loop(self):
        """Main monitoring loop with enhanced analysis."""
        while self._running:
            try:
                async with monitor_latency("monitor_loop"):
                    for token_address in list(self.monitored_tokens):
                        try:
                            # Get fresh market data
                            start_time = time.time()
                            market_data = await self._get_market_data(token_address)
                            observe_monitor_latency("market_data", time.time() - start_time)
                            
                            # Track market changes
                            market_changes = track_market_update(
                                token_address,
                                market_data,
                                self.previous_market_data.get(token_address)
                            )
                            
                            # Update previous market data for next comparison
                            self.previous_market_data[token_address] = market_data
                            
                            # If significant movement detected, include in token data
                            if market_changes["significant_movement"]:
                                market_data["market_changes"] = market_changes
                                if WEBSOCKET_AVAILABLE and ws_manager:
                                    try:
                                        await ws_manager.broadcast_analytics({
                                            "token_address": token_address,
                                            "market_changes": market_changes,
                                            "timestamp": datetime.utcnow().isoformat()
                                        })
                                    except Exception as e:
                                        logger.warning(f"Failed to broadcast analytics: {e}")
                            
                            # Get fresh momentum data
                            try:
                                start_time = time.time()
                                momentum_data = await self.analyzer.get_token_momentum(token_address)
                                observe_monitor_latency("momentum_analysis", time.time() - start_time)
                                
                                if momentum_data and momentum_data.get("momentum_score") is not None:
                                    # Record the momentum score in metrics
                                    record_momentum_score(momentum_data["momentum_score"])
                            except Exception as e:
                                logger.warning(f"Error getting momentum data for {token_address}: {e}")
                                momentum_data = {}
                            
                            # Combine data for analysis
                            token_data = {
                                **market_data,
                                "momentum": momentum_data
                            }
                            
                            # Create TokenMetrics object for scoring
                            metrics = TokenMetrics()
                            # We don't set token_id here as it's a database field - we'll handle it in _store_token_data
                            
                            # Fill TokenMetrics with data from token_data
                            if 'price' in token_data:
                                metrics.price = token_data['price']
                            
                            if 'market_cap' in token_data:
                                metrics.market_cap = token_data['market_cap']
                            
                            if 'volume_24h' in token_data:
                                metrics.volume_24h = token_data['volume_24h']
                            
                            if 'liquidity' in token_data:
                                metrics.liquidity = token_data['liquidity']
                            
                            if 'holder_count' in token_data:
                                metrics.holder_count = token_data['holder_count']
                            
                            # Update score with new data
                            score = await self.scorer.get_token_score(token_address, metrics)
                            token_data["score"] = score.to_dict()
                            
                            # Time the storage operation
                            start_time = time.time()
                            async with async_db_session() as db:
                                await self._store_token_data(db, token_data)
                            observe_monitor_latency("store_data", time.time() - start_time)
                            
                            # Broadcast update via WebSocket if available
                            if WEBSOCKET_AVAILABLE and ws_manager:
                                start_time = time.time()
                                try:
                                    await ws_manager.broadcast_token_update(token_data)
                                    observe_monitor_latency("broadcast", time.time() - start_time)
                                except Exception as e:
                                    logger.warning(f"Failed to broadcast token update: {e}")
                            
                            log_token_update("updated")
                            
                            # Record momentum score if available
                            if momentum_data and momentum_data.get("momentum_score") is not None:
                                record_momentum_score(momentum_data["momentum_score"])
                            
                            # Broadcast analytics update if significant changes
                            if (momentum_data and momentum_data.get("momentum_score", 0) >= 3.0):
                                if WEBSOCKET_AVAILABLE and ws_manager:
                                    try:
                                        await ws_manager.broadcast_analytics({
                                            "token_address": token_address,
                                            "momentum": momentum_data,
                                            "timestamp": datetime.utcnow().isoformat()
                                        })
                                    except Exception as e:
                                        logger.warning(f"Failed to broadcast analytics: {e}")
                        
                        except Exception as e:
                            logger.warning(f"Error updating token {token_address}: {e}")
                            log_token_update("error")
                
                # Sleep between monitoring cycles
                await asyncio.sleep(getattr(self.settings, 'monitoring_interval', 60))
            
            except Exception as e:
                logger.exception(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Brief pause on error
    
    async def _get_market_data(self, token_address: str) -> Dict[str, Any]:
        """Get market data from multiple sources."""
        start_time = time.time()
        try:
            tasks = [
                self._get_dexscreener_data(token_address),
                self._get_birdeye_data(token_address)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            observe_monitor_latency("market_data", time.time() - start_time)
            
            market_data = {}
            for result in results:
                if isinstance(result, dict):
                    market_data.update(result)
            
            return market_data
            
    async def _get_dexscreener_data(self, token_address: str) -> Dict[str, Any]:
        """Get token data from Dexscreener."""
        try:
            pairs = await self.dexscreener.get_token_pairs(token_address)
            if not pairs:
                return {}
                
            # Use the first pair with the most liquidity
            pairs.sort(key=lambda p: p.liquidity_usd, reverse=True)
            pair = pairs[0]
            
            return {
                "price": pair.price_usd,
                "liquidity": pair.liquidity_usd,
                "volume_24h": pair.volume_24h,
                "price_change_24h": pair.price_change_24h,
                "dex": pair.dex
            }
        except Exception as e:
            logger.error(f"Error getting Dexscreener data: {e}")
            return {}
            
    async def _get_birdeye_data(self, token_address: str) -> Dict[str, Any]:
        """Get token data from Birdeye."""
        try:
            price_data = await self.birdeye.get_token_price(token_address)
            return {
                "price": price_data.price_usd,
                "market_cap": price_data.market_cap,
                "liquidity": price_data.liquidity,
                "volume_24h": price_data.volume_24h,
                "price_change_24h": price_data.price_change_24h,
                "holder_count": price_data.holders
            }
        except Exception as e:
            logger.error(f"Error getting Birdeye data: {e}")
            return {}
    
    async def _store_token_data(self, db: Session, token_data: Dict[str, Any]):
        """Store token data in the database."""
        address = token_data["address"]
        try:
            logger.info(f"_store_token_data: session={db} thread={threading.get_ident()}")
            # Only use direct session calls (no run_db_query)
            token = db.query(Token).filter(Token.address == address).first()
            logger.info(f"_store_token_data: after token query, thread={threading.get_ident()}")
            if not token:
                token = Token(address=address)
                db.add(token)
                db.flush()
                logger.info(f"_store_token_data: after token add/flush, thread={threading.get_ident()}")
            # Debug log for price
            logger.info(f"_store_token_data: token_data['price']={token_data.get('price')} type={type(token_data.get('price'))}")
            metrics = TokenMetrics(
                token_id=token.id,
                price=float(token_data.get("price", 0)),
                volume_24h=float(token_data.get("volume_24h", 0)),
                market_cap=float(token_data.get("market_cap", 0)),
                liquidity=float(token_data.get("liquidity", 0)),
                holder_count=token_data.get("holder_count", 0),
                buy_count_24h=token_data.get("buys_24h", 0),
                sell_count_24h=token_data.get("sells_24h", 0),
                price_change_24h=float(token_data.get("price_change_24h", 0))
            )
            logger.info(f"_store_token_data: metrics.price={metrics.price} type={type(metrics.price)}")
            db.add(metrics)
            db.flush()
            logger.info(f"_store_token_data: after metrics add/flush, thread={threading.get_ident()}")
            db.commit()
            logger.info(f"_store_token_data: after commit, thread={threading.get_ident()}")
            # Store score
            if "score" in token_data:
                score_data = token_data["score"]
                score = TokenScoreModel(
                    token_id=token.id,
                    liquidity_score=score_data.get("liquidity_score", 0),
                    contract_safety_score=score_data.get("contract_safety_score", 0),
                    ownership_score=score_data.get("ownership_score", 0),
                    liquidity_lock_score=score_data.get("liquidity_lock_score", 0),
                    honeypot_risk_score=score_data.get("honeypot_risk_score", 0),
                    mention_frequency_score=score_data.get("mention_frequency_score", 0),
                    source_reliability_score=score_data.get("source_reliability_score", 0),
                    sentiment_score=score_data.get("sentiment_score", 0),
                    liquidity_composite=score_data.get("liquidity_composite", 0),
                    safety_composite=score_data.get("safety_composite", 0),
                    social_composite=score_data.get("social_composite", 0),
                    total_score=score_data.get("total_score", 0),
                    raw_metrics=score_data
                )
                db.add(score)
                db.flush()
                db.commit()
                logger.info(f"_store_token_data: after score add/flush/commit, thread={threading.get_ident()}")
            # Alert generation: check for alerts and store them
            from src.core.services.alert_service import AlertService
            # Re-fetch token to ensure id is an int
            token = db.query(Token).filter(Token.address == address).first()
            if token is not None and isinstance(token.id, int):
                alerts = await AlertService(db).check_alerts(token.id)
                for alert in alerts:
                    db.add(alert)
                if alerts:
                    db.commit()
                    logger.info(f"_store_token_data: {len(alerts)} alerts generated and committed.")
            else:
                logger.warning(f"_store_token_data: Could not generate alerts, token or token.id invalid for address {address}")
        except Exception as e:
            logger.exception(f"Error storing token data: {e}")
            db.rollback()

    async def get_tracked_count(self) -> int:
        """Get number of tokens currently being tracked."""
        try:
            async with async_db_session() as session:
                return await run_db_query(session, lambda s: s.query(Token).count())
        except Exception as e:
            logger.error(f"Error getting tracked count: {e}")
            return 0

    async def get_mentions_today(self) -> int:
        """Get number of token mentions today."""
        today = datetime.utcnow().date()
        try:
            async with async_db_session() as session:
                return await run_db_query(
                    session, 
                    lambda s, d: s.query(TokenMention).filter(TokenMention.mentioned_at >= d).count(),
                    today
                )
        except Exception as e:
            logger.error(f"Error getting mentions count: {e}")
            return 0

    async def get_active_alerts_count(self) -> int:
        """Get number of active alerts."""
        try:
            async with async_db_session() as session:
                return await run_db_query(
                    session,
                    lambda s: s.query(Alert).filter(Alert.is_deleted == False).count()
                )
        except Exception as e:
            logger.error(f"Error getting alerts count: {e}")
            return 0

    async def get_system_status(self) -> dict:
        """Get overall system status metrics."""
        return {
            "is_running": self.is_running,
            "uptime_hours": (datetime.utcnow() - self.start_time).total_seconds() / 3600 if self.start_time else 0,
            "messages_processed": self.messages_processed,
            "errors_last_hour": self.errors_last_hour,
            "api_status": await self._check_api_status(),
            "memory_usage_mb": self._get_memory_usage()
        }

    async def _check_api_status(self) -> dict:
        """Check status of connected APIs."""
        statuses = {}
        apis = [
            ("birdeye", self.birdeye_client),
            ("rugcheck", self.rugcheck_client),
            ("dexscreener", self.dexscreener_client),
            ("pumpfun", self.pumpfun_client),
            ("bonkfun", self.bonkfun_client)
        ]
        
        for name, client in apis:
            try:
                await client.check_status()
                statuses[name] = "healthy"
            except Exception as e:
                logger.warning(f"API {name} health check failed: {e}")
                statuses[name] = "error"
        
        return statuses

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024  # Convert to MB

    async def update_token(self, token_address: str, db: Session):
        """Update a single token's metrics and store in the database (for testing and manual update)."""
        try:
            # Get fresh market data
            market_data = await self._get_market_data(token_address)
            # Track market changes (optional, not used in DB)
            self.previous_market_data[token_address] = market_data
            # Get fresh momentum data
            try:
                momentum_data = await self.analyzer.get_token_momentum(token_address)
            except Exception as e:
                logger.warning(f"Error getting momentum data for {token_address}: {e}")
                momentum_data = {}
            # Combine data for analysis
            token_data = {
                **market_data,
                "momentum": momentum_data,
                "address": token_address
            }
            # Create TokenMetrics object for scoring
            metrics = TokenMetrics()
            if 'price' in token_data:
                metrics.price = token_data['price']
            if 'market_cap' in token_data:
                metrics.market_cap = token_data['market_cap']
            if 'volume_24h' in token_data:
                metrics.volume_24h = token_data['volume_24h']
            if 'liquidity' in token_data:
                metrics.liquidity = token_data['liquidity']
            if 'holder_count' in token_data:
                metrics.holder_count = token_data['holder_count']
            # Update score with new data
            score = await self.scorer.get_token_score(token_address, metrics)
            token_data["score"] = score.to_dict()
            # Store in database
            await self._store_token_data(db, token_data)
        except Exception as e:
            logger.exception(f"Error updating token {token_address}: {e}")
            raise