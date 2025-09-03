"""
Basic usage example for the LogAnalyticsEngine.
Demonstrates log ingestion and a simple query.
"""

from log_analytics_engine import LogAnalyticsEngine, LogEntry

engine = LogAnalyticsEngine()

log = LogEntry(
    timestamp="2025-07-21T12:00:00Z",
    level="ERROR",
    message="Database connection failed",
    source="db",
    tags=["db", "critical"],
)
engine.ingest_log(log)

results = engine.query_logs({"level": "ERROR"})
print("Queried logs:", results)
