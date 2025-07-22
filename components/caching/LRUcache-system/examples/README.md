# LRU Cache System Examples

All usage, including quick-start and advanced scenarios, is provided as standalone scripts in this `examples/` directory.

Key examples:

- `basic_usage.py`: Basic set/get, batch operations, metrics, and health check.
- `batch_and_eviction.py`: Batch operations and LRU eviction scenario.
- `ttl_expiry.py`: Demonstrates automatic expiration of cache items (TTL).
- `function_decorator.py`: Function result caching using the lru_cache decorator.
- `serialization.py`: Save and restore cache state (serialization/deserialization).
- `metrics_and_hooks.py`: Track cache metrics and observe event hooks.

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
