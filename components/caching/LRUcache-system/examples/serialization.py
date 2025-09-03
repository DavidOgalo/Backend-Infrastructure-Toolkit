"""
Serialization and deserialization scenario: Save and restore cache state.
"""

from LRUcache_system import LRUCache

cache = LRUCache[str, int](max_size=2)
cache.set("x", 100)
cache.set("y", 200)

serialized = cache.serialize()
print("Serialized cache:", serialized)

# Create a new cache and restore state
new_cache = LRUCache[str, int](max_size=2)
new_cache.deserialize(serialized)
print("Restored keys:", new_cache.keys())
print("Restored values:", new_cache.values())
