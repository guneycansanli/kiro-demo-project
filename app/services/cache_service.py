"""
Cache service for storing weather data and location lookups.

Implements an in-memory cache with TTL-based expiration and LRU eviction.
"""

import threading
import time
from typing import Any, Optional, Dict, Tuple
from collections import OrderedDict


class CacheService:
    """
    Thread-safe in-memory cache with TTL expiration and LRU eviction.
    
    The cache stores values with expiration timestamps and automatically
    removes expired entries on access. When the cache reaches its maximum
    size, it evicts the least recently used entry.
    """
    
    def __init__(self, max_size: int = 100, default_ttl: int = 300):
        """
        Initialize the cache service.
        
        Args:
            max_size: Maximum number of entries in the cache
            default_ttl: Default time-to-live in seconds (default: 300 = 5 minutes)
        """
        self._cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._lock = threading.Lock()
        self._max_size = max_size
        self._default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache.
        
        Automatically removes expired entries and updates access order for LRU.
        
        Args:
            key: The cache key
            
        Returns:
            The cached value if found and not expired, None otherwise
        """
        with self._lock:
            if key not in self._cache:
                return None
            
            value, expiration = self._cache[key]
            
            # Check if entry has expired
            if time.time() > expiration:
                # Remove expired entry
                del self._cache[key]
                return None
            
            # Move to end to mark as recently used (LRU)
            self._cache.move_to_end(key)
            
            return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Store a value in the cache with TTL.
        
        If the cache is full, evicts the least recently used entry.
        
        Args:
            key: The cache key
            value: The value to cache
            ttl: Time-to-live in seconds (uses default_ttl if not specified)
        """
        with self._lock:
            # Use default TTL if not specified
            if ttl is None:
                ttl = self._default_ttl
            
            # Calculate expiration timestamp
            expiration = time.time() + ttl
            
            # If key already exists, update it
            if key in self._cache:
                self._cache[key] = (value, expiration)
                self._cache.move_to_end(key)
                return
            
            # If cache is full, evict least recently used (first item)
            if len(self._cache) >= self._max_size:
                # Remove the first (least recently used) item
                self._cache.popitem(last=False)
            
            # Add new entry
            self._cache[key] = (value, expiration)
    
    def clear(self) -> None:
        """
        Clear all entries from the cache.
        """
        with self._lock:
            self._cache.clear()
    
    def size(self) -> int:
        """
        Get the current number of entries in the cache.
        
        Returns:
            Number of entries currently in the cache
        """
        with self._lock:
            return len(self._cache)
    
    def _cleanup_expired(self) -> None:
        """
        Remove all expired entries from the cache.
        
        This is an internal method for testing and maintenance.
        """
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, (_, expiration) in self._cache.items()
                if current_time > expiration
            ]
            for key in expired_keys:
                del self._cache[key]
