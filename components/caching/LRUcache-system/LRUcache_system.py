"""
High-Performance LRU Cache System with TTL and Monitoring

A production-ready, thread-safe LRU cache implementation with:
- Time-To-Live (TTL) support
- Comprehensive metrics and monitoring
- Event-driven architecture with hooks
- Memory-efficient design with size limits
- Batch operations for improved performance
- Serialization support for persistence
"""

import threading
import time
import json
import pickle
import logging
from typing import Any, Dict, Optional, List, Callable, Generic, TypeVar, Tuple
from dataclasses import dataclass, field
from collections import OrderedDict
from enum import Enum
from contextlib import contextmanager
import heapq
from functools import wraps
import weakref

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

K = TypeVar('K')  # Key type
V = TypeVar('V')  # Value type

class CacheEventType(Enum):
    """Cache event types for monitoring and hooks"""
    HIT = "hit"
    MISS = "miss"
    SET = "set"
    DELETE = "delete"
    EXPIRE = "expire"
    EVICT = "evict"
    CLEAR = "clear"

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    value: Any
    access_time: float
    creation_time: float
    ttl: Optional[float] = None
    access_count: int = 0
    size: int = 0
    
    @property
    def is_expired(self) -> bool:
        """Check if entry has expired"""
        if self.ttl is None:
            return False
        return time.time() > self.creation_time + self.ttl
    
    @property
    def age(self) -> float:
        """Get entry age in seconds"""
        return time.time() - self.creation_time
    
    def touch(self):
        """Update access time and increment access count"""
        self.access_time = time.time()
        self.access_count += 1

@dataclass
class CacheMetrics:
    """Comprehensive cache metrics for monitoring"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    expirations: int = 0
    total_size: int = 0
    peak_size: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total_requests = self.hits + self.misses
        return self.hits / total_requests if total_requests > 0 else 0.0
    
    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate"""
        return 1.0 - self.hit_rate
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'sets': self.sets,
            'deletes': self.deletes,
            'evictions': self.evictions,
            'expirations': self.expirations,
            'total_size': self.total_size,
            'peak_size': self.peak_size,
            'hit_rate': self.hit_rate,
            'miss_rate': self.miss_rate
        }


class CacheHook:
    """
    Base class for cache event hooks. Override methods to handle cache events.
    """
    def on_hit(self, key: Any, value: Any, entry: CacheEntry):
        """Called when cache hit occurs."""
        pass

    def on_miss(self, key: Any):
        """Called when cache miss occurs."""
        pass

    def on_set(self, key: Any, value: Any, entry: CacheEntry):
        """Called when item is set in cache."""
        pass

    def on_delete(self, key: Any, entry: CacheEntry):
        """Called when item is deleted from cache."""
        pass

    def on_expire(self, key: Any, entry: CacheEntry):
        """Called when item expires."""
        pass

    def on_evict(self, key: Any, entry: CacheEntry):
        """Called when item is evicted."""
        pass

class LoggingHook(CacheHook):
    """
    Hook that logs cache events for observability.
    """
    def __init__(self, log_level: int = logging.INFO):
        self.log_level = log_level

    def on_hit(self, key: Any, value: Any, entry: CacheEntry):
        logger.log(self.log_level, f"Cache HIT: {key} (age: {entry.age:.2f}s)")

    def on_miss(self, key: Any):
        logger.log(self.log_level, f"Cache MISS: {key}")

    def on_set(self, key: Any, value: Any, entry: CacheEntry):
        logger.log(self.log_level, f"Cache SET: {key} (size: {entry.size} bytes)")

    def on_delete(self, key: Any, entry: CacheEntry):
        logger.log(self.log_level, f"Cache DELETE: {key}")

    def on_expire(self, key: Any, entry: CacheEntry):
        logger.log(self.log_level, f"Cache EXPIRE: {key} (age: {entry.age:.2f}s)")

    def on_evict(self, key: Any, entry: CacheEntry):
        logger.log(self.log_level, f"Cache EVICT: {key} (age: {entry.age:.2f}s)")

