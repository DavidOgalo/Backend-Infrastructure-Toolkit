"""
Function result caching using the lru_cache decorator.
"""

from LRUcache_system import lru_cache


@lru_cache(maxsize=10, ttl=2.0)
def expensive_function(x, y):
    print(f"Computing {x} + {y}")
    return x + y


print("Result 1:", expensive_function(1, 2))
print("Result 2:", expensive_function(1, 2))  # Should hit cache
print("Cache info:", expensive_function.cache_info())
