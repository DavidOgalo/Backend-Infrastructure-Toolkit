import unittest
import time
import logging
from LRUcache_system import LRUCache, LoggingHook, CacheHook

class TestLRUCacheIntegration(unittest.TestCase):
    def setUp(self):
        self.cache = LRUCache(max_size=5, default_ttl=0.2, enable_metrics=True)
        self.hook_events = []
        class TestHook(CacheHook):
            def on_hit(self, key, value, entry):
                self.hook_events.append(("hit", key))
            def on_miss(self, key):
                self.hook_events.append(("miss", key))
            def on_set(self, key, value, entry):
                self.hook_events.append(("set", key))
            def on_expire(self, key, entry):
                self.hook_events.append(("expire", key))
            def on_evict(self, key, entry):
                self.hook_events.append(("evict", key))
        self.test_hook = TestHook()
        self.test_hook.hook_events = self.hook_events
        self.cache.add_hook(self.test_hook)

    def test_event_hooks(self):
        self.cache.set("a", 1)
        self.cache.get("a")
        self.cache.get("b")  # miss
        self.cache.set("b", 2)
        self.cache.set("c", 3)
        self.cache.set("d", 4)
        self.cache.set("e", 5)
        self.cache.set("f", 6)  # Should evict one
        time.sleep(0.3)
        self.cache.get("a")  # Should be expired
        events = [e[0] for e in self.hook_events]
        self.assertIn("hit", events)
        self.assertIn("miss", events)
        self.assertIn("set", events)
        self.assertIn("evict", events)
        self.assertIn("expire", events)

    def test_metrics_and_health(self):
        self.cache.set("x", 100)
        self.cache.get("x")
        metrics = self.cache.get_metrics()
        health = self.cache.health_check()
        self.assertIsInstance(metrics, dict)
        self.assertEqual(health["status"], "healthy")
        self.assertIn("metrics", health)

    def test_serialization(self):
        self.cache.set("foo", "bar")
        data = self.cache.serialize()
        new_cache = LRUCache(max_size=5)
        new_cache.deserialize(data)
        self.assertEqual(new_cache.get("foo"), "bar")

if __name__ == "__main__":
    unittest.main()
