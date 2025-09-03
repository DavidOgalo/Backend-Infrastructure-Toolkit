import unittest

from config_manager import ConfigManager


class TestConfigManagerUnit(unittest.TestCase):
    def setUp(self):
        self.config = ConfigManager()

    def test_set_and_get(self):
        self.config.set("test.key", "value")
        self.assertEqual(self.config.get("test.key"), "value")

    def test_batch_set_and_get(self):
        items = {"a": 1, "b": 2}
        self.config.batch_set(items)
        result = self.config.batch_get(["a", "b"])
        self.assertEqual(result["a"], 1)
        self.assertEqual(result["b"], 2)

    def test_temporary_override(self):
        self.config.set("test.key", "original")
        with self.config.temporary_override("test.key", "temporary"):
            self.assertEqual(self.config.get("test.key"), "temporary")
        self.assertEqual(self.config.get("test.key"), "original")

    def test_encryption(self):
        config = ConfigManager(enable_encryption=True)
        config.set("secret.key", "sensitive", encrypt=True)
        self.assertEqual(config.get("secret.key"), "sensitive")


if __name__ == "__main__":
    unittest.main()
