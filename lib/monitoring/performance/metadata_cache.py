"""Metadata caching to reduce repeated calculations."""

import functools
import time
from typing import Any, Dict, Optional, Tuple
from collections import OrderedDict
import threading


class MetadataCache:
    """
    LRU cache for function metadata to avoid repeated calculations.
    
    Caches:
    - Module and qualname lookups
    - Source file paths
    - Function signatures
    - Common serialized values
    """
    
    def __init__(self, max_size: int = 10000, ttl_seconds: float = 3600):
        """
        Initialize cache with size limit and TTL.
        
        Args:
            max_size: Maximum number of entries to cache
            ttl_seconds: Time-to-live for cache entries in seconds
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            value, timestamp = self._cache[key]
            
            # Check if expired
            if time.time() - timestamp > self.ttl_seconds:
                del self._cache[key]
                self._misses += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache with current timestamp.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        with self._lock:
            # Remove oldest if at capacity
            if len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
            
            self._cache[key] = (value, time.time())
    
    def cache_function_metadata(self, func: Any) -> Dict[str, Any]:
        """
        Cache and return function metadata.
        
        Args:
            func: Function to get metadata for
            
        Returns:
            Dictionary with module, qualname, file, etc.
        """
        # Use stable key based on module and qualname
        module = getattr(func, "__module__", "unknown")
        qualname = getattr(func, "__qualname__", func.__name__)
        cache_key = f"func_meta_{module}.{qualname}"
        
        # Check cache first
        cached = self.get(cache_key)
        if cached is not None:
            return cached
        
        # Calculate metadata
        metadata = {
            "module": module,
            "qualname": qualname,
            "name": func.__name__,
        }
        
        # Try to get source file
        try:
            import inspect
            metadata["file"] = inspect.getfile(func)
        except:
            metadata["file"] = "unknown"
        
        # Cache and return
        self.set(cache_key, metadata)
        return metadata
    
    def cache_serialized(self, obj: Any, serialized: Any) -> None:
        """
        Cache serialized version of an object.
        
        Uses object id as key for mutable objects.
        Uses value as key for immutable objects.
        """
        if isinstance(obj, (str, int, float, bool, type(None))):
            # Immutable - use value as key
            key = f"ser_val_{type(obj).__name__}_{obj}"
        else:
            # Mutable - use id
            key = f"ser_id_{id(obj)}"
        
        self.set(key, serialized)
    
    def get_serialized(self, obj: Any) -> Optional[Any]:
        """
        Get cached serialized version if available.
        """
        if isinstance(obj, (str, int, float, bool, type(None))):
            key = f"ser_val_{type(obj).__name__}_{obj}"
        else:
            key = f"ser_id_{id(obj)}"
        
        return self.get(key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0
            
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "ttl_seconds": self.ttl_seconds
            }
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0


# Global cache instance
_metadata_cache = MetadataCache()


def get_metadata_cache() -> MetadataCache:
    """Get the global metadata cache instance."""
    return _metadata_cache 