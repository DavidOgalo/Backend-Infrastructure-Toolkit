"""
Batch operations and LRU eviction scenario.
"""
from LRUcache_system import LRUCache

cache = LRUCache[str, int](max_size=3)

# Batch set
with cache.batch_operations():
    cache.set_many({
        "a": 1,
        "b": 2,
        "c": 3
    })

print("Initial keys:", cache.keys())

# Add another item to trigger eviction
cache.set("d", 4)
print("Keys after LRU eviction:", cache.keys())
