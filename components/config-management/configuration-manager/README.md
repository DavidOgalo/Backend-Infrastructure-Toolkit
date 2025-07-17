# Configuration Manager

A production-ready, extensible configuration management system for modern backend services. This component provides centralized, multi-source configuration with environment variable overrides, hot reloading, schema validation, encryption, and observability.

---

## Features

- **Multi-source configuration**: Load from JSON, YAML, environment variables, and remote sources.
- **Environment variable precedence**: Override config values with environment variables for flexible deployments.
- **Hot reloading**: Detects file changes and reloads configuration automatically without downtime.
- **Nested key access**: Retrieve deeply nested config values using dot notation (e.g., `database.host`).
- **Type-safe retrieval**: Automatic type coercion and schema validation for robust config usage.
- **Encryption support**: Secure sensitive values with built-in encryption/decryption.
- **Comprehensive logging & metrics**: Built-in metrics for access, cache, reloads, and validation errors.
- **Thread-safe**: Safe for concurrent access in multi-threaded environments.
- **Extensible validation**: Register custom validators for different config sections.
- **Change listeners**: Subscribe to config changes for dynamic reconfiguration.

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

### Basic Example

```python
from config_manager import ConfigManager

config = ConfigManager(
    config_files=["config.json", "config.yaml"],
    enable_hot_reload=True,
    enable_encryption=True
)

# Access config values
host = config.get('database.host')
api_key = config.get('api.key')

# Set a value (optionally encrypted)
config.set('database.password', 'supersecret', encrypt=True)

# Use validated helpers
db_cfg = config.get_database_config()
api_cfg = config.get_api_config()

# Add a change listener
config.add_change_listener(lambda event, old, new: print("Config changed!"))

# Metrics and health
print(config.get_metrics())
print(config.health_check())
```

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

- Add new config sources (e.g., remote, secrets manager) by extending the loader logic.
- Register custom validators for new config sections.
- Integrate with your logging/monitoring stack as needed.

---

## Testing

- Unit and integration tests are recommended for your config schemas and usage.
- Use the `temporary_override` context manager for test isolation.

---
