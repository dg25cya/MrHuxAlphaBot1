"""Cache utilities for storing temporary data."""
import asyncio
import json
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Optional, TypeVar, Callable, Dict

import redis
from loguru import logger

from ..config.settings import get_settings

settings = get_settings()

# Type variable for the function return type
T = TypeVar('T')

class Cache:
    """Redis-based cache implementation with in-memory fallback."""

    def __init__(self) -> None:
        """Initialize cache with Redis connection."""
        self._redis = None
        self._lock = asyncio.Lock()
        self._memory_cache: Dict[str, tuple[Any, float]] = {}  # {key: (value, expiration_timestamp)}
        self._redis_available = True  # Assume Redis is available until proven otherwise

    def _get_redis(self) -> Optional[redis.Redis]:
        """Get or create Redis connection."""
        if not self._redis_available:
            return None
        
        if self._redis is None:
            try:
                redis_url = settings.redis_url
                # Handle the case where redis_url is a pydantic model instead of a string
                if hasattr(redis_url, 'startswith'):
                    self._redis = redis.Redis.from_url(
                        redis_url,
                        encoding='utf-8',
                        decode_responses=True
                    )
                else:
                    logger.warning("Redis URL is not a string, using in-memory cache")
                    self._redis_available = False
                    return None
            except Exception as e:
                logger.error(f"Error connecting to Redis: {e}")
                self._redis_available = False
                return None
                
        return self._redis

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        # Try Redis first
        try:
            redis_client = self._get_redis()
            if redis_client:
                return redis_client.get(key)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self._redis_available = False
        
        # Fall back to in-memory cache
        if key in self._memory_cache:
            value, expiration = self._memory_cache[key]
            # Check if expired
            if expiration > datetime.now().timestamp():
                return value
            else:
                # Remove expired entry
                del self._memory_cache[key]
        
        return None

    async def set(
        self,
        key: str,
        value: str,
        expire: int = 3600  # 1 hour default
    ) -> bool:
        """Set value in cache with expiration."""
        # Try Redis first
        try:
            redis_client = self._get_redis()
            if redis_client:
                return redis_client.set(key, value, ex=expire)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            self._redis_available = False
        
        # Fall back to in-memory cache
        expiration = datetime.now().timestamp() + expire
        self._memory_cache[key] = (value, expiration)
        return True

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        success = False
        
        # Try Redis first
        try:
            redis_client = self._get_redis()
            if redis_client:
                success = bool(redis_client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            self._redis_available = False
        
        # Also check in-memory cache
        if key in self._memory_cache:
            del self._memory_cache[key]
            success = True
            
        return success
            
    def __call__(self, ttl: int = 3600) -> None:
        """Make the cache instance callable for use as a decorator."""
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Create a cache key from function name and arguments
                key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
                
                # Try to get cached value
                cached = await self.get(key)
                if cached:
                    try:
                        return json.loads(cached)
                    except Exception as e:
                        return cached
                        
                # If not cached, execute function and cache result
                result = await func(*args, **kwargs)
                try:
                    await self.set(key, json.dumps(result), expire=ttl)
                except Exception as e:
                    await self.set(key, str(result), expire=ttl)
                    
                return result
            return wrapper
        return decorator

# Global cache instance
cache = Cache()