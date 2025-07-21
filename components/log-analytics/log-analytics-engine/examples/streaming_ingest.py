"""
Example: Real-time streaming log ingestion with LogAnalyticsEngine
Simulate logs arriving in real time (e.g., from a microservice or event stream), and process them as they come in.
"""
import random
import time
from datetime import datetime, timezone
from log_analytics_engine import LogAnalyticsEngine, LogEntry

levels = ["INFO", "DEBUG", "WARN", "ERROR"]
sources = ["auth", "api", "db", "worker"]
messages = [
    "User login successful", "User login failed", "Database connection error",
    "API request timeout", "Worker started", "Worker stopped",
    "Cache miss", "Cache hit", "Permission denied", "Resource not found"
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

def main():
    engine = LogAnalyticsEngine()
    print("Streaming logs (press Ctrl+C to stop)...")
    try:
        while True:
            log = random_log()
            engine.ingest_log(log)
            print(f"Ingested: [{log.timestamp}] {log.level} {log.source}: {log.message}")
            time.sleep(0.5)  # Simulate log arrival every 0.5s
    except KeyboardInterrupt:
        print("\nStopped streaming.")
        print("Final stats:", engine.get_stats())

if __name__ == "__main__":
    main()