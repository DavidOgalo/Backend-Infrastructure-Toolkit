"""
Basic usage example for the LRUCache system.
Demonstrates basic set/get, batch operations, metrics, and health check.
"""
from LRUcache_system import LRUCache, LoggingHook

# Create a cache with a max size of 5 and 10s TTL
cache = LRUCache[str, dict](max_size=5, default_ttl=10.0, enable_metrics=True)

# Add a logging hook for observability
cache.add_hook(LoggingHook())

# Set and get values
cache.set("user:1", {"name": "John"})
user = cache.get("user:1")
print(f"User 1: {user}")

# Batch operations
with cache.batch_operations():
    cache.set_many({
        "user:2": {"name": "Jane"},
        "user:3": {"name": "Bob"}
    })
users = cache.get_many(["user:1", "user:2"])
print(f"Batch get result: {users}")

# Metrics and health
print("Metrics:", cache.get_metrics())
print("Health:", cache.health_check())
