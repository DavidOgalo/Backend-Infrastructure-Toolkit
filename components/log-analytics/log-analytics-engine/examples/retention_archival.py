"""
Example: Log retention and archival simulation with LogAnalyticsEngine
Simulate log retention policies and periodic archival
"""

from datetime import datetime, timedelta, timezone

from log_analytics_engine import LogAnalyticsEngine, LogEntry


def main():
    engine = LogAnalyticsEngine()
    now = datetime.now(timezone.utc)
    # Ingest logs with timestamps over 2 days
    for i in range(48):
        ts = now - timedelta(hours=i)
        engine.ingest_log(
            LogEntry(
                timestamp=ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                level="INFO",
                message=f"Hourly log {i}",
                source="worker",
            )
        )
    # Simulate retention: keep only last 24 hours
    cutoff = (now - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    recent_logs = engine.query_logs(
        {"start_time": cutoff, "end_time": now.strftime("%Y-%m-%dT%H:%M:%SZ")}
    )
    print(f"Logs in last 24 hours: {len(recent_logs)}")
    # Simulate archival (just print count here)
    old_logs = engine.query_logs({"end_time": cutoff})
    print(f"Logs to archive: {len(old_logs)}")


if __name__ == "__main__":
    main()
