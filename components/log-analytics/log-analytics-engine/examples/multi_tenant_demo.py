"""
Example: Multi-tenant log analytics with LogAnalyticsEngine
Shows how to handle logs from multiple tenants/services and query per-tenant.
"""

import random
from datetime import datetime, timezone

from log_analytics_engine import LogAnalyticsEngine, LogEntry

tenants = ["tenantA", "tenantB", "tenantC"]
levels = ["INFO", "ERROR"]
sources = ["api", "db"]
messages = ["Login", "Logout", "DB error", "API timeout"]


def random_log(tenant):
    now = datetime.now(timezone.utc)
    return LogEntry(
        timestamp=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        level=random.choice(levels),
        message=random.choice(messages),
        source=random.choice(sources),
        tags=[tenant],
    )


def main():
    engine = LogAnalyticsEngine()
    # Ingest logs for multiple tenants
    for _ in range(100):
        tenant = random.choice(tenants)
        engine.ingest_log(random_log(tenant))
    # Query logs for tenantB
    tenant_logs = engine.query_logs({"tags": ["tenantB"]})
    print(f"Logs for tenantB: {len(tenant_logs)}")
    for log in tenant_logs[:5]:
        print(f"[{log.timestamp}] {log.level} {log.source}: {log.message}")


if __name__ == "__main__":
    main()
