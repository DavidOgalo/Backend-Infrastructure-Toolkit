"""
Example: Alerting with LogAnalyticsEngine
"""

import random
from datetime import datetime, timezone

from log_analytics_engine import AlertRule, AlertSeverity, LogAnalyticsEngine, LogEntry


def main():
    engine = LogAnalyticsEngine()
    # levels = ["INFO", "DEBUG", "WARN", "ERROR"]  # Unused variable removed
    sources = ["auth", "api", "db", "worker"]
    messages = [
        "User login failed",
        "Database connection error",
        "API request timeout",
        "Permission denied",
    ]

    def random_error_log():
        now = datetime.now(timezone.utc)
        return LogEntry(
            timestamp=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            level="ERROR",
            message=random.choice(messages),
            source=random.choice(sources),
            tags=[random.choice(["api", "db", "worker"])],
        )

    # Add an alert rule: 3+ ERRORs in 2 minutes triggers HIGH alert
    error_alert = AlertRule(
        name="High Error Rate",
        description="Trigger if 3+ ERROR logs in 2 minutes",
        conditions={"level": "ERROR"},
        severity=AlertSeverity.HIGH,
        threshold=3,
        time_window=120,
        cooldown=60,
    )
    engine.add_alert_rule(error_alert)
    # Ingest 5 ERROR logs to trigger alert
    for _ in range(5):
        log = random_error_log()
        engine.ingest_log(log)
    # Show triggered alerts
    alerts = engine.get_alerts()
    print(f"\nTriggered alerts: {len(alerts)}")
    for alert in alerts:
        print(
            f"[{alert.triggered_at}] {alert.severity.value.upper()} {alert.rule_name}: {alert.message}"
        )


if __name__ == "__main__":
    main()
