"""
Example: Using ConfigManager with a remote HTTP config loader.
"""
from config_manager import ConfigManager, HTTPConfigLoader

# Replace with your actual config service URL
REMOTE_CONFIG_URL = "https://config-service.example.com/app-config"

remote_loader = HTTPConfigLoader(REMOTE_CONFIG_URL, retries=2, timeout=3)

config = ConfigManager(
    config_files=["config.json"],
    remote_loaders=[remote_loader]
)

# Access config values (merged from local and remote)
db_config = config.get_database_config()
print("Database config:", db_config)

api_config = config.get_api_config()
print("API config:", api_config)

# Show full config for inspection
print("Full merged config:", config._config)
