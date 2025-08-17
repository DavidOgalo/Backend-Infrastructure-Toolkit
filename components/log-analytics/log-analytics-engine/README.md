# Log Analytics Engine

A production-ready, high-performance log analytics engine for real-time log ingestion, multi-index querying, alerting, and observability. Designed for modern backend systems, this engine provides advanced log processing, flexible querying, and robust alerting capabilities.

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Extending the Engine](#extending-the-engine)
- [Testing](#testing)
- [Best Practices](#best-practices)
- [Contributing](#contributing)
- [License](#license)

## Overview

The Log Analytics Engine is a Python-based system for ingesting, indexing, querying, and analyzing logs in real time. It supports multi-indexing (by time, level, source, and keyword), advanced filtering, and a flexible alerting system. The engine is thread-safe, highly extensible, and suitable for both real-time and batch log analytics in modern backend environments.

For a comprehensive overview of the system architecture, design rationale, integration points, and deployment reference, see [System Design Document](./system_design.md).

## Key Features

- **Real-Time Log Ingestion**: Supports streaming, batch, and file-based log ingestion
- **Multi-Index Architecture**: Indexes by time (AVL/BST), level, source, keyword (inverted index), and tags
- **Advanced Query Capabilities**: Filter by time range, level, source, tags, keywords, severity, with sorting and pagination
- **Aggregation and Analytics**: Group by, histogram, and top-N queries
- **Configurable Alerting System**: Define rules with thresholds, time windows, cooldowns, and external notification hooks
- **Processing Pipeline**: Pre-ingest enrichment/filter hooks for custom log processing
- **Batch File Processing**: Efficient ingestion from JSONL or text files with performance tracking
- **Dashboard Integration**: Export metrics in Prometheus and JSON formats
- **Alert Persistence**: Save and reload triggered alerts to/from file
- **Thread-Safe**: Supports concurrent ingestion and querying
- **Extensible**: Easy to add new indexes, alert types, enrichment, or integrations

## Architecture

Major components and layers in the codebase:

```python
LogAnalyticsEngine
├── LogEntry (Rich log object with metadata, tags, severity)
├── BinarySearchTree (AVL for time-based queries)
├── Indexes (Level, Source, Keyword, Tags)
├── Alerting (AlertRule, Alert, Notification Hooks)
├── Processing Pipeline (Pre-ingest hooks)
├── Batch/File Processing
├── Dashboard Integration (Prometheus/JSON)
└── Thread Safety Layer (RLock)
```

## Installation

The engine is a standalone Python module requiring Python 3.7+.

```bash
# Clone the repository (if not already done)
git clone https://github.com/DavidOgalo/Backend-Infrastructure-Toolkit
cd Backend-Infrastructure-Toolkit/components/log-analytics/log-analytics-engine

# (Optional) Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (if any)
pip install -r requirements.txt  # No external dependencies by default
```

**Dependencies:**

- Python 3.7+
- Standard library (`json`, `threading`, `time`)

## Getting Started

### Basic Usage

```python
from log_analytics_engine import LogAnalyticsEngine, LogEntry

# Initialize the engine
engine = LogAnalyticsEngine()

# Ingest a single log
log = LogEntry(
    timestamp="2025-07-21T12:00:00Z",
    level="ERROR",
    message="Database connection failed",
    source="db",
    tags=["db", "critical"]
)
engine.ingest_log(log)
```

### Advanced Configuration

```python
from log_analytics_engine import LogAnalyticsEngine, AlertRule, AlertSeverity

# Initialize with alert rule
engine = LogAnalyticsEngine()

# Define and add an alert rule
rule = AlertRule(
    name="High Error Rate",
    description="Trigger if 3+ ERROR logs in 2 minutes",
    conditions={"level": "ERROR"},
    severity=AlertSeverity.HIGH,
    threshold=3,
    time_window=120,  # seconds
    cooldown=60
)
engine.add_alert_rule(rule)

# Add external notification hook
def notify(alert):
    print(f"External notification: {alert.message}")
engine.add_alert_notification_hook(notify)
```

## Usage

All usage scenarios, including quick-start and advanced examples, are provided as standalone scripts in the `examples/` directory. Key example:

- `examples/basic_usage.py`: Ingest a log and perform a simple query.

See the `examples/` directory and `examples/README.md` for more advanced and scenario-based usage scripts.

**How to run an example:**

> **Important:** Always run the example scripts with the parent directory in your `PYTHONPATH` to ensure imports work correctly.

On Windows PowerShell:

```pwsh
$env:PYTHONPATH="."; python .\examples\basic_usage.py
```

On Linux/macOS/bash:

```bash
PYTHONPATH=. python ./examples/basic_usage.py
```

Replace `basic_usage.py` with any other example script as needed.

### Use Cases

1. **Log Ingestion**

   ```python
   # Batch ingestion
   engine.ingest_logs([log1, log2])

   # File ingestion (JSONL or text)
   metrics = engine.ingest_logs_from_file("logs.jsonl", file_type="jsonl")
   print(metrics)  # {'file': ..., 'count': ..., 'duration_sec': ..., 'logs_per_sec': ...}
   ```

2. **Querying Logs**

   ```python
   # Query by time range and level
   results = engine.query_logs({
       "start_time": "2025-07-21T11:00:00Z",
       "end_time": "2025-07-21T12:00:00Z",
       "level": "ERROR"
   })

   # Query by keyword
   results = engine.query_logs({"keyword": "cache"})

   # Query by tags or source
   results = engine.query_logs({"tags": ["api"], "min_severity": 30})

   # Advanced: sorting and pagination
   results = engine.query_logs(
       {"level": "ERROR"}, sort_by="timestamp", sort_desc=True, page=0, page_size=50
   )
   ```

3. **Aggregation**

   ```python
   agg = engine.aggregate_logs(results, group_by="source", histogram="level", top_n={"tags": 5})
   print(agg)
   ```

4. **Alerting & Notification**

   ```python
   # Retrieve triggered alerts
   alerts = engine.get_alerts()
   for alert in alerts:
       print(alert)

   # Persist and reload alerts
   engine.persist_alerts_to_file("alerts.jsonl")
   engine.load_alerts_from_file("alerts.jsonl")
   ```

5. **Metrics & Dashboard Integration**

   ```python
   # Get summary stats
   stats = engine.get_stats()
   print(stats)

   # Export metrics for Prometheus
   prom_metrics = engine.export_metrics_prometheus()
   print(prom_metrics)

   # Export metrics as JSON for dashboards
   json_metrics = engine.export_metrics_json()
   print(json_metrics)
   ```

## API Reference

### LogEntry

- `timestamp`: ISO8601 string (UTC recommended)
- `level`: Log level (e.g., INFO, ERROR)
- `message`: Log message
- `source`: (Optional) Source system/component
- `tags`: (Optional) List of tags
- `metadata`: (Optional) Dict of extra fields
- `severity_score`: Numeric score for level
- `age_seconds`: Age of log in seconds
- `matches_filter(filters)`: Returns `True` if log matches filter dict

### LogAnalyticsEngine

| Method | Description |
|--------|-------------|
| `ingest_log(log: LogEntry)` | Ingest a single log |
| `ingest_logs(logs: List[LogEntry])` | Ingest multiple logs |
| `ingest_logs_from_file(file_path, file_type)` | Ingest logs from file (JSONL/text) |
| `add_pre_ingest_hook(hook_fn)` | Register enrichment/filter hook |
| `query_logs(filters, sort_by, sort_desc, page, page_size)` | Query logs with filters, sorting, pagination |
| `aggregate_logs(logs, group_by, histogram, top_n)` | Aggregate logs |
| `add_alert_rule(rule: AlertRule)` | Add an alert rule |
| `add_alert_notification_hook(hook_fn)` | Register external alert notification hook |
| `get_alerts() -> List[Alert]` | Get triggered alerts |
| `persist_alerts_to_file(file_path)` | Save alerts to file |
| `load_alerts_from_file(file_path)` | Load alerts from file |
| `get_stats() -> Dict` | Get summary stats |
| `export_metrics_prometheus() -> str` | Export metrics for Prometheus |
| `export_metrics_json() -> Dict` | Export metrics for dashboards |

### AlertRule

- `name`, `description`, `conditions`, `severity`, `threshold`, `time_window`, `cooldown`, `enabled`
- `should_trigger(count, current_time)`: Returns `True` if alert should fire

### Alert

- `rule_name`, `message`, `severity`, `triggered_at`, `count`, `sample_logs`, `metadata`

## Extending the Engine

- Add new indexes (e.g., `user_id`, `request_id`) by updating the `LogAnalyticsEngine` class
- Integrate with external alerting/notification systems using notification hooks
- Add support for log persistence (e.g., to disk or database)
- Implement custom enrichment/filter hooks for log processing
- Build custom dashboards using metrics export APIs
- Implement custom query operators or aggregations as needed

### Example: Custom Pre-Ingest Hook

```python
def enrich_log(log: LogEntry):
    log.metadata["env"] = "production"
    return log

engine.add_pre_ingest_hook(enrich_log)
```

## Testing

Tests are organized in the `tests/` directory:

- **Unit tests** (`test_unit.py`): Cover core engine logic, log ingestion, querying, and alert rule triggering
- **Integration tests** (`test_integration.py`): Validate batch file ingestion, alert notification hooks, and end-to-end scenarios
- **Performance tests** (`test_performance.py`): Measure ingestion throughput and engine scalability

### Running Tests

```bash
pytest tests/
# or
python -m unittest discover tests
```

## Best Practices

- Use ISO8601 UTC timestamps for all logs
- Define alert rules with appropriate thresholds and cooldowns
- Regularly monitor engine stats and triggered alerts
- Extend the engine for specific observability needs
- Use thread-safe operations for concurrent environments
- Export metrics to Prometheus/Grafana for real-time monitoring

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add comprehensive tests
4. Update documentation
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
