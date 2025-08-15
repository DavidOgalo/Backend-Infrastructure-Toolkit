# High-Performance LRU Cache System

A production-ready, thread-safe LRU cache implementation with TTL support, comprehensive metrics, and advanced monitoring capabilities.

## System Design & Architecture

For a deep dive into architecture, design decisions, and advanced usage, see the [System Design Document](./system_design.md).

## Overview

This caching system provides a high-performance, memory-efficient LRU (Least Recently Used) cache with enterprise-grade features for modern backend applications requiring fast data access and intelligent memory management.

## Key Features

### Core Functionality

- **LRU Eviction Policy**: O(1) get/set operations with efficient memory management
- **TTL Support**: Time-To-Live expiration with automatic cleanup
- **Thread-Safe Operations**: Full concurrency support with read/write locks
- **Memory Management**: Configurable size and memory limits

### Advanced Features

- **Comprehensive Metrics**: Hit rates, miss rates, eviction statistics
- **Event Hooks**: Extensible event system for monitoring and debugging (fully implemented via `CacheHook` and `add_hook()`)
- **Batch Operations**: Efficient bulk get/set operations (fully implemented via `set_many()`, `get_many()`, and `batch_operations()` context manager)
- **Serialization**: JSON-based persistence and restoration
- **Dictionary Interface**: Native Python dict-like access patterns

## Architecture

```python
LRUCache
├── OrderedDict (Core Storage)
├── TTL Management System
├── Metrics Collection
├── Event Hook System
├── Background Cleanup
└── Thread Safety Layer
```

## Use Cases

### 1. API Response Caching

```python
from LRUcache_system import LRUCache
cache = LRUCache[str, dict](max_size=1000, default_ttl=300)
cache.set("user:123", {"name": "John", "email": "john@example.com"})
user_data = cache.get("user:123")
```

### 2. Database Query Caching

```python
from LRUcache_system import lru_cache

@lru_cache(maxsize=500, ttl=600)
def get_user_by_id(user_id: int):
    return database.query("SELECT * FROM users WHERE id = ?", user_id)

user = get_user_by_id(123)  # First call: hits database
user = get_user_by_id(123)  # Second call: hits cache
```

### 3. Session Storage

```python
from LRUcache_system import LRUCache
session_cache = LRUCache[str, dict](max_size=10000, default_ttl=1800, max_memory_mb=100)
session_cache.set(session_id, {"user_id": user_id, "permissions": permissions, "last_activity": datetime.now()})
```

### 4. Computed Results Caching

```python
from LRUcache_system import LRUCache
computation_cache = LRUCache[tuple, float](max_size=1000)

def expensive_calculation(x, y, z):
    cache_key = (x, y, z)
    result = computation_cache.get(cache_key)
    if result is None:
        result = complex_math_operation(x, y, z)
        computation_cache.set(cache_key, result)
    return result
```

## Getting Started

### Basic Usage

```python
from LRUcache_system import LRUCache
cache = LRUCache(max_size=100)
cache.set("key1", "value1")
value = cache.get("key1")
exists = cache.exists("key1")
cache["key2"] = "value2"
value = cache["key2"]
del cache["key2"]
```

### Advanced Configuration

```python
cache = LRUCache(
    max_size=1000,
    default_ttl=300,
    enable_metrics=True,
    cleanup_interval=60,
    max_memory_mb=50
)
from LRUcache_system import LoggingHook
cache.add_hook(LoggingHook())
```

## Configuration Options

| Parameter         | Type             | Default   | Description                       |
|-------------------|------------------|-----------|-----------------------------------|
| `max_size`        | `int`            | `1000`    | Maximum number of cached items     |
| `default_ttl`     | `Optional[float]`| `None`    | Default time-to-live in seconds    |
| `enable_metrics`  | `bool`           | `True`    | Enable performance metrics         |
| `cleanup_interval`| `float`          | `60.0`    | Background cleanup interval (secs) |
| `max_memory_mb`   | `Optional[float]`| `None`    | Maximum memory usage (MB)          |

## Metrics & Monitoring

### Performance Metrics

```python
from LRUcache_system import LRUCache
cache = LRUCache(max_size=100)
metrics = cache.get_metrics()
print(metrics)
# Example output: {'hits': 850, 'misses': 150, ...}
```

### Health Monitoring

```python
health = cache.health_check()
print(health)
# Example output: {'status': 'healthy', 'size': 175, ...}
```

