"""
Cache Management System
Handles Redis caching for improved performance
"""
import json
import pickle
import asyncio
import logging
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import hashlib
import os

logger = logging.getLogger(__name__)

class CacheManager:
    """In-memory cache manager with TTL support"""
    
    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_cache: Dict[str, datetime] = {}
        self.max_cache_size = 1000
        self.default_ttl = 3600  # 1 hour
        
        # Performance tracking
        self.hit_count = 0
        self.miss_count = 0
        self.total_requests = 0
        self.last_cleanup_time = datetime.now()
        
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache with performance tracking"""
        try:
            self.total_requests += 1
            
            # Check if key exists and hasn't expired
            if key in self.cache and key in self.ttl_cache:
                if datetime.now() < self.ttl_cache[key]:
                    self.hit_count += 1
                    # Update access count
                    self.cache[key]["access_count"] = self.cache[key].get("access_count", 0) + 1
                    self.cache[key]["last_accessed"] = datetime.now()
                    return self.cache[key].get("value")
                else:
                    # Remove expired key
                    await self.delete(key)
            
            self.miss_count += 1
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL"""
        try:
            # Use default TTL if not provided
            if ttl is None:
                ttl = self.default_ttl
            
            # Check cache size and cleanup if necessary
            if len(self.cache) >= self.max_cache_size:
                await self._cleanup_expired()
                
                # If still too large, remove oldest entries
                if len(self.cache) >= self.max_cache_size:
                    await self._remove_oldest()
            
            # Set cache value with metadata
            self.cache[key] = {
                "value": value,
                "created_at": datetime.now(),
                "access_count": 0,
                "last_accessed": datetime.now()
            }
            
            # Set TTL
            self.ttl_cache[key] = datetime.now() + timedelta(seconds=ttl)
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            if key in self.cache:
                del self.cache[key]
            if key in self.ttl_cache:
                del self.ttl_cache[key]
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    async def clear(self) -> bool:
        """Clear entire cache"""
        try:
            self.cache.clear()
            self.ttl_cache.clear()
            return True
            
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    async def _cleanup_expired(self):
        """Remove expired cache entries"""
        current_time = datetime.now()
        expired_keys = [
            key for key, expiry in self.ttl_cache.items()
            if current_time >= expiry
        ]
        
        for key in expired_keys:
            await self.delete(key)
        
        # Update last cleanup time
        self.last_cleanup_time = current_time
    
    async def _remove_oldest(self):
        """Remove oldest cache entries when max size reached"""
        if not self.cache:
            return
            
        # Sort by creation time and remove oldest 10%
        sorted_keys = sorted(
            self.cache.keys(),
            key=lambda k: self.cache[k]["created_at"]
        )
        
        remove_count = max(1, len(sorted_keys) // 10)
        for key in sorted_keys[:remove_count]:
            await self.delete(key)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics with performance metrics"""
        await self._cleanup_expired()
        
        total_size = len(self.cache)
        total_access = sum(
            item["access_count"] for item in self.cache.values()
        )
        
        # Calculate hit rate
        hit_rate = (self.hit_count / max(self.total_requests, 1)) * 100
        miss_rate = (self.miss_count / max(self.total_requests, 1)) * 100
        
        # Calculate memory usage estimation
        memory_usage_mb = sum(
            len(str(item["value"])) for item in self.cache.values()
        ) / (1024 * 1024)
        
        # Time since last cleanup
        time_since_cleanup = (datetime.now() - self.last_cleanup_time).total_seconds()
        
        return {
            "total_keys": total_size,
            "total_access": total_access,
            "max_size": self.max_cache_size,
            "hit_ratio": total_access / max(total_size, 1),
            "performance_metrics": {
                "hit_count": self.hit_count,
                "miss_count": self.miss_count,
                "total_requests": self.total_requests,
                "hit_rate_percent": round(hit_rate, 2),
                "miss_rate_percent": round(miss_rate, 2),
                "memory_usage_mb": round(memory_usage_mb, 2),
                "time_since_cleanup_seconds": round(time_since_cleanup, 2)
            },
            "cache_efficiency": {
                "utilization_percent": round((total_size / self.max_cache_size) * 100, 2),
                "average_access_per_key": round(total_access / max(total_size, 1), 2)
            }
        }
    
    def create_cache_key(self, *args, **kwargs) -> str:
        """Create consistent cache key from arguments"""
        key_data = {
            "args": args,
            "kwargs": kwargs,
            "timestamp": datetime.now().strftime("%Y%m%d")
        }
        
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()

# Global cache manager instance
cache_manager = CacheManager()

# Decorator for caching function results
def cache_result(ttl: int = 3600):
    """Decorator to cache function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = cache_manager.create_cache_key(
                func.__name__, *args, **kwargs
            )
            
            # Try to get from cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator