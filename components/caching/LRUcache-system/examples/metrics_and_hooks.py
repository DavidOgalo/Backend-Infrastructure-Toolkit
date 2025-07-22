"""
Metrics and event hooks scenario: Track cache metrics and observe events.
"""
from LRUcache_system import LRUCache, LoggingHook

cache = LRUCache[str, int](max_size=2, enable_metrics=True)
cache.add_hook(LoggingHook())

cache.set("a", 1)
cache.set("b", 2)
cache.get("a")
cache.get("c", 0)
cache.delete("b")

print("Metrics:", cache.get_metrics())
