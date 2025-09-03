"""
Basic usage example for the production-ready ConfigManager.
Demonstrates initialization, config access, metrics, and temporary override.
"""

from config_manager import ConfigManager


def on_config_change(event, old_config, new_config):
    print(f"Configuration changed: {event}")


config = ConfigManager(
    config_files=["config.json", "config.yaml"],
    enable_hot_reload=True,
    enable_encryption=True,
)

config.add_change_listener(on_config_change)

print("=== Database Configuration ===")
db_config = config.get_database_config()
print(f"Database config: {db_config}")

print("\n=== API Configuration ===")
api_config = config.get_api_config()
print(f"API config: {api_config}")

print("\n=== Metrics ===")
metrics = config.get_metrics()
print(f"Config metrics: {metrics}")

print("\n=== Health Check ===")
health = config.health_check()
print(f"Health status: {health}")

print("\n=== Temporary Override ===")
with config.temporary_override("database.host", "temp-host"):
    print(f"Temporary host: {config.get('database.host')}")
print(f"Original host: {config.get('database.host')}")
