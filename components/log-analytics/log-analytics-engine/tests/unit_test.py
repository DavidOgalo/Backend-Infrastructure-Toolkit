import unittest

from log_analytics_engine import AlertRule, AlertSeverity, LogAnalyticsEngine, LogEntry


class TestLogAnalyticsEngineUnit(unittest.TestCase):
    def setUp(self):
        self.engine = LogAnalyticsEngine()

    def test_ingest_log(self):
        log = LogEntry(
            timestamp="2025-07-21T12:00:00Z",
            level="INFO",
            message="Test log",
            source="test",
        )
        self.engine.ingest_log(log)
        self.assertEqual(len(self.engine.all_logs), 1)
        self.assertEqual(self.engine.level_index["INFO"][0].message, "Test log")

    def test_query_logs(self):
        log1 = LogEntry(
            timestamp="2025-07-21T12:00:00Z",
            level="ERROR",
            message="Error log",
            source="api",
        )
        log2 = LogEntry(
            timestamp="2025-07-21T12:01:00Z",
            level="INFO",
            message="Info log",
            source="api",
        )
        self.engine.ingest_logs([log1, log2])
        results = self.engine.query_logs({"level": "ERROR"})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].level, "ERROR")

    def test_alert_rule(self):
        rule = AlertRule(
            name="TestAlert",
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
        alerts = self.engine.get_alerts()
        self.assertTrue(any(a.rule_name == "TestAlert" for a in alerts))


if __name__ == "__main__":
    unittest.main()
