"""
Simple in-memory caching utility with TTL support.
"""
import time
from typing import Any, Optional, Dict, Tuple
from functools import wraps
import asyncio


class SimpleCache:
    """Thread-safe in-memory cache with TTL support."""
    
    def __init__(self):
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        async with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if time.time() < expiry:
                    return value
                else:
                    # Expired, remove it
                    del self._cache[key]
            return None
    
    async def set(self, key: str, value: Any, ttl_seconds: int):
        """Set value in cache with TTL in seconds."""
        async with self._lock:
            expiry = time.time() + ttl_seconds
            self._cache[key] = (value, expiry)
    
    async def clear(self):
        """Clear all cached values."""
        async with self._lock:
            self._cache.clear()


# Global cache instance
_global_cache = SimpleCache()


def cached(ttl_seconds: int):
    """
    Decorator to cache async function results with TTL.
    
    Args:
        ttl_seconds: Time to live in seconds
    
    Usage:
        @cached(ttl_seconds=60)
        async def my_function(arg1, arg2):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached_value = await _global_cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await _global_cache.set(cache_key, result, ttl_seconds)
            return result
        
        return wrapper
    return decorator


async def clear_cache():
    """Clear the global cache."""
    await _global_cache.clear()
