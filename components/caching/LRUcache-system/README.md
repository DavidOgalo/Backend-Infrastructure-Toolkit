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

### Usage & Example Scenarios

All usage, including quick-start and advanced scenarios, is provided as standalone scripts in the `examples/` directory. Here is a key example:

- `examples/basic_usage.py`: Basic set/get, batch operations, metrics, and health check.

See the `examples/` directory and `examples/README.md` for more advanced and scenario-based usage scripts.

**How to run an example:**

> **Important:** Always run the example scripts with the parent directory in your `PYTHONPATH` so that imports work correctly.

On Windows PowerShell:

```pwsh
$env:PYTHONPATH="."; python .\examples\basic_usage.py
```

On Linux/macOS/bash:

```bash
PYTHONPATH=. python ./examples/basic_usage.py
```

Replace `basic_usage.py` with any other example script as needed.

These scripts demonstrate real-world backend scenarios, including LRU eviction, TTL expiry, batch operations, metrics, hooks, and serialization. You can use or extend them for your own use-cases.

#### Minimal Quick-Start (copy-paste into your own script)

```python
from LRUcache_system import LRUCache

cache = LRUCache(max_size=5, default_ttl=10.0)
cache.set("foo", "bar")
print(cache.get("foo"))
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
