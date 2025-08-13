# Configuration Management System

A production-ready, thread-safe configuration manager with advanced features for modern backend services.

## Overview

This configuration management system provides a robust solution for handling application settings with support for multiple sources, hot reloading, validation, and security features essential for production environments.

## Key Features

### Core Functionality

- **Multi-Source Configuration**: JSON, YAML, environment variables, and now remote sources via pluggable loaders (see RemoteConfigLoader)
- **Hot Reloading**: Automatic configuration updates with file watching
- **Thread-Safe Operations**: Full thread safety with read/write locks
- **Nested Key Access**: Dot notation for hierarchical configuration (`database.host`)

### Advanced Features

- **Schema Validation**: Type checking and validation rules
- **Encryption Support**: Secure handling of sensitive configuration values (custom key support)
- **Change Listeners**: Event-driven configuration updates
- **Comprehensive Metrics**: Access patterns, cache hit rates, reload statistics
- **Health Monitoring**: Built-in health checks and status reporting
- **Extensibility**: Plugin/extension interfaces for new sources and hooks. Now supports remote config loading via pluggable loader interfaces (e.g., HTTP, S3, etcd, Consul).

### Production Ready

- **Error Handling**: Graceful failure with detailed error context
- **Logging Integration**: Structured logging with configurable levels
- **Temporary Overrides**: Context manager for testing and debugging
- **Performance Optimized**: Caching and efficient data structures

## Architecture

Major modules and layers present and functional in the codebase

```python
ConfigManager
├── File Sources (JSON/YAML)
├── Environment Variables
├── Validation Layer
├── Encryption Engine
├── Cache Layer
├── Change Detection
├── Metrics Collection
├── Remote Sources (via RemoteConfigLoader, HTTPConfigLoader, etc.)
└── Plugin/Extension Interfaces
```

## Use Cases

### 1. **Database Configuration**

```python
config = ConfigManager(["config.json"])
db_config = config.get_database_config()
# Returns: {'host': 'localhost', 'port': 5432, 'database': 'myapp', ...}
```

### 2. **API Settings**

```python
api_config = config.get_api_config()
# Returns: {'key': 'xxx', 'rate_limit': 1000, 'timeout': 30.0, ...}
```

### 3. **Environment Overrides**

```bash
export DATABASE_HOST=prod-db.example.com
export API_RATE_LIMIT=5000
```

### 4. **Hot Reloading**

```python
def on_config_change(event, old_config, new_config):
    logger.info("Configuration updated")

config.add_change_listener(on_config_change)
```

### 5. **Encryption for Secrets**

```python
config.set('database.password', 'secret123', encrypt=True)
password = config.get('database.password')  # Automatically decrypted
```

## Getting Started

### Basic Usage

```python
from config_manager import ConfigManager

# Initialize with default settings
config = ConfigManager()

# Get configuration values
debug_mode = config.get('debug', False)
database_url = config.get('database.url', 'sqlite:///app.db')

# Set configuration values
config.set('feature_flags.new_ui', True)
```

### Advanced Configuration

```python
# Initialize with custom settings
config = ConfigManager(
    config_files=["config.json", "config.yaml"],
    enable_hot_reload=True,
    reload_interval=30,
    enable_encryption=True
)

# Add change listener
config.add_change_listener(lambda event, old, new: print("Config changed!"))

# Use temporary overrides for testing
with config.temporary_override('database.host', 'test-db'):
    # Configuration temporarily changed
    test_connection()
# Configuration restored

### Remote Configuration Loader Example

```python
from config_manager import ConfigManager, HTTPConfigLoader

# Use a remote HTTP config source
http_loader = HTTPConfigLoader(url="https://example.com/config.json", max_retries=3)
config = ConfigManager(remote_loaders=[http_loader])

# Access remote config values
api_key = config.get('api.key')
```

## Configuration Format

### JSON Configuration

```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "database": "myapp",
    "user": "postgres",
    "password": "secret",
    "pool_size": 10,
    "timeout": 30
  },
  "api": {
    "key": "your-api-key",
    "rate_limit": 1000,
    "timeout": 30.0,
    "base_url": "https://api.example.com"
  },
  "logging": {
    "level": "INFO",
    "format": "json"
  },
  "feature_flags": {
    "new_ui": false,
    "advanced_analytics": true
  }
}
```

### YAML Configuration

```yaml
database:
  host: localhost
  port: 5432
  database: myapp
  user: postgres
  password: secret
  pool_size: 10
  timeout: 30

api:
  key: your-api-key
  rate_limit: 1000
  timeout: 30.0
  base_url: https://api.example.com

logging:
  level: INFO
  format: json

feature_flags:
  new_ui: false
  advanced_analytics: true
