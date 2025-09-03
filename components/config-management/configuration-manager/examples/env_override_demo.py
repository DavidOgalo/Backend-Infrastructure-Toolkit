"""
Environment variable override demo: Shows how environment variables take precedence over file config.
"""

import os

from config_manager import ConfigManager

# Set an environment variable before loading config
os.environ["DATABASE_HOST"] = "env-db-host.example.com"

config = ConfigManager(config_files=["config.json"])
print("DATABASE_HOST from environment:", config.get("database.host"))
