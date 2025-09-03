"""
TTL expiry scenario: Demonstrates automatic expiration of cache items.
"""

import time

from LRUcache_system import LRUCache

cache = LRUCache[str, str](max_size=2, default_ttl=2.0)
cache.set("foo", "bar")
print("Set foo -> bar")
print("Value immediately:", cache.get("foo"))
time.sleep(3)
print("Value after TTL expires:", cache.get("foo", "expired"))