```

## 🔧 Environment Variables

The system automatically maps environment variables to configuration keys:

| Environment Variable | Configuration Key | Description |
|---------------------|-------------------|-------------|
| `DATABASE_HOST` | `database.host` | Database hostname |
| `DATABASE_PORT` | `database.port` | Database port |
| `DATABASE_NAME` | `database.database` | Database name |
| `DATABASE_USER` | `database.user` | Database username |
| `DATABASE_PASSWORD` | `database.password` | Database password |
| `API_KEY` | `api.key` | API authentication key |
| `API_RATE_LIMIT` | `api.rate_limit` | API rate limit |
| `DEBUG` | `debug` | Debug mode flag |
| `LOG_LEVEL` | `logging.level` | Logging level |

## Security Features

### Encryption

```python
# Enable encryption (auto-generates a key if not provided)
config = ConfigManager(enable_encryption=True)

# Use a custom encryption key (recommended for production)
from cryptography.fernet import Fernet
key = Fernet.generate_key()
config = ConfigManager(enable_encryption=True, encryption_key=key)

# Encrypt sensitive values
config.set('database.password', 'secret123', encrypt=True)
config.set('api.secret_key', 'top-secret', encrypt=True)

# Values are automatically decrypted when accessed
password = config.get('database.password')  # Returns decrypted value
```

> **Note:** Key management and rotation are critical for production. Store your encryption key securely (e.g., environment variable, secrets manager).

### Validation

```python
# Custom validator
def validate_port(value):
    port = int(value)
    if not 1 <= port <= 65535:
        raise ValueError(f"Invalid port: {port}")
    return port

# Add validator
config.validators['port'] = validate_port
```

## Monitoring & Metrics

### Health Check

```python
health = config.health_check()
print(health)
# {
#   'status': 'healthy',
#   'config_files_loaded': 2,
#   'hot_reload_enabled': True,
#   'encryption_enabled': True,
#   'metrics': {...}
# }
```

### Metrics

```python
metrics = config.get_metrics()
print(metrics)
# {
#   'access_count': 150,
#   'cache_hits': 140,
#   'cache_misses': 10,
#   'reload_count': 3,
#   'validation_errors': 0,
#   'cache_hit_rate': 0.93
# }
```

## Hot Reloading

The configuration manager automatically detects file changes and reloads configuration:

1. **File Monitoring**: Watches configuration files for changes
2. **Hash Comparison**: Uses MD5 hashes to detect actual changes
3. **Atomic Updates**: Ensures consistent state during reloads
4. **Change Notifications**: Triggers registered listeners
5. **Error Handling**: Graceful handling of invalid configurations

## Testing

- Implemented unit and integration tests for the config schemas and usage.
- Used the `temporary_override` context manager for test isolation.

### Unit Tests

```python
import unittest
from config_manager import ConfigManager

class TestConfigManager(unittest.TestCase):
    def test_basic_config(self):
        config = ConfigManager()
        config.set('test.key', 'value')
        self.assertEqual(config.get('test.key'), 'value')
    
    def test_temporary_override(self):
        config = ConfigManager()
        config.set('test.key', 'original')
        
        with config.temporary_override('test.key', 'temporary'):
            self.assertEqual(config.get('test.key'), 'temporary')
        
        self.assertEqual(config.get('test.key'), 'original')
```

### Integration Tests

```python
def test_environment_override():
    os.environ['DATABASE_HOST'] = 'test-host'
    config = ConfigManager()
    assert config.get('database.host') == 'test-host'
