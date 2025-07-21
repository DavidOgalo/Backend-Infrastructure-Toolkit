"""
Example: Dashboard metrics and summary statistics with LogAnalyticsEngine
"""
import random
from datetime import datetime, timezone, timedelta
from log_analytics_engine import LogAnalyticsEngine, LogEntry

def main():
    engine = LogAnalyticsEngine()
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
    def random_log():
        now = datetime.now(timezone.utc)
        return LogEntry(
            timestamp=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            level=random.choice(levels),
            message=random.choice(messages),
            source=random.choice(sources),
            tags=[random.choice(["auth", "api", "db", "worker", "cache"])]
        )
    # Ingest 200 logs
    for _ in range(200):
        engine.ingest_log(random_log())
    # Show dashboard metrics
    stats = engine.get_stats()
    print("\nDashboard Metrics:")
    print(f"Total logs: {stats['total_logs']}")
    print(f"Logs by level: {stats['levels']}")
    print(f"Logs by source: {stats['sources']}")
    print(f"Unique keywords: {stats['keywords']}")

if __name__ == "__main__":
    main()
