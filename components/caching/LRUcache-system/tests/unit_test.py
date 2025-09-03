import time
import unittest

from LRUcache_system import LRUCache


class TestLRUCacheUnit(unittest.TestCase):
    def setUp(self):
        self.cache = LRUCache(max_size=3)

    def test_basic_operations(self):
        self.cache.set("a", "1")
        self.cache.set("b", "2")
        self.assertEqual(self.cache.get("a"), "1")
        self.assertEqual(len(self.cache), 2)

    def test_lru_eviction(self):
        self.cache.set("a", "1")
        self.cache.set("b", "2")
        self.cache.set("c", "3")
        self.cache.set("d", "4")  # Should evict "a"
        self.assertIsNone(self.cache.get("a"))
        self.assertEqual(self.cache.get("d"), "4")

    def test_ttl_expiration(self):
        cache = LRUCache(max_size=10, default_ttl=0.1)
        cache.set("key", "value")
        time.sleep(0.2)
        self.assertIsNone(cache.get("key"))

    def test_batch_operations(self):
        items = {"x": 1, "y": 2, "z": 3}
        self.cache.set_many(items)
        result = self.cache.get_many(["x", "y", "z"])
        self.assertEqual(result["x"], 1)
        self.assertEqual(result["y"], 2)
        self.assertEqual(result["z"], 3)

    def test_dict_interface(self):
        self.cache["foo"] = "bar"
        self.assertEqual(self.cache["foo"], "bar")
        del self.cache["foo"]
        self.assertFalse("foo" in self.cache)


if __name__ == "__main__":
    unittest.main()
