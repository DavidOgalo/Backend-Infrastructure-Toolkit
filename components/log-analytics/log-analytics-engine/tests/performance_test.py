import time
import unittest

from log_analytics_engine import LogAnalyticsEngine, LogEntry


class TestLogAnalyticsEnginePerformance(unittest.TestCase):
    def setUp(self):
        self.engine = LogAnalyticsEngine()

    def test_high_throughput_ingestion(self):
        logs = [
            LogEntry(
                timestamp="2025-07-21T12:00:00Z",
                level="INFO",
                message=f"Log {i}",
                source="perf",
            )
            for i in range(1000)
        ]
        start = time.time()
        self.engine.ingest_logs(logs)
        duration = time.time() - start
        self.assertLess(duration, 2)  # Should ingest 1000 logs in under 2 seconds
        self.assertEqual(len(self.engine.all_logs), 1000)


if __name__ == "__main__":
    unittest.main()
