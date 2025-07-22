# Log Analytics Engine Examples

All usage, including quick-start and advanced scenarios, is provided as standalone scripts in this `examples/` directory.

Key examples:

- `basic_usage.py`: Ingest a log and perform a simple query.
- `ingest_and_query.py`: Ingest multiple logs and perform advanced queries.
- `alerting_demo.py`: Demonstrates alerting use-cases.
- `dashboard_metrics.py`: Shows dashboard metrics and stats.
- `custom_alerts.py`: Define and trigger custom alert rules.
- `streaming_ingest.py`: Simulate real-time/streaming log ingestion.
- `multi_tenant_demo.py`: Multi-tenant log analytics scenario.
- `retention_archival.py`: Demonstrates log retention and archival logic.

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
