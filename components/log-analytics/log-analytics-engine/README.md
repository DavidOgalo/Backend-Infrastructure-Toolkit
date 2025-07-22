# Log Analytics Engine

A production-ready, high-performance log analytics engine for real-time log ingestion, multi-index querying, alerting, and observability. Designed for modern backend systems, this engine provides advanced log processing, flexible querying, and robust alerting capabilities.

---

## Table of Contents

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

## Overview

The **Log Analytics Engine** is a Python-based system for ingesting, indexing, querying, and analyzing logs in real time. It supports multi-indexing (by time, level, source, and keyword), advanced filtering, and a flexible alerting system. The engine is thread-safe, highly extensible, and suitable for both real-time and batch log analytics in modern backend environments.

---

## Features

- **Real-time log ingestion** with streaming and batch support
- **Multi-index architecture**: time (AVL/BST), level, source, keyword (inverted index)
- **Advanced query capabilities**: filter by time range, level, source, tags, keywords, severity, etc.
- **Configurable alerting system**: define rules with thresholds, time windows, and cooldowns
- **Dashboard metrics**: summary stats for observability
- **Thread-safe**: supports concurrent ingestion and querying
- **Extensible**: easy to add new indexes, alert types, or integrations

---

## Architecture

- **LogEntry**: Rich log object with metadata, tags, and severity scoring
- **BinarySearchTree**: Custom AVL tree for efficient time-based queries
- **Indexes**: Dictionaries for level, source, and keyword (inverted index)
- **Alerting**: AlertRule and Alert classes for rule-based notifications
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

All usage, including quick-start and advanced scenarios, is provided as standalone scripts in the `examples/` directory. Here are a few key examples:

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
```

Batch ingestion:

```python
engine.ingest_logs([log1, log2, ...])
```

### Querying Logs

Query by time range and level:

```python
results = engine.query_logs({
    "start_time": "2025-07-21T11:00:00Z",
    "end_time": "2025-07-21T12:00:00Z",
    "level": "ERROR"
})
```

Query by keyword:

```python
results = engine.query_logs({"keyword": "cache"})
```

Query by tags, source, or min severity:

```python
results = engine.query_logs({"tags": ["api"], "min_severity": 30})
```

### Alerting

Define and add an alert rule:

```python
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
```

Alerts are triggered automatically during ingestion. Retrieve them:

```python
alerts = engine.get_alerts()
for alert in alerts:
    print(alert)
```

### Metrics & Stats

```python
stats = engine.get_stats()
print(stats)
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
- `query_logs(filters: Dict) -> List[LogEntry]`: Query logs by filters
- `add_alert_rule(rule: AlertRule)`: Add an alert rule
- `get_alerts() -> List[Alert]`: Get triggered alerts
- `get_stats() -> Dict`: Get summary stats

### AlertRule

- `name`, `description`, `conditions`, `severity`, `threshold`, `time_window`, `cooldown`, `enabled`
- `should_trigger(count, current_time)`: Returns True if alert should fire

### Alert

- `rule_name`, `message`, `severity`, `triggered_at`, `count`, `sample_logs`, `metadata`

---

## Extending the Engine

- Add new indexes (e.g., user_id, request_id) by updating the `LogAnalyticsEngine` class
- Integrate with external alerting/notification systems by extending the alerting logic
- Add support for log persistence (e.g., to disk or database)
- Implement custom query operators or aggregations as needed

## Testing

- The demo in `log_analytics_engine.py` provides a basic test scenario
- For unit tests, use `pytest` or `unittest` and mock log entries/alert rules
- Ensure thread safety by testing concurrent ingestion and queries

## Best Practices

- Use ISO8601 UTC timestamps for all logs
- Define alert rules with appropriate thresholds and cooldowns
- Regularly monitor engine stats and triggered alerts
- Extend the engine for your specific observability needs
