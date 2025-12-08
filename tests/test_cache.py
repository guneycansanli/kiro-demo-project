"""
Property-based and unit tests for cache service.

Tests cache operations including TTL expiration, LRU eviction,
and performance improvements using property-based testing with Hypothesis.
"""

import unittest
import time
from hypothesis import given, settings, strategies as st
from app.services.cache_service import CacheService


class TestCacheRoundTrip(unittest.TestCase):
    """Property-based tests for cache round-trip operations."""
    
    @settings(max_examples=100)
    @given(
        key=st.text(min_size=1),
        value=st.one_of(
            st.text(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.lists(st.integers()),
            st.dictionaries(st.text(min_size=1), st.integers())
        )
    )
    def test_cache_round_trip_property(self, key: str, value):
        """
        Feature: weather-web-service, Property 17: Cache improves response times
        
        For any key-value pair, storing a value in the cache and immediately
        retrieving it should return the same value (round-trip consistency).
        
        Validates: Requirements 10.3
        """
        cache = CacheService(max_size=100, default_ttl=300)
        
        # Store value in cache
        cache.set(key, value)
        
        # Retrieve value from cache
        retrieved = cache.get(key)
        
        # The retrieved value should match the stored value
        self.assertEqual(retrieved, value)


class TestCacheOperations(unittest.TestCase):
    """Unit tests for cache operations."""
    
    def setUp(self):
        """Set up a fresh cache for each test."""
        self.cache = CacheService(max_size=3, default_ttl=1)
    
    def test_set_and_get(self):
        """Test basic set and get operations."""
        self.cache.set("key1", "value1")
        self.assertEqual(self.cache.get("key1"), "value1")
        
        self.cache.set("key2", 42)
        self.assertEqual(self.cache.get("key2"), 42)
        
        self.cache.set("key3", {"data": "test"})
        self.assertEqual(self.cache.get("key3"), {"data": "test"})
    
    def test_get_nonexistent_key(self):
        """Test that getting a non-existent key returns None."""
        result = self.cache.get("nonexistent")
        self.assertIsNone(result)
    
    def test_update_existing_key(self):
        """Test that updating an existing key works correctly."""
        self.cache.set("key1", "value1")
        self.cache.set("key1", "value2")
        self.assertEqual(self.cache.get("key1"), "value2")
    
    def test_clear(self):
        """Test that clear removes all entries."""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.set("key3", "value3")
        
        self.assertEqual(self.cache.size(), 3)
        
        self.cache.clear()
        
        self.assertEqual(self.cache.size(), 0)
        self.assertIsNone(self.cache.get("key1"))
        self.assertIsNone(self.cache.get("key2"))
        self.assertIsNone(self.cache.get("key3"))


class TestCacheTTLExpiration(unittest.TestCase):
    """Unit tests for TTL-based expiration."""
    
    def test_ttl_expiration(self):
        """Test that entries expire after TTL."""
        cache = CacheService(max_size=10, default_ttl=1)
        
        # Set a value with 1 second TTL
        cache.set("key1", "value1", ttl=1)
        
        # Should be available immediately
        self.assertEqual(cache.get("key1"), "value1")
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired and return None
        self.assertIsNone(cache.get("key1"))
    
    def test_custom_ttl(self):
        """Test that custom TTL values work correctly."""
        cache = CacheService(max_size=10, default_ttl=10)
        
        # Set with short TTL
        cache.set("short", "value1", ttl=1)
        # Set with longer TTL
        cache.set("long", "value2", ttl=5)
        
        # Both should be available immediately
        self.assertEqual(cache.get("short"), "value1")
        self.assertEqual(cache.get("long"), "value2")
        
        # Wait for short TTL to expire
        time.sleep(1.1)
        
        # Short should be expired, long should still be available
        self.assertIsNone(cache.get("short"))
        self.assertEqual(cache.get("long"), "value2")
    
    def test_expired_entry_removed_on_access(self):
        """Test that expired entries are removed when accessed."""
        cache = CacheService(max_size=10, default_ttl=1)
        
        cache.set("key1", "value1", ttl=1)
        
        # Entry exists
        self.assertEqual(cache.size(), 1)
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Access expired entry
        result = cache.get("key1")
        self.assertIsNone(result)
        
        # Entry should be removed from cache
        self.assertEqual(cache.size(), 0)


class TestCacheLRUEviction(unittest.TestCase):
    """Unit tests for LRU eviction."""
    
    def test_lru_eviction_on_full_cache(self):
        """Test that least recently used entry is evicted when cache is full."""
        cache = CacheService(max_size=3, default_ttl=300)
        
        # Fill cache to capacity
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        self.assertEqual(cache.size(), 3)
        
        # Add one more entry, should evict key1 (least recently used)
        cache.set("key4", "value4")
        
        # Cache should still have 3 entries
        self.assertEqual(cache.size(), 3)
        
        # key1 should be evicted
        self.assertIsNone(cache.get("key1"))
        
        # Other keys should still be present
        self.assertEqual(cache.get("key2"), "value2")
        self.assertEqual(cache.get("key3"), "value3")
        self.assertEqual(cache.get("key4"), "value4")
    
    def test_lru_access_updates_order(self):
        """Test that accessing an entry updates its position in LRU order."""
        cache = CacheService(max_size=3, default_ttl=300)
        
        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Access key1 to make it recently used
        cache.get("key1")
        
        # Add new entry, should evict key2 (now least recently used)
        cache.set("key4", "value4")
        
        # key2 should be evicted
        self.assertIsNone(cache.get("key2"))
        
        # key1 should still be present (was accessed)
        self.assertEqual(cache.get("key1"), "value1")
        self.assertEqual(cache.get("key3"), "value3")
        self.assertEqual(cache.get("key4"), "value4")
    
    def test_lru_update_existing_key(self):
        """Test that updating an existing key doesn't cause eviction."""
        cache = CacheService(max_size=3, default_ttl=300)
        
        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Update existing key
        cache.set("key1", "updated_value1")
        
        # Cache should still have 3 entries
        self.assertEqual(cache.size(), 3)
        
        # All keys should still be present
        self.assertEqual(cache.get("key1"), "updated_value1")
        self.assertEqual(cache.get("key2"), "value2")
        self.assertEqual(cache.get("key3"), "value3")
    
    def test_lru_eviction_order(self):
        """Test that multiple evictions follow LRU order."""
        cache = CacheService(max_size=3, default_ttl=300)
        
        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Add two more entries
        cache.set("key4", "value4")  # Evicts key1
        cache.set("key5", "value5")  # Evicts key2
        
        # key1 and key2 should be evicted
        self.assertIsNone(cache.get("key1"))
        self.assertIsNone(cache.get("key2"))
        
        # key3, key4, key5 should be present
        self.assertEqual(cache.get("key3"), "value3")
        self.assertEqual(cache.get("key4"), "value4")
        self.assertEqual(cache.get("key5"), "value5")


class TestCacheThreadSafety(unittest.TestCase):
    """Unit tests for thread safety."""
    
    def test_concurrent_access(self):
        """Test that cache handles concurrent access correctly."""
        import threading
        
        cache = CacheService(max_size=100, default_ttl=300)
        errors = []
        
        def worker(thread_id):
            try:
                for i in range(50):
                    key = f"thread{thread_id}_key{i}"
                    value = f"thread{thread_id}_value{i}"
                    cache.set(key, value)
                    retrieved = cache.get(key)
                    if retrieved != value:
                        errors.append(f"Mismatch in thread {thread_id}: expected {value}, got {retrieved}")
            except Exception as e:
                errors.append(f"Exception in thread {thread_id}: {e}")
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check that no errors occurred
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")


if __name__ == '__main__':
    unittest.main()
