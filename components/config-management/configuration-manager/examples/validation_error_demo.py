"""
Validation error demo: Shows how schema validation errors are handled.
"""
from config_manager import ConfigManager, ConfigError

# Simulate a config missing required fields
bad_config = {
    "database": {
        "host": "localhost"
        # Missing 'port', 'database', 'user'
    }
}

with open("bad_config.json", "w") as f:
    import json
    json.dump(bad_config, f)

try:
    config = ConfigManager(config_files=["bad_config.json"])
except ConfigError as e:
    print("Validation error caught:", e)
finally:
    import os
    os.remove("bad_config.json")
