import unittest
import os
from config_manager import ConfigManager

class TestConfigManagerIntegration(unittest.TestCase):
    def setUp(self):
        # Set environment variable for override test
        os.environ['DATABASE_HOST'] = 'integration-host'
        self.config = ConfigManager()

    def tearDown(self):
        # Clean up environment variable
        if 'DATABASE_HOST' in os.environ:
            del os.environ['DATABASE_HOST']

    def test_environment_override(self):
        self.assertEqual(self.config.get('database.host'), 'integration-host')

    def test_change_listener(self):
        changes = []
        def listener(event, old, new):
            changes.append((event, old, new))
        self.config.add_change_listener(listener)
        self.config.set('test.key', 'new_value')
        # Simulate change notification
        self.config._notify_changes({'test.key': 'old_value'}, {'test.key': 'new_value'})
        self.assertTrue(any('config_changed' in c for c in changes))

if __name__ == '__main__':
    unittest.main()
