import json
import os
import unittest

from log_analytics_engine import AlertRule, AlertSeverity, LogAnalyticsEngine, LogEntry


class TestLogAnalyticsEngineIntegration(unittest.TestCase):
    def setUp(self):
        self.engine = LogAnalyticsEngine()

    def test_batch_file_ingestion_and_metrics(self):
        # Create sample logs and write to file
        logs = [
            {
                "timestamp": "2025-07-21T12:00:00Z",
                "level": "INFO",
                "message": "Log1",
                "source": "api",
            },
            {
                "timestamp": "2025-07-21T12:01:00Z",
                "level": "ERROR",
                "message": "Log2",
                "source": "db",
            },
        ]
        file_path = "test_logs.jsonl"
        with open(file_path, "w", encoding="utf-8") as f:
            for log in logs:
                f.write(json.dumps(log) + "\n")
        metrics = self.engine.ingest_logs_from_file(file_path, file_type="jsonl")
        self.assertEqual(metrics["count"], 2)
        os.remove(file_path)

    def test_alert_notification_hook(self):
        notifications = []

        def notify(alert):
            notifications.append(alert.message)

        self.engine.add_alert_notification_hook(notify)
        rule = AlertRule(
            name="IntegrationAlert",
            description="Test",
            conditions={"level": "ERROR"},
            severity=AlertSeverity.HIGH,
            threshold=1,
        )
        self.engine.add_alert_rule(rule)
        log = LogEntry(
            timestamp="2025-07-21T12:00:00Z",
            level="ERROR",
            message="Error log",
            source="api",
        )
        self.engine.ingest_log(log)
        self.assertTrue(any("IntegrationAlert" in msg for msg in notifications))


if __name__ == "__main__":
    unittest.main()
