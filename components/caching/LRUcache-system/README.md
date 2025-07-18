# LRU Cache System

A high-performance, production-ready Least Recently Used (LRU) cache system for Python, featuring TTL (Time-To-Live), metrics, event hooks, batch operations, and serialization. Designed for scalable backend services and real-world workloads.

---

## Features

- **LRU eviction policy**: O(1) get/set with automatic removal of least recently used items.
- **TTL support**: Expire items after a configurable time-to-live.
- **Comprehensive metrics**: Track hits, misses, evictions, expirations, and more.
- **Event-driven hooks**: Subscribe to cache events (hit, miss, set, delete, expire, evict) for observability.
- **Memory-efficient**: Configurable size and memory limits.
- **Batch operations**: Efficiently set/get multiple items.
- **Serialization**: Save/load cache state to/from JSON.
- **Thread-safe**: Safe for concurrent access in multi-threaded environments.
- **Decorator**: Simple function result caching with TTL.

---

## Installation

Add the component to your project (assuming you have the repo cloned):

```bash
cd components/caching/LRUcache-system
pip install -r requirements.txt  # if dependencies are needed
```

**Dependencies:**

- Python 3.7+

---

## Usage

### Basic Example

```python
from LRUcache_system import LRUCache, LoggingHook

# Create a cache with a max size of 5 and 10s TTL
cache = LRUCache[str, dict](max_size=5, default_ttl=10.0, enable_metrics=True)

# Add a logging hook for observability
cache.add_hook(LoggingHook())

# Set and get values
cache.set("user:1", {"name": "John"})
user = cache.get("user:1")

# Batch operations
with cache.batch_operations():
    cache.set_many({
        "user:2": {"name": "Jane"},
        "user:3": {"name": "Bob"}
    })
users = cache.get_many(["user:1", "user:2"])

# Metrics and health
print(cache.get_metrics())
print(cache.health_check())
```

### Function Result Caching

```python
from LRUcache_system import lru_cache

@lru_cache(maxsize=10, ttl=5.0)
def expensive_function(x, y):
    return x + y

result = expensive_function(1, 2)
```

---

## API Reference

### LRUCache Initialization

```python
LRUCache(
    max_size: int = 1000,
    default_ttl: Optional[float] = None,
    enable_metrics: bool = True,
    cleanup_interval: float = 60.0,
    max_memory_mb: Optional[float] = None
)
```

### Core Methods

- `get(key, default=None)`: Retrieve a value by key.
- `set(key, value, ttl=None)`: Set a value with optional TTL.
- `delete(key)`: Remove a key from the cache.
- `clear()`: Remove all items from the cache.
- `get_many(keys)`: Get multiple values at once.
- `set_many(items, ttl=None)`: Set multiple values at once.
- `exists(key)`: Check if a key exists and is not expired.
- `keys()`, `values()`, `items()`: Get all valid keys, values, or items.
- `add_hook(hook)`: Add an event hook (e.g., LoggingHook).
- `get_metrics()`: Get cache metrics.
- `get_info()`: Get cache info and configuration.
- `health_check()`: Get health and status info.
- `serialize()`, `deserialize(data)`: Save/load cache state as JSON.

### Decorator

- `lru_cache(maxsize=128, ttl=None)`: Decorator for caching function results.

---

## Best Practices

- **Tune max_size and TTL** for your workload and memory constraints.
- **Use hooks** (e.g., LoggingHook) for observability and debugging.
- **Monitor metrics** to optimize cache hit rate and performance.
- **Use batch operations** for efficiency when working with many items.

---

## Metrics & Observability

The cache tracks:

- Hits, misses, sets, deletes, evictions, expirations
- Total and peak memory usage
- Hit/miss rates

Use `get_metrics()` for monitoring and alerting.

---

## Extending

- Implement custom hooks by subclassing `CacheHook`.
- Integrate with your logging/monitoring stack as needed.

---

## Testing

- Unit and integration tests are recommended for your cache usage.
- Use the batch context manager for test isolation.
