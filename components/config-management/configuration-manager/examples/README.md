# Configuration Manager Examples

All usage, including quick-start and advanced scenarios, is provided as standalone scripts in this `examples/` directory.

Key examples:

- `basic_usage.py`: Initialize the configuration manager, access configs, view metrics, and use temporary overrides.
- `hot_reload_demo.py`: Demonstrates hot reloading when config files change.
- `env_override_demo.py`: Shows environment variable precedence over file config.
- `encryption_demo.py`: Store and retrieve encrypted configuration values.
- `validation_error_demo.py`: Handles and demonstrates schema validation errors.
- `remote_config_usage.py`: Demonstrates loading configuration from a remote HTTP source using the pluggable loader interface.

See the scripts for more advanced and scenario-based usage.

Remote config loading is now supported via extensible loader interfaces (see `remote_config_usage.py` for an HTTP example). You can implement your own loaders for S3, etcd, Consul, and more.

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

To run the remote config loader example:

```pwsh
$env:PYTHONPATH="."; python .\examples\remote_config_usage.py
```

Replace with your own loader or source as needed.

You can use or extend these scripts for your own use-cases.