### Cache Information

```python
info = cache.get_info()
print(info)
# Example output: {'size': 175, 'max_size': 1000, ...}
```

## Event Hooks

### Built-in Hooks

```python
from LRUcache_system import LoggingHook
cache.add_hook(LoggingHook(log_level=logging.INFO))
```

### Custom Hooks

```python
from LRUcache_system import CacheHook
class MetricsHook(CacheHook):
    def __init__(self, metrics_client):
        self.metrics = metrics_client
    def on_hit(self, key, value, entry):
        self.metrics.increment('cache.hit')
    def on_miss(self, key):
        self.metrics.increment('cache.miss')
    def on_evict(self, key, entry):
        self.metrics.increment('cache.evict')
        self.metrics.histogram('cache.entry_age', entry.age)
cache.add_hook(MetricsHook(metrics_client))
```

## Batch Operations

### Efficient Bulk Operations

```python
cache.set_many({"user:1": {"name": "John"}, "user:2": {"name": "Jane"}}, ttl=300)
users = cache.get_many(["user:1", "user:2"])
with cache.batch_operations():
    cache.set("key1", "value1")
    cache.set("key2", "value2")
```

## TTL and Expiration

### Time-To-Live Configuration

```python
cache.set("session:123", session_data, ttl=1800)
cache = LRUCache(default_ttl=300)
cache.set("key", "value")
```

### Manual Cleanup

```python
cache._cleanup_expired()
entry = cache._cache.get("key")
if entry and entry.is_expired:
    print("Item has expired")
```

## Function Decorator

### Automatic Function Caching

```python
from LRUcache_system import lru_cache
@lru_cache(maxsize=128, ttl=300)
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
result1 = fibonacci(50)
result2 = fibonacci(50)
print(fibonacci.cache_info())
fibonacci.cache_clear()
```

## Serialization

### Persistence Support

```python
serialized_data = cache.serialize()
with open('cache_backup.json', 'w') as f:
    f.write(serialized_data)
new_cache = LRUCache[str, dict](max_size=1000)
with open('cache_backup.json', 'r') as f:
    new_cache.deserialize(f.read())
```

## Testing

All tests are implemented in the `tests/` folder for modularity and clarity:

- **Unit tests** (`unit_test.py`): Validate core cache operations: set/get, eviction, TTL expiry, batch operations, and dict interface.
- **Integration tests** (`integration_test.py`): Cover advanced scenarios: event hooks, metrics, health checks, serialization, and decorator usage.
- **Performance tests** (`performance_test.py`): Benchmark cache set/get throughput and ensure performance targets are met.

### Running Tests

To run all tests:

```bash
python -m unittest discover tests
```

Or run a specific test file:

```bash
python -m unittest tests/unit_test.py
python -m unittest tests/integration_test.py
python -m unittest tests/performance_test.py
```

Each test file covers distinct use-cases and scenarios. See the test source for details.

## Production Deployment

## Installation

```bash
pip install .
```

```python
from LRUcache_system import LRUCache, CacheHook

# Basic usage
cache = LRUCache(max_size=100, ttl=60)
cache.set('key', 'value')
value = cache.get('key')

# Batch operations
cache.set_many({'a': 1, 'b': 2})
values = cache.get_many(['a', 'b'])
with cache.batch_operations():
    cache.set('c', 3)
    cache.set('d', 4)

# Hooks
class MyHook(CacheHook):
    def on_set(self, key, value):
        print(f"Set: {key} -> {value}")
cache.add_hook(MyHook())

# Health check
health = cache.health_check()
print(health)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add comprehensive tests
4. Update documentation
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

---

## Usage

### Usage & Example Scenarios

All usage, including quick-start and advanced scenarios, is provided as standalone scripts in the `examples/` directory. Here is a key example:

- `examples/basic_usage.py`: Initialize the cache system, access configs, view metrics, and use temporary overrides.

See the `examples/` directory and `examples/README.md` for more advanced and scenario-based usage scripts.

**How to run an example:**

> **Important:** Always run the example scripts with the parent directory in your `PYTHONPATH` so that imports work correctly.

On Windows PowerShell:

```pwsh
$env:PYTHONPATH="."; python .\examples\basic_usage.py
```

On Linux/macOS/bash:

```pwsh
PYTHONPATH=. python ./examples/basic_usage.py
```

Replace `basic_usage.py` with any other example script as needed.
