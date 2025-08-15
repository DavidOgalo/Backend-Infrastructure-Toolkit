# Log Analytics Engine

A production-ready, high-performance log analytics engine for real-time log ingestion, multi-index querying, alerting, and observability. Designed for modern backend systems, this engine provides advanced log processing, flexible querying, and robust alerting capabilities.

## Table of Contents

- [System Design & Architecture](#system-design--architecture)
- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Extending the Engine](#extending-the-engine)
- [Testing](#testing)
- [Best Practices](#best-practices)

---

## System Design & Architecture

For a comprehensive overview of the system architecture, design rationale, integration points and deployment reference see [System Design Document](./system_design.md).

---

## Overview

The **Log Analytics Engine** is a Python-based system for ingesting, indexing, querying, and analyzing logs in real time. It supports multi-indexing (by time, level, source, and keyword), advanced filtering, and a flexible alerting system. The engine is thread-safe, highly extensible, and suitable for both real-time and batch log analytics in modern backend environments.

---

## Features

- **Real-time log ingestion** with streaming, batch, and file support
- **Multi-index architecture**: time (AVL/BST), level, source, keyword (inverted index), tags
- **Advanced query capabilities**: filter by time range, level, source, tags, keywords, severity, with sorting and pagination
- **Aggregation and analytics**: group by, histogram, top-N queries
- **Configurable alerting system**: define rules with thresholds, time windows, cooldowns, and external notification hooks
- **Processing pipeline**: pre-ingest enrichment/filter hooks for custom log processing
- **Batch file processing**: ingest logs from JSONL or text files with performance tracking
- **Dashboard integration**: export metrics in Prometheus and JSON formats
- **Alert persistence**: save and reload triggered alerts to/from file
- **Thread-safe**: supports concurrent ingestion and querying
- **Extensible**: easy to add new indexes, alert types, enrichment, or integrations

---

## Architecture

- **LogEntry**: Rich log object with metadata, tags, severity scoring, and extensible fields
- **BinarySearchTree**: Custom AVL tree for efficient time-based queries
- **Indexes**: Dictionaries for level, source, keyword (inverted index), and tags
- **Alerting**: AlertRule and Alert classes for rule-based notifications and external hooks
- **Processing Pipeline**: Pre-ingest hooks for enrichment and filtering
- **Batch/File Processing**: Efficient ingestion from files with performance metrics
- **Dashboard Integration**: Metrics export for Prometheus/Grafana and JSON dashboards
- **Thread Safety**: Uses `threading.RLock` for safe concurrent access

---

## Installation

This engine is a standalone Python module. Requires Python 3.7+.

```bash
# Clone the repository (if not already done)
git clone https://github.com/DavidOgalo/Backend-Infrastructure-Toolkit
cd Backend-Infrastructure-Toolkit/components/log-analytics/log-analytics-engine

# (Optional) Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (if any)
pip install -r requirements.txt  # (No external dependencies by default)
```

---

## Usage

### Usage & Example Scenarios

All usage, including quick-start and advanced scenarios, is provided as standalone scripts in the `examples/` directory. Here is a key example:

- `examples/basic_usage.py`: Ingest a log and perform a simple query

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

These scripts demonstrate real-world backend scenarios, including log ingestion, querying, alerting, and dashboard metrics. You can use or extend them for your own use-cases.

> **Note:** The main implementation file does not contain any demo or usage code. All examples are in the `examples/` folder for clarity and best practice.

### Log Ingestion

```python
from log_analytics_engine import LogAnalyticsEngine, LogEntry

engine = LogAnalyticsEngine()
log = LogEntry(
    timestamp="2025-07-21T12:00:00Z",
    level="ERROR",
    message="Database connection failed",
    source="db",
    tags=["db", "critical"]
)
engine.ingest_log(log)

# Batch ingestion
engine.ingest_logs([log1, log2, ...])

# File ingestion (JSONL or text)
metrics = engine.ingest_logs_from_file("logs.jsonl", file_type="jsonl")
print(metrics)  # {'file': ..., 'count': ..., 'duration_sec': ..., 'logs_per_sec': ...}
```

### Querying Logs

#### Query by time range and level

```python
results = engine.query_logs({
    "start_time": "2025-07-21T11:00:00Z",
    "end_time": "2025-07-21T12:00:00Z",
    "level": "ERROR"
})
```

#### Query by keyword

```python
results = engine.query_logs({"keyword": "cache"})
```

#### Query by tags, source, or min severity

```python
results = engine.query_logs({"tags": ["api"], "min_severity": 30})
```

#### Advanced: sorting and pagination

```python
results = engine.query_logs(
    {"level": "ERROR"}, sort_by="timestamp", sort_desc=True, page=0, page_size=50
)
```

#### Aggregation: group by, histogram, top-N

```python
agg = engine.aggregate_logs(results, group_by="source", histogram="level", top_n={"tags": 5})
print(agg)
```

### Alerting & Notification

```python
# Define and add an alert rule
from log_analytics_engine import AlertRule, AlertSeverity

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

# Register external alert notification hook (e.g., send to webhook/email)
def notify(alert):
    print(f"External notification: {alert.message}")
engine.add_alert_notification_hook(notify)

# Alerts are triggered automatically during ingestion. Retrieve them
alerts = engine.get_alerts()
for alert in alerts:
    print(alert)

# Persist and reload alerts
engine.persist_alerts_to_file("alerts.jsonl")
engine.load_alerts_from_file("alerts.jsonl")
```

### Metrics & Dashboard Integration

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

---

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
- `matches_filter(filters)`: Returns True if log matches filter dict

### LogAnalyticsEngine

- `ingest_log(log: LogEntry)`: Ingest a single log
- `ingest_logs(logs: List[LogEntry])`: Ingest multiple logs
- `ingest_logs_from_file(file_path, file_type)`: Ingest logs from file (JSONL/text)
- `add_pre_ingest_hook(hook_fn)`: Register enrichment/filter hook
- `query_logs(filters, sort_by, sort_desc, page, page_size)`: Query logs with filters, sorting, pagination
- `aggregate_logs(logs, group_by, histogram, top_n)`: Aggregate logs
- `add_alert_rule(rule: AlertRule)`: Add an alert rule
- `add_alert_notification_hook(hook_fn)`: Register external alert notification hook
- `get_alerts() -> List[Alert]`: Get triggered alerts
- `persist_alerts_to_file(file_path)`: Save alerts to file
- `load_alerts_from_file(file_path)`: Load alerts from file
- `get_stats() -> Dict`: Get summary stats
- `export_metrics_prometheus() -> str`: Export metrics for Prometheus
- `export_metrics_json() -> Dict`: Export metrics for dashboards

### AlertRule

- `name`, `description`, `conditions`, `severity`, `threshold`, `time_window`, `cooldown`, `enabled`
- `should_trigger(count, current_time)`: Returns True if alert should fire

### Alert

- `rule_name`, `message`, `severity`, `triggered_at`, `count`, `sample_logs`, `metadata`

---

## Extending the Engine

- Add new indexes (e.g., user_id, request_id) by updating the `LogAnalyticsEngine` class
- Integrate with external alerting/notification systems using notification hooks
- Add support for log persistence (e.g., to disk or database)
- Implement custom enrichment/filter hooks for log processing
- Build custom dashboards using metrics export APIs
- Implement custom query operators or aggregations as needed

## Testing

All tests are implemented in the `tests/` directory and follow a modular structure:

- **Unit tests** (`tests/test_unit.py`): Cover core engine logic, log ingestion, querying, and alert rule triggering.
- **Integration tests** (`tests/test_integration.py`): Validate batch file ingestion, alert notification hooks, and end-to-end scenarios.
- **Performance tests** (`tests/test_performance.py`): Measure ingestion throughput and engine scalability.

Run all tests using `pytest` or `unittest`:

```bash
pytest tests/
# or
python -m unittest discover tests
```

## Best Practices

- Use ISO8601 UTC timestamps for all logs
- Define alert rules with appropriate thresholds and cooldowns
- Regularly monitor engine stats and triggered alerts
- Extend the engine for your specific observability needs
