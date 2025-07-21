"""
Example: Ingest logs and perform basic queries with LogAnalyticsEngine
"""
import random
from datetime import datetime, timezone, timedelta
from log_analytics_engine import LogAnalyticsEngine, LogEntry

levels = ["INFO", "DEBUG", "WARN", "ERROR"]
sources = ["auth", "api", "db", "worker"]
messages = [
    "User login successful",
    "User login failed",
    "Database connection error",
    "API request timeout",
    "Worker started",
    "Worker stopped",
    "Cache miss",
    "Cache hit",
    "Permission denied",
    "Resource not found"
]

def random_log(ts_offset=0):
    now = datetime.now(timezone.utc) - timedelta(seconds=ts_offset)
    return LogEntry(
        timestamp=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        level=random.choice(levels),
        message=random.choice(messages),
        source=random.choice(sources),
        tags=[random.choice(["auth", "api", "db", "worker", "cache"])]
    )

def main():
    engine = LogAnalyticsEngine()
    # Ingest 100 simulated logs over the last 10 minutes
    for i in range(100):
        log = random_log(ts_offset=random.randint(0, 600))
        engine.ingest_log(log)
    # Query: All ERROR logs in the last 5 minutes
    start = (datetime.now(timezone.utc) - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    end = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    error_logs = engine.query_logs({"start_time": start, "end_time": end, "level": "ERROR"})
    print(f"\nERROR logs in last 5 minutes: {len(error_logs)}")
    for log in error_logs[:3]:
        print(f"[{log.timestamp}] {log.level} {log.source}: {log.message}")
    if len(error_logs) > 3:
        print(f"...and {len(error_logs)-3} more")
    # Query: All logs with 'cache' keyword
    cache_logs = engine.query_logs({"keyword": "cache"})
    print(f"\nLogs with 'cache' keyword: {len(cache_logs)}")
    for log in cache_logs[:3]:
        print(f"[{log.timestamp}] {log.level} {log.source}: {log.message}")
    if len(cache_logs) > 3:
        print(f"...and {len(cache_logs)-3} more")
    # Show stats
    print("\nEngine stats:")
    print(engine.get_stats())

if __name__ == "__main__":
    main()
