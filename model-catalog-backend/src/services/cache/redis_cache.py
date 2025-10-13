"""Redis cache implementation for high-performance caching."""

import json
import pickle
from typing import Any, Optional, Union
from datetime import timedelta
import redis
from redis.exceptions import RedisError

from src.core.config import settings
from src.core.exceptions import CacheError


class RedisCache:
    """Redis cache implementation with high-performance features."""
    
    def __init__(self, redis_url: Optional[str] = None):
        """Initialize Redis cache connection."""
        self.redis_url = redis_url or getattr(settings, 'REDIS_URL', 'redis://localhost:6379')
        self.redis_client = redis.from_url(self.redis_url, decode_responses=False)
        
        # Test connection
        try:
            self.redis_client.ping()
        except RedisError as e:
            raise CacheError(f"Failed to connect to Redis: {str(e)}")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
            
            # Try to deserialize as JSON first, then pickle
            try:
                return json.loads(value.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return pickle.loads(value)
                
        except RedisError as e:
            raise CacheError(f"Failed to get key {key}: {str(e)}")
    
    def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set value in cache with optional TTL."""
        try:
            # Try to serialize as JSON first, fallback to pickle
            try:
                serialized_value = json.dumps(value).encode('utf-8')
            except (TypeError, ValueError):
                serialized_value = pickle.dumps(value)
            
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            
            return self.redis_client.set(key, serialized_value, ex=ttl)
            
        except RedisError as e:
            raise CacheError(f"Failed to set key {key}: {str(e)}")
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            return bool(self.redis_client.delete(key))
        except RedisError as e:
            raise CacheError(f"Failed to delete key {key}: {str(e)}")
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return bool(self.redis_client.exists(key))
        except RedisError as e:
            raise CacheError(f"Failed to check key {key}: {str(e)}")
    
    def get_ttl(self, key: str) -> int:
        """Get TTL for a key in seconds."""
        try:
            return self.redis_client.ttl(key)
        except RedisError as e:
            raise CacheError(f"Failed to get TTL for key {key}: {str(e)}")
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern."""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except RedisError as e:
            raise CacheError(f"Failed to clear pattern {pattern}: {str(e)}")
    
    def increment(self, key: str, amount: int = 1) -> int:
        """Increment a counter in cache."""
        try:
            return self.redis_client.incr(key, amount)
        except RedisError as e:
            raise CacheError(f"Failed to increment key {key}: {str(e)}")
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        try:
            info = self.redis_client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(info)
            }
        except RedisError as e:
            raise CacheError(f"Failed to get cache stats: {str(e)}")
    
    def _calculate_hit_rate(self, info: dict) -> float:
        """Calculate cache hit rate."""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return round((hits / total) * 100, 2)
    
    def close(self):
        """Close Redis connection."""
        try:
            self.redis_client.close()
        except RedisError:
            pass  # Ignore errors when closing


# Global cache instance
cache = RedisCache()
