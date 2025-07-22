# Configuration Manager Examples

All usage, including quick-start and advanced scenarios, is provided as standalone scripts in this `examples/` directory.

Key examples:

- `basic_usage.py`: Initialize the configuration manager, access configs, view metrics, and use temporary overrides.
- `hot_reload_demo.py`: Demonstrates hot reloading when config files change.
- `env_override_demo.py`: Shows environment variable precedence over file config.
- `encryption_demo.py`: Store and retrieve encrypted configuration values.
- `validation_error_demo.py`: Handles and demonstrates schema validation errors.

See the scripts for more advanced and scenario-based usage.

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

You can use or extend these scripts for your own use-cases.
