"""Redis-based caching implementation."""
from typing import Any, Dict, Optional, Union
import json
try:
    import redis.asyncio as redis
except ImportError:
    # Fallback to synchronous redis with async wrapper
    import redis
    
from loguru import logger

from ..config.settings import get_settings

settings = get_settings()

class RedisCache:
    """Redis-based cache with TTL support."""

    def __init__(self, ttl_seconds: int = 300) -> None:
        """Initialize Redis cache with TTL."""
        self._ttl_seconds = ttl_seconds
        self._redis: Optional[redis.Redis] = None
        self._fallback_cache: Dict[str, Any] = {}

    async def initialize(self) -> None:
        """Initialize Redis connection."""
        if not self._redis:
            try:
                redis_url = str(settings.redis_url) if settings.redis_url else None
                if redis_url:
                    self._redis = redis.Redis.from_url(
                        redis_url,
                        encoding='utf-8',
                        decode_responses=True
                    )
                else:
                    logger.warning("No Redis URL configured. Using in-memory fallback for rate limiting.")
                    self._fallback_cache = {}
            except Exception as e:
                logger.error(f"Failed to initialize Redis cache: {e}")
                # Provide a fallback mechanism for tests
                logger.warning("Using dictionary-based cache as fallback")
                self._fallback_cache = {}
                return

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            try:
                if hasattr(self._redis, 'close'):
                    close_result = self._redis.close()
                    if hasattr(close_result, '__await__'):
                        await close_result
            except Exception:
                pass  # Ignore close errors
            self._redis = None

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self._redis:
            try:
                await self.initialize()
            except Exception as e:
                # Use fallback cache
                return self._fallback_cache.get(key)

        try:
            if self._redis is None:
                return self._fallback_cache.get(key)
                
            value = await self._redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """Set value in cache with TTL."""
        if not self._redis:
            try:
                await self.initialize()
            except Exception as e:
                # Use fallback cache
                self._fallback_cache[key] = value
                return True

        try:
            if self._redis is None:
                self._fallback_cache[key] = value
                return True
                
            ttl = ttl_seconds if ttl_seconds is not None else self._ttl_seconds
            serialized = json.dumps(value)
            await self._redis.set(
                key,
                serialized,
                ex=ttl
            )
            return True
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self._redis:
            try:
                await self.initialize()
            except Exception as e:
                # Use fallback cache
                if key in self._fallback_cache:
                    del self._fallback_cache[key]
                return True

        try:
            if self._redis is None:
                if key in self._fallback_cache:
                    del self._fallback_cache[key]
                return True
                
            await self._redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False

    async def clear(self) -> bool:
        """Clear all cache entries."""
        if not self._redis:
            try:
                await self.initialize()
            except Exception as e:
                # Use fallback cache
                self._fallback_cache.clear()
                return True

        try:
            if self._redis is None:
                self._fallback_cache.clear()
                return True
                
            await self._redis.flushdb()
            return True
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return False