```

## Production Deployment

### Best Practices

1. **Configuration Files**

   ```bash
   # Separate configs by environment
   /etc/myapp/
   ├── config.json          # Base configuration
   ├── config.prod.json     # Production overrides
   └── config.dev.json      # Development overrides
   ```

2. **Environment Variables**

   ```bash
   # Use environment-specific variables
   export ENV=production
   export CONFIG_FILES="/etc/myapp/config.json,/etc/myapp/config.prod.json"
   export DATABASE_PASSWORD_ENCRYPTED="enc:gAAAAABh..."
   ```

3. **Docker Integration**

   ```dockerfile
   # Copy configuration files
   COPY config/ /app/config/
   
   # Set environment variables
   ENV CONFIG_FILES="/app/config/config.json"
   ENV ENABLE_HOT_RELOAD=false
   ```

4. **Kubernetes ConfigMaps**

   ```yaml
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: app-config
   data:
     config.json: |
       {
         "database": {
           "host": "postgres-service",
           "port": 5432
         }
       }
   ```

## Configuration Reference

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `config_files` | `List[str]` | `["config.json", "config.yaml"]` | Configuration file paths |
| `enable_hot_reload` | `bool` | `True` | Enable automatic reloading |
| `reload_interval` | `int` | `30` | Reload check interval (seconds) |
| `enable_encryption` | `bool` | `False` | Enable value encryption |
| `encryption_key` | `bytes` | `None` | Custom encryption key |

### Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `get(key, default=None)` | Get configuration value | `Any` |
| `set(key, value, encrypt=False)` | Set configuration value | `None` |
| `get_database_config()` | Get database configuration | `Dict[str, Any]` |
| `get_api_config()` | Get API configuration | `Dict[str, Any]` |
| `get_metrics()` | Get access metrics | `Dict[str, Any]` |
| `health_check()` | Perform health check | `Dict[str, Any]` |
| `add_change_listener(callback)` | Add change listener | `None` |
| `remove_change_listener(callback)` | Remove change listener | `None` |
| `temporary_override(key, value)` | Context manager for temporary changes | `ContextManager` |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add comprehensive tests
4. Update documentation
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

---

## Installation

Add the component to your project (assuming you have the repo cloned):

```bash
cd components/config-management/configuration-manager
pip install -r requirements.txt  
```

**Dependencies:**

- Python 3.7+
- `pyyaml`, `cryptography`

---

## Usage

### Usage & Example Scenarios

All usage, including quick-start and advanced scenarios, is provided as standalone scripts in the `examples/` directory. Here is a key example:

- `examples/basic_usage.py`: Initialize the configuration manager, access configs, view metrics, and use temporary overrides.

See the `examples/` directory and `examples/README.md` for more advanced and scenario-based usage scripts.

**How to run an example:**

> **Important:** Always run the example scripts with the parent directory in your `PYTHONPATH` so that imports work correctly.

On Windows PowerShell:

```pwsh
$env:PYTHONPATH="."; python .\examples\basic_usage.py
```

On Linux/macOS/bash:

```bash
PYTHONPATH=. python ./examples/basic_usage.py
```

Replace `basic_usage.py` with any other example script as needed.

These scripts demonstrate real-world backend scenarios, including config loading, validation, encryption, and observability. You can use or extend them for your own use-cases.

#### Minimal Quick-Start (copy-paste into your own script)

```python
from config_manager import ConfigManager

config = ConfigManager(
    config_files=["config.json", "config.yaml"],
    enable_hot_reload=True,
    enable_encryption=True
)
```

---

### Environment Variable Overrides

Set environment variables to override config values:

```bash
export DATABASE_HOST=prod-db.example.com
export API_KEY=prod-api-key
```

---

## API Reference

### Initialization

```python
ConfigManager(
    config_files: Optional[List[str]] = None,
    enable_hot_reload: bool = True,
    reload_interval: int = 30,
    enable_encryption: bool = False,
    encryption_key: Optional[bytes] = None
)
```

### Core Methods

- `get(key_path: str, default: Any = None) -> Any`: Retrieve a config value (dot notation supported).
- `set(key_path: str, value: Any, encrypt: bool = False)`: Set a config value, optionally encrypted.
- `get_database_config() -> Dict[str, Any]`: Get validated database config.
- `get_api_config() -> Dict[str, Any]`: Get validated API config.
- `add_change_listener(listener)`: Register a callback for config changes.
- `remove_change_listener(listener)`: Remove a change listener.
- `get_metrics() -> Dict[str, Any]`: Get access, cache, reload, and validation metrics.
- `health_check() -> Dict[str, Any]`: Get health and status info.
- `temporary_override(key_path, value)`: Context manager for temporary config overrides.

---

## Security & Best Practices

- **Encryption**: Use `enable_encryption=True` for sensitive values (e.g., passwords, API keys).
- **Validation**: Extend or customize validators for your config schema.
- **Observability**: Monitor metrics and logs for config access and reloads.
- **Thread Safety**: Safe for use in multi-threaded applications.

---

## Metrics & Observability

The manager tracks:

- Access count, cache hits/misses
- Reload count, validation errors
- Last reload time, cache hit rate

Use `get_metrics()` to retrieve metrics for monitoring and alerting.

---

## Extending

Register custom validators for new config sections (see `validators` dict).
Integrate with your logging/monitoring stack as needed.
Add new config sources using the `RemoteConfigLoader` interface (e.g., HTTP, S3, etcd, Consul).

### Plugin/Extension Interfaces

You can extend the configuration manager with custom source plugins and hook plugins:

- **Source Plugins:** Inherit from `ConfigSourcePlugin`, implement `load()`, and register with `add_source_plugin()`.
- **Hook Plugins:** Inherit from `ConfigHookPlugin`, implement `on_config_change()`, and register with `add_hook_plugin()`.

#### Example Source Plugin

```python
from config_manager import ConfigSourcePlugin

class VaultConfigPlugin(ConfigSourcePlugin):
    def load(self):
        # Fetch config from Vault (mocked)
        return {"secrets": {"api_key": "vault-key"}}
```

#### Example Hook Plugin

```python
from config_manager import ConfigHookPlugin

class SlackNotificationHook(ConfigHookPlugin):
    def on_config_change(self, event, old_config, new_config):
        print("Config changed! Notifying Slack...")
```

#### Registering Plugins

```python
config = ConfigManager()
config.add_source_plugin(VaultConfigPlugin())
config.add_hook_plugin(SlackNotificationHook())
```

See `examples/plugin_examples.py` for a full demo.

---