class LRUCache(Generic[K, V]):
    """
    High-performance, thread-safe LRU cache with advanced features:
    
    - LRU eviction policy with O(1) get/set operations
    - TTL (Time-To-Live) support with automatic cleanup
    - Comprehensive metrics and monitoring
    - Event hooks for observability
    - Memory-efficient with configurable size limits
    - Thread-safe operations
    - Batch operations for improved performance
    - Serialization support for persistence
    """
    
    def __init__(self, 
                 max_size: int = 1000,
                 default_ttl: Optional[float] = None,
                 enable_metrics: bool = True,
                 cleanup_interval: float = 60.0,
                 max_memory_mb: Optional[float] = None):
        
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.enable_metrics = enable_metrics
        self.cleanup_interval = cleanup_interval
        self.max_memory_bytes = max_memory_mb * 1024 * 1024 if max_memory_mb else None
        
        # Core data structures
        self._cache: OrderedDict[K, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        
        # Metrics
        self.metrics = CacheMetrics() if enable_metrics else None
        
        # Event hooks
        self._hooks: List[CacheHook] = []
        
        # TTL cleanup
        self._cleanup_thread = None
        self._should_stop = threading.Event()
        
        # Start cleanup thread if TTL is enabled
        if default_ttl is not None or cleanup_interval > 0:
            self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """Start background thread for TTL cleanup"""
        def cleanup_worker():
            while not self._should_stop.wait(self.cleanup_interval):
                try:
                    self._cleanup_expired()
                except Exception as e:
                    logger.error(f"Error during cache cleanup: {e}")
        
        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()
        logger.info("Cache cleanup thread started")
    
    def _cleanup_expired(self):
        """Remove expired entries from cache"""
        with self._lock:
            expired_keys = []
            for key, entry in self._cache.items():
                if entry.is_expired:
                    expired_keys.append(key)
            
            for key in expired_keys:
                entry = self._cache.pop(key)
                self._fire_hook_expire(key, entry)
                if self.metrics:
                    self.metrics.expirations += 1
    
    def _calculate_size(self, obj: Any) -> int:
        """Calculate approximate memory size of object"""
        try:
            return len(pickle.dumps(obj))
        except:
            return len(str(obj))
    
    def _fire_hook_hit(self, key: K, value: V, entry: CacheEntry):
        """Fire hit event hooks"""
        for hook in self._hooks:
            try:
                hook.on_hit(key, value, entry)
            except Exception as e:
                logger.error(f"Error in hit hook: {e}")
    
    def _fire_hook_miss(self, key: K):
        """Fire miss event hooks"""
        for hook in self._hooks:
            try:
                hook.on_miss(key)
            except Exception as e:
                logger.error(f"Error in miss hook: {e}")
    
    def _fire_hook_set(self, key: K, value: V, entry: CacheEntry):
        """Fire set event hooks"""
        for hook in self._hooks:
            try:
                hook.on_set(key, value, entry)
            except Exception as e:
                logger.error(f"Error in set hook: {e}")
    
    def _fire_hook_delete(self, key: K, entry: CacheEntry):
        """Fire delete event hooks"""
        for hook in self._hooks:
            try:
                hook.on_delete(key, entry)
            except Exception as e:
                logger.error(f"Error in delete hook: {e}")
    
    def _fire_hook_expire(self, key: K, entry: CacheEntry):
        """Fire expire event hooks"""
        for hook in self._hooks:
            try:
                hook.on_expire(key, entry)
            except Exception as e:
                logger.error(f"Error in expire hook: {e}")
    
    def _fire_hook_evict(self, key: K, entry: CacheEntry):
        """Fire evict event hooks"""
        for hook in self._hooks:
            try:
                hook.on_evict(key, entry)
            except Exception as e:
                logger.error(f"Error in evict hook: {e}")
    
    def _evict_lru(self):
        """Evict least recently used item"""
        if not self._cache:
            return
        
        # Get LRU item (first item in OrderedDict)
        lru_key = next(iter(self._cache))
        entry = self._cache.pop(lru_key)
        
        self._fire_hook_evict(lru_key, entry)
        
        if self.metrics:
            self.metrics.evictions += 1
            self.metrics.total_size -= entry.size
    
    def _check_memory_limit(self) -> bool:
        """Check if memory limit is exceeded"""
        if self.max_memory_bytes is None:
            return False
        
        if self.metrics:
            return self.metrics.total_size > self.max_memory_bytes
        
        return False
    
    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """Get value from cache with LRU update"""
        with self._lock:
            if key not in self._cache:
                self._fire_hook_miss(key)
                if self.metrics:
                    self.metrics.misses += 1
                return default
            
            entry = self._cache[key]
            
            # Check expiration
            if entry.is_expired:
                self._cache.pop(key)
                self._fire_hook_expire(key, entry)
                self._fire_hook_miss(key)
                if self.metrics:
                    self.metrics.misses += 1
                    self.metrics.expirations += 1
                return default
            
            # Update LRU order and access metadata
            self._cache.move_to_end(key)
            entry.touch()
            
            self._fire_hook_hit(key, entry.value, entry)
            if self.metrics:
                self.metrics.hits += 1
            
            return entry.value
    
    def set(self, key: K, value: V, ttl: Optional[float] = None) -> None:
        """Set value in cache with optional TTL"""
        with self._lock:
            current_time = time.time()
            effective_ttl = ttl if ttl is not None else self.default_ttl
            
            # Calculate entry size
            entry_size = self._calculate_size(value)
            
            # Create cache entry
            entry = CacheEntry(
                value=value,
                access_time=current_time,
                creation_time=current_time,
                ttl=effective_ttl,
                access_count=1,
                size=entry_size
            )
            
            # If key already exists, update it
            if key in self._cache:
                old_entry = self._cache[key]
                if self.metrics:
                    self.metrics.total_size -= old_entry.size
            
            # Add to cache
            self._cache[key] = entry
            self._cache.move_to_end(key)
            
            # Update metrics
            if self.metrics:
                self.metrics.sets += 1
                self.metrics.total_size += entry_size
                self.metrics.peak_size = max(self.metrics.peak_size, self.metrics.total_size)
            
            # Evict if necessary
            while len(self._cache) > self.max_size or self._check_memory_limit():
                self._evict_lru()
            
            self._fire_hook_set(key, value, entry)
    
    def delete(self, key: K) -> bool:
        """Delete key from cache"""
        with self._lock:
            if key not in self._cache:
                return False
            
            entry = self._cache.pop(key)
            
            if self.metrics:
                self.metrics.deletes += 1
                self.metrics.total_size -= entry.size
            
            self._fire_hook_delete(key, entry)
            return True
    
    def clear(self) -> None:
        """Clear all entries from cache"""
        with self._lock:
            self._cache.clear()
            if self.metrics:
                self.metrics.total_size = 0
    
    def get_many(self, keys: List[K]) -> Dict[K, V]:
        """Get multiple values efficiently"""
        result = {}
        for key in keys:
            value = self.get(key)
            if value is not None:
                result[key] = value
        return result
    
    def set_many(self, items: Dict[K, V], ttl: Optional[float] = None) -> None:
        """Set multiple values efficiently"""
        for key, value in items.items():
            self.set(key, value, ttl)
    
    def exists(self, key: K) -> bool:
        """Check if key exists and is not expired"""
        with self._lock:
            if key not in self._cache:
                return False
            
            entry = self._cache[key]
            if entry.is_expired:
                self._cache.pop(key)
                self._fire_hook_expire(key, entry)
                if self.metrics:
                    self.metrics.expirations += 1
                return False
            
            return True
    
    def keys(self) -> List[K]:
        """Get all valid (non-expired) keys"""
        with self._lock:
            valid_keys = []
            expired_keys = []
            
            for key, entry in self._cache.items():
                if entry.is_expired:
                    expired_keys.append(key)
                else:
                    valid_keys.append(key)
            
            # Clean up expired keys
            for key in expired_keys:
                entry = self._cache.pop(key)
                self._fire_hook_expire(key, entry)
                if self.metrics:
                    self.metrics.expirations += 1
            
            return valid_keys
    
    def values(self) -> List[V]:
        """Get all valid (non-expired) values"""
        with self._lock:
            valid_values = []
            expired_keys = []
            
            for key, entry in self._cache.items():
                if entry.is_expired:
                    expired_keys.append(key)
                else:
                    valid_values.append(entry.value)
            
            # Clean up expired keys
            for key in expired_keys:
                entry = self._cache.pop(key)
                self._fire_hook_expire(key, entry)
                if self.metrics:
                    self.metrics.expirations += 1
            
            return valid_values
    
    def items(self) -> List[Tuple[K, V]]:
        """Get all valid (non-expired) key-value pairs"""
        with self._lock:
            valid_items = []
            expired_keys = []
            
            for key, entry in self._cache.items():
                if entry.is_expired:
                    expired_keys.append(key)
                else:
                    valid_items.append((key, entry.value))
            
            # Clean up expired keys
            for key in expired_keys:
                entry = self._cache.pop(key)
                self._fire_hook_expire(key, entry)
                if self.metrics:
                    self.metrics.expirations += 1
            
            return valid_items
    
    def size(self) -> int:
        """Get current cache size"""
        with self._lock:
            return len(self._cache)
    
    def memory_usage(self) -> int:
        """Get current memory usage in bytes"""
        if self.metrics:
            return self.metrics.total_size
        return 0
    
    def add_hook(self, hook: CacheHook) -> None:
        """Add event hook"""
        self._hooks.append(hook)
    
    def remove_hook(self, hook: CacheHook) -> None:
        """Remove event hook"""
        if hook in self._hooks:
            self._hooks.remove(hook)
    
    def get_metrics(self) -> Optional[Dict[str, Any]]:
        """Get cache metrics"""
        return self.metrics.to_dict() if self.metrics else None
    
    def get_info(self) -> Dict[str, Any]:
        """Get comprehensive cache information"""
        with self._lock:
            info = {
                'size': len(self._cache),
                'max_size': self.max_size,
                'memory_usage': self.memory_usage(),
                'max_memory_mb': self.max_memory_bytes / (1024 * 1024) if self.max_memory_bytes else None,
                'default_ttl': self.default_ttl,
                'cleanup_interval': self.cleanup_interval,
                'hooks_count': len(self._hooks)
            }
            
            if self.metrics:
                info['metrics'] = self.metrics.to_dict()
            
            return info
    
    def reset_metrics(self) -> None:
        """Reset cache metrics"""
        if self.metrics:
            self.metrics = CacheMetrics()
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        with self._lock:
            return {
                'status': 'healthy',
                'size': len(self._cache),
                'memory_usage_mb': self.memory_usage() / (1024 * 1024),
                'cleanup_thread_alive': self._cleanup_thread.is_alive() if self._cleanup_thread else False,
                'metrics': self.get_metrics()
            }
    
    @contextmanager
    def batch_operations(self):
        """Context manager for batch operations"""
        with self._lock:
            yield self
    
    def serialize(self) -> str:
        """Serialize cache to JSON string"""
        with self._lock:
            serializable_cache = {}
            for key, entry in self._cache.items():
                if not entry.is_expired:
                    serializable_cache[str(key)] = {
                        'value': entry.value,
                        'creation_time': entry.creation_time,
                        'ttl': entry.ttl,
                        'access_count': entry.access_count
                    }
            return json.dumps(serializable_cache)
    
    def deserialize(self, data: str) -> None:
        """Deserialize cache from JSON string"""
        with self._lock:
            cache_data = json.loads(data)
            current_time = time.time()
            
            for key, entry_data in cache_data.items():
                # Check if entry would be expired
                if entry_data.get('ttl') is not None:
                    if current_time > entry_data['creation_time'] + entry_data['ttl']:
                        continue  # Skip expired entries
                
                entry = CacheEntry(
                    value=entry_data['value'],
                    access_time=current_time,
                    creation_time=entry_data['creation_time'],
                    ttl=entry_data.get('ttl'),
                    access_count=entry_data.get('access_count', 0),
                    size=self._calculate_size(entry_data['value'])
                )
                
                self._cache[key] = entry
    
    def __len__(self) -> int:
        """Get cache size"""
        return self.size()
    
    def __contains__(self, key: K) -> bool:
        """Check if key exists in cache"""
        return self.exists(key)
    
    def __getitem__(self, key: K) -> V:
        """Get item with dict-like access"""
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value
    
    def __setitem__(self, key: K, value: V) -> None:
        """Set item with dict-like access"""
        self.set(key, value)
    
    def __delitem__(self, key: K) -> None:
        """Delete item with dict-like access"""
        if not self.delete(key):
            raise KeyError(key)
    
    def __repr__(self) -> str:
        return f"LRUCache(size={len(self._cache)}, max_size={self.max_size})"
    
    def __del__(self):
        """Cleanup on destruction"""
        if self._cleanup_thread:
            self._should_stop.set()

# Decorator for caching function results
def lru_cache(maxsize: int = 128, ttl: Optional[float] = None):
    """Decorator for caching function results"""
    def decorator(func):
        cache = LRUCache(max_size=maxsize, default_ttl=ttl)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = (args, tuple(sorted(kwargs.items())))
            
            # Try to get from cache
            result = cache.get(key)
            if result is not None:
                return result
            
            # Calculate and cache result
            result = func(*args, **kwargs)
            cache.set(key, result)
            return result
        
        wrapper.cache = cache
        wrapper.cache_info = lambda: cache.get_info()
        wrapper.cache_clear = lambda: cache.clear()
        
        return wrapper
    return decorator

# Example usage and testing
if __name__ == "__main__":
    # Create cache with hooks
    cache = LRUCache[str, dict](
        max_size=5,
        default_ttl=10.0,
        enable_metrics=True,
        max_memory_mb=1.0
    )
    
    # Add logging hook
    cache.add_hook(LoggingHook())
    
    # Test basic operations
    print("=== Basic Operations ===")
    cache.set("user:1", {"name": "John", "email": "john@example.com"})
    cache.set("user:2", {"name": "Jane", "email": "jane@example.com"})
    
    print(f"User 1: {cache.get('user:1')}")
    print(f"User 2: {cache.get('user:2')}")
    print(f"User 3: {cache.get('user:3', 'Not found')}")
    
    # Test batch operations
    print("\n=== Batch Operations ===")
    with cache.batch_operations():
        cache.set_many({
            "user:3": {"name": "Bob", "email": "bob@example.com"},
            "user:4": {"name": "Alice", "email": "alice@example.com"},
            "user:5": {"name": "Charlie", "email": "charlie@example.com"}
        })
    
    users = cache.get_many(["user:1", "user:3", "user:5"])
    print(f"Batch get result: {users}")
    
    # Test cache info and metrics
    print("\n=== Cache Info ===")
    info = cache.get_info()
    print(f"Cache info: {info}")
    
    print("\n=== Health Check ===")
    health = cache.health_check()
    print(f"Health: {health}")
    
    # Test function decorator
    print("\n=== Function Decorator ===")
    @lru_cache(maxsize=10, ttl=5.0)
    def expensive_function(x: int, y: int) -> int:
        print(f"Computing {x} + {y}")
        return x + y
    
    print(f"Result 1: {expensive_function(1, 2)}")
    print(f"Result 2: {expensive_function(1, 2)}")  # Should hit cache
    print(f"Cache info: {expensive_function.cache_info()}")
    
    # Test serialization
    print("\n=== Serialization ===")
    serialized = cache.serialize()
    print(f"Serialized cache length: {len(serialized)} bytes")
    
    # Test LRU eviction
    print("\n=== LRU Eviction Test ===")
    cache.set("user:6", {"name": "David", "email": "david@example.com"})  # Should evict user:1
    print(f"All keys: {cache.keys()}")
    print(f"Cache size: {len(cache)}")
    
