import time
import unittest

from LRUcache_system import LRUCache


class TestLRUCachePerformance(unittest.TestCase):
    def test_set_get_performance(self):
        cache = LRUCache[int, str](max_size=10000)
        # Benchmark set operations
        start_time = time.time()
        for i in range(10000):
            cache.set(i, f"value_{i}")
        set_time = time.time() - start_time
        # Benchmark get operations
        start_time = time.time()
        for i in range(10000):
            cache.get(i)
        get_time = time.time() - start_time
        print(f"Set operations: {set_time:.3f}s ({10000 / set_time:.0f} ops/sec)")
        print(f"Get operations: {get_time:.3f}s ({10000 / get_time:.0f} ops/sec)")
        # Assert that performance is within reasonable bounds (example threshold)
        self.assertLess(set_time, 2.0)
        self.assertLess(get_time, 2.0)


if __name__ == "__main__":
    unittest.main()
