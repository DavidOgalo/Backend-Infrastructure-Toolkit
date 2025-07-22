"""
Encryption demo: Shows how to store and retrieve encrypted configuration values.
"""
from config_manager import ConfigManager

config = ConfigManager(enable_encryption=True)

# Set an encrypted value
config.set('api.secret_key', 'super-secret-value', encrypt=True)

# Retrieve (automatically decrypted)
print("Decrypted API secret key:", config.get('api.secret_key'))

# Show raw encrypted value in config dict
print("Raw stored value:", config._config['api']['secret_key'])
