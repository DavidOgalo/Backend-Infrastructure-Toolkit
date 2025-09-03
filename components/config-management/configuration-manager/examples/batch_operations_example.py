"""
Example usage of batch_get and batch_set in ConfigManager.
"""

from config_manager import ConfigManager

if __name__ == "__main__":
    config = ConfigManager()
    # Batch set multiple values
    config.batch_set(
        {
            "feature_flags.new_ui": True,
            "feature_flags.advanced_analytics": False,
            "database.host": "localhost",
            "database.port": 5432,
        }
    )
    # Batch get multiple values
    keys = [
        "feature_flags.new_ui",
        "feature_flags.advanced_analytics",
        "database.host",
        "database.port",
        "missing.key",
    ]
    results = config.batch_get(keys, default="N/A")
    print("Batch get results:")
    for k, v in results.items():
        print(f"  {k}: {v}")
