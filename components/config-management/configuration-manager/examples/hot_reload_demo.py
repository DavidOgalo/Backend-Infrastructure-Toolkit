"""
Hot reload demo: Shows how the ConfigManager automatically reloads configuration when a file changes.
"""
import time
from config_manager import ConfigManager

def on_config_change(event, old_config, new_config):
    print(f"[Hot Reload] {event}:\nOld: {old_config}\nNew: {new_config}")

config = ConfigManager(
    config_files=["config.json"],
    enable_hot_reload=True
)
config.add_change_listener(on_config_change)

print("Watching for config changes. Modify config.json to trigger reload...")
try:
    while True:
        time.sleep(2)
        print("Current DB host:", config.get('database.host', 'not set'))
except KeyboardInterrupt:
    print("Stopped.")
