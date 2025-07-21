"""
Example: Custom alerting with multiple conditions in LogAnalyticsEngine
Demonstrate alerting on complex conditions (e.g., ERROR logs from a specific source and keyword).
"""
from datetime import datetime, timezone
from log_analytics_engine import LogAnalyticsEngine, LogEntry, AlertRule, AlertSeverity

def main():
    engine = LogAnalyticsEngine()
    # Add a custom alert: 2+ ERRORs from 'db' containing 'timeout' in 1 minute
    alert_rule = AlertRule(
        name="DB Timeout Spike",
        description="Trigger if 2+ ERROR logs from db with 'timeout' in 1 minute",
        conditions={"level": "ERROR", "source": "db", "keywords": ["timeout"]},
        severity=AlertSeverity.CRITICAL,
        threshold=2,
        time_window=60,
        cooldown=30
    )
    engine.add_alert_rule(alert_rule)
    # Ingest logs to trigger alert
    now = datetime.now(timezone.utc)
    logs = [
        LogEntry(timestamp=now.strftime("%Y-%m-%dT%H:%M:%SZ"), level="ERROR", message="DB timeout error", source="db"),
        LogEntry(timestamp=now.strftime("%Y-%m-%dT%H:%M:%SZ"), level="ERROR", message="DB timeout again", source="db"),
    ]
    for log in logs:
        engine.ingest_log(log)
    # Show alerts
    alerts = engine.get_alerts()
    print(f"Triggered alerts: {len(alerts)}")
    for alert in alerts:
        print(f"[{alert.triggered_at}] {alert.severity.value.upper()} {alert.rule_name}: {alert.message}")

if __name__ == "__main__":
    main()