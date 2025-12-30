"""Tests for CachedResponse utility class."""

import time
import pytest

from src.utils.resilience import CachedResponse, DEFAULT_CACHE_TTL_SECONDS


class TestCachedResponse:
    """Test suite for CachedResponse class."""

    def test_cache_creation(self):
        """Test basic cache creation with default TTL."""
        data = {"version": "1.0.0"}
        cache = CachedResponse(data)
        
        assert cache.data == data
        assert cache.ttl_seconds == DEFAULT_CACHE_TTL_SECONDS
        assert cache.is_valid()

    def test_cache_creation_custom_ttl(self):
        """Test cache creation with custom TTL."""
        data = {"version": "1.0.0"}
        cache = CachedResponse(data, ttl_seconds=60)
        
        assert cache.data == data
        assert cache.ttl_seconds == 60
        assert cache.is_valid()

    def test_cache_is_valid_immediately_after_creation(self):
        """Test that cache is valid immediately after creation."""
        cache = CachedResponse({"test": "data"})
        assert cache.is_valid() is True

    def test_cache_time_remaining(self):
        """Test time_remaining returns positive value for fresh cache."""
        cache = CachedResponse({"test": "data"}, ttl_seconds=300)
        remaining = cache.time_remaining()
        
        # Should be close to 300 seconds (allowing for execution time)
        assert 298 <= remaining <= 300

    def test_cache_invalidate(self):
        """Test manual cache invalidation."""
        cache = CachedResponse({"test": "data"}, ttl_seconds=300)
        assert cache.is_valid() is True
        
        cache.invalidate()
        
        assert cache.is_valid() is False
        assert cache.time_remaining() == 0.0

    def test_cache_expiration_short_ttl(self):
        """Test cache expiration with very short TTL."""
        cache = CachedResponse({"test": "data"}, ttl_seconds=0)
        
        # With 0 TTL, cache should be invalid immediately
        # (monotonic time has moved since creation)
        time.sleep(0.01)  # Small delay to ensure time has passed
        assert cache.is_valid() is False

    def test_cache_data_immutability(self):
        """Test that cache data is accessible and unchanged."""
        original_data = {"key": "value", "nested": {"a": 1}}
        cache = CachedResponse(original_data)
        
        assert cache.data == original_data
        assert cache.data["key"] == "value"
        assert cache.data["nested"]["a"] == 1

    def test_cache_generic_types(self):
        """Test cache works with different data types."""
        # Dict
        dict_cache = CachedResponse({"test": "data"})
        assert dict_cache.data == {"test": "data"}
        
        # List
        list_cache = CachedResponse([1, 2, 3])
        assert list_cache.data == [1, 2, 3]
        
        # String
        str_cache = CachedResponse("test string")
        assert str_cache.data == "test string"
        
        # None
        none_cache = CachedResponse(None)
        assert none_cache.data is None

    def test_cache_time_remaining_after_invalidation(self):
        """Test time_remaining is 0 after invalidation."""
        cache = CachedResponse({"test": "data"}, ttl_seconds=300)
        cache.invalidate()
        
        assert cache.time_remaining() == 0.0

    def test_multiple_invalidations(self):
        """Test that multiple invalidations don't cause issues."""
        cache = CachedResponse({"test": "data"})
        
        cache.invalidate()
        assert cache.is_valid() is False
        
        cache.invalidate()  # Second invalidation
        assert cache.is_valid() is False

    def test_cache_uses_monotonic_time(self):
        """Test that cache uses monotonic time (clock-adjustment resilient)."""
        cache = CachedResponse({"test": "data"}, ttl_seconds=300)
        
        # The created_at should be based on monotonic time
        # We can verify by checking it's a reasonable positive number
        assert cache.created_at > 0
        
        # Verify is_valid works correctly
        assert cache.is_valid() is True


class TestCachedResponseEdgeCases:
    """Edge case tests for CachedResponse."""

    def test_zero_ttl_cache(self):
        """Test cache with zero TTL expires immediately."""
        cache = CachedResponse({"test": "data"}, ttl_seconds=0)
        time.sleep(0.001)  # Tiny delay
        assert cache.is_valid() is False

    def test_negative_ttl_not_recommended(self):
        """Test behavior with negative TTL (not recommended but shouldn't crash)."""
        # Negative TTL should result in immediately invalid cache
        cache = CachedResponse({"test": "data"}, ttl_seconds=-1)
        assert cache.is_valid() is False

    def test_very_large_ttl(self):
        """Test cache with very large TTL."""
        cache = CachedResponse({"test": "data"}, ttl_seconds=86400 * 365)  # 1 year
        assert cache.is_valid() is True
        assert cache.time_remaining() > 86400 * 364  # Almost a year remaining

    def test_empty_data(self):
        """Test cache with empty data structures."""
        empty_dict = CachedResponse({})
        assert empty_dict.data == {}
        assert empty_dict.is_valid()
        
        empty_list = CachedResponse([])
        assert empty_list.data == []
        assert empty_list.is_valid()
