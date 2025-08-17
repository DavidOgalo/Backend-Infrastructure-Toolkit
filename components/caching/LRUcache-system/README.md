# High-Performance LRU Cache System

A production-ready, thread-safe LRU (Least Recently Used) cache implementation with TTL support, comprehensive metrics, and advanced monitoring capabilities.

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Configuration Options](#configuration-options)
- [Metrics & Monitoring](#metrics--monitoring)
- [Event Hooks](#event-hooks)
- [Batch Operations](#batch-operations)
- [TTL and Expiration](#ttl-and-expiration)
- [Function Decorator](#function-decorator)
- [Serialization](#serialization)
- [Testing](#testing)
- [Production Deployment](#production-deployment)
- [Contributing](#contributing)
- [License](#license)

## Overview

This caching system provides a high-performance, memory-efficient LRU cache with enterprise-grade features for modern backend applications requiring fast data access and intelligent memory management.

For a deep dive into architecture, design decisions, and advanced usage, see the [System Design Document](./system_design.md).

## Key Features

### Core Functionality

- **LRU Eviction Policy**: O(1) get/set operations with efficient memory management
- **TTL Support**: Time-To-Live expiration with automatic cleanup
- **Thread-Safe Operations**: Full concurrency support with read/write locks
- **Memory Management**: Configurable size and memory limits

### Advanced Features

- **Comprehensive Metrics**: Hit rates, miss rates, eviction statistics
- **Event Hooks**: Extensible event system for monitoring and debugging
- **Batch Operations**: Efficient bulk get/set operations
- **Serialization**: JSON-based persistence and restoration
- **Dictionary Interface**: Native Python dict-like access patterns

## Architecture

Major components and layers in the codebase:

```python
LRUCache
├── OrderedDict (Core Storage)
├── TTL Management System
├── Metrics Collection
├── Event Hook System
├── Background Cleanup
└── Thread Safety Layer
```

## Installation

Install the system to your project (assuming you have the repo cloned):

```bash
cd components/lru-cache
pip install .
```

**Dependencies:**

- Python 3.7+
- Standard library (`json`, `threading`, `time`, `logging`)

## Getting Started

### Basic Usage

```python
from LRUcache_system import LRUCache

# Initialize with default settings
cache = LRUCache(max_size=100)

# Basic operations
cache.set("key1", "value1")
value = cache.get("key1")  # Returns "value1"
exists = cache.exists("key1")  # Returns True
cache["key2"] = "value2"  # Dictionary-style set
value = cache["key2"]  # Dictionary-style get
del cache["key2"]  # Dictionary-style delete
```

### Advanced Configuration

```python
from LRUcache_system import LRUCache, LoggingHook

# Initialize with custom settings
cache = LRUCache(
    max_size=1000,
    default_ttl=300,
    enable_metrics=True,
    cleanup_interval=60,
    max_memory_mb=50
)

# Add logging hook
cache.add_hook(LoggingHook(log_level="INFO"))
```

## Usage

All usage scenarios, including quick-start and advanced examples, are provided as standalone scripts in the `examples/` directory. Key example:

- `examples/basic_usage.py`: Initialize the cache system, perform basic operations, view metrics, and use hooks.

See the `examples/` directory and `examples/README.md` for more advanced and scenario-based usage scripts.

**How to run an example:**

> **Important:** Always run the example scripts with the parent directory in your `PYTHONPATH` to ensure imports work correctly.

On Windows PowerShell:

```pwsh
$env:PYTHONPATH="."; python .\examples\basic_usage.py
```

On Linux/macOS/bash:

```bash
PYTHONPATH=. python ./examples/basic_usage.py
```

Replace `basic_usage.py` with any other example script as needed.

### Use Cases

1. **API Response Caching**

   ```python
   from LRUcache_system import LRUCache
   cache = LRUCache[str, dict](max_size=1000, default_ttl=300)
   cache.set("user:123", {"name": "John", "email": "john@example.com"})
   user_data = cache.get("user:123")
   ```

2. **Database Query Caching**

   ```python
   from LRUcache_system import lru_cache

   @lru_cache(maxsize=500, ttl=600)
   def get_user_by_id(user_id: int):
       return database.query("SELECT * FROM users WHERE id = ?", user_id)

   user = get_user_by_id(123)  # Hits database
   user = get_user_by_id(123)  # Hits cache
   ```

3. **Session Storage**

   ```python
   from LRUcache_system import LRUCache
   session_cache = LRUCache[str, dict](max_size=10000, default_ttl=1800, max_memory_mb=100)
   session_cache.set(session_id, {"user_id": user_id, "permissions": permissions, "last_activity": datetime.now()})
   ```

4. **Computed Results Caching**

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

## Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_size` | `int` | `1000` | Maximum number of cached items |
| `default_ttl` | `Optional[float]` | `None` | Default time-to-live in seconds |
| `enable_metrics` | `bool` | `True` | Enable performance metrics |
| `cleanup_interval` | `float` | `60.0` | Background cleanup interval (seconds) |
| `max_memory_mb` | `Optional[float]` | `None` | Maximum memory usage (MB) |

## Metrics & Monitoring

The system tracks performance metrics such as hit rates, miss rates, and eviction statistics.

### Performance Metrics

```python
metrics = cache.get_metrics()
print(metrics)
# Example output: {'hits': 850, 'misses': 150, 'hit_rate': 0.85, 'evictions': 10}
```

### Health Monitoring

```python
health = cache.health_check()
print(health)
# Example output: {'status': 'healthy', 'size': 175, 'max_size': 1000, 'memory_usage_mb': 2.5}
```

### Cache Information

```python
info = cache.get_info()
print(info)
# Example output: {'size': 175, 'max_size': 1000, 'ttl_enabled': True, 'memory_usage_mb': 2.5}
```

## Event Hooks

### Built-in Hooks

```python
from LRUcache_system import LoggingHook
cache.add_hook(LoggingHook(log_level="INFO"))
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

Efficiently handle multiple cache operations:

```python
# Bulk set
cache.set_many({"user:1": {"name": "John"}, "user:2": {"name": "Jane"}}, ttl=300)

# Bulk get
users = cache.get_many(["user:1", "user:2"])

# Batch transaction
with cache.batch_operations():
    cache.set("key1", "value1")
    cache.set("key2", "value2")
```

## TTL and Expiration

### Time-To-Live Configuration

```python
# Set with specific TTL
cache.set("session:123", session_data, ttl=1800)

# Set with default TTL
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

Automate caching for functions:

```python
from LRUcache_system import lru_cache

@lru_cache(maxsize=128, ttl=300)
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result1 = fibonacci(50)  # Computes result
result2 = fibonacci(50)  # Hits cache
print(fibonacci.cache_info())  # View cache stats
fibonacci.cache_clear()  # Clear cache
```

## Serialization

Persist and restore cache state:

```python
# Serialize cache
serialized_data = cache.serialize()
with open('cache_backup.json', 'w') as f:
    f.write(serialized_data)

# Restore cache
new_cache = LRUCache[str, dict](max_size=1000)
with open('cache_backup.json', 'r') as f:
    new_cache.deserialize(f.read())
```

## Testing

Tests are organized in the `tests/` folder:

- **Unit tests** (`unit_test.py`): Validate core operations (set/get, eviction, TTL expiry, batch operations, dict interface).
- **Integration tests** (`integration_test.py`): Cover advanced scenarios (event hooks, metrics, health checks, serialization, decorator usage).
- **Performance tests** (`performance_test.py`): Benchmark cache set/get throughput and ensure performance targets.

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

## Production Deployment

### Best Practices

1. **Configuration**

   Configure cache size and TTL based on workload:

   ```python
   cache = LRUCache(max_size=10000, default_ttl=3600, max_memory_mb=500)
   ```

2. **Docker Integration**

   ```dockerfile
   # Install dependencies
   COPY requirements.txt .
   RUN pip install -r requirements.txt

   # Copy application code
   COPY . /app
   WORKDIR /app
   ```

3. **Kubernetes Deployment**

   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: cache-service
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: cache-service
     template:
       metadata:
         labels:
           app: cache-service
       spec:
         containers:
         - name: cache-service
           image: cache-service:latest
           env:
           - name: CACHE_MAX_SIZE
             value: "10000"
           - name: CACHE_TTL
             value: "3600"
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add comprehensive tests
4. Update documentation
5. Submit a pull request

## License

MIT License - See the [LICENSE](../../../LICENSE) file for details.
