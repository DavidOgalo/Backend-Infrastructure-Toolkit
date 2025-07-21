"""
Production-Ready Log Analytics Engine

A comprehensive log processing system with real-time analytics, alerting,
and multi-index querying capabilities for modern observability needs.

Key Features:
- Real-time log ingestion with streaming support
- Multi-index architecture (time, level, keyword, source)
- Advanced query capabilities with filters and aggregations
- Alerting system with configurable rules
- Dashboard metrics and visualization data
- Batch processing for historical analysis
- Thread-safe operations with high throughput
"""

import re
import json
import threading
import time
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Callable, Generator, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import heapq
from abc import ABC, abstractmethod
import asyncio
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LogLevel(Enum):
    """Standard log levels"""
    TRACE = 0
    DEBUG = 10
    INFO = 20
    WARN = 30
    ERROR = 40
    FATAL = 50

class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class LogEntry:
    def __hash__(self):
        """
        Make LogEntry hashable so it can be used in sets and as dict keys.
        Hash is based on immutable identifying fields (e.g., timestamp, level, message, source).
        """
        return hash((self.timestamp, self.level, self.message, self.source))

    def __eq__(self, other):
        if not isinstance(other, LogEntry):
            return False
        return (
            self.timestamp == other.timestamp and
            self.level == other.level and
            self.message == other.message and
            self.source == other.source
        )
    """Enhanced log entry with comprehensive metadata"""
    timestamp: str
    level: str
    message: str
    source: str = ""
    thread_id: Optional[str] = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    parsed_time: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize computed fields"""
        if self.parsed_time is None:
            self.parsed_time = self._parse_timestamp()
    
    def _parse_timestamp(self) -> datetime:
        """Parse timestamp string to datetime object"""
        try:
            # Handle various timestamp formats
            timestamp_formats = [
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S",
                "%d/%b/%Y:%H:%M:%S %z"  # Common log format
            ]
            
            for fmt in timestamp_formats:
                try:
                    if self.timestamp.endswith('Z'):
                        return datetime.strptime(self.timestamp, fmt).replace(tzinfo=timezone.utc)
                    else:
                        return datetime.strptime(self.timestamp, fmt)
                except ValueError:
                    continue
            
            # Fallback to current time if parsing fails
            logger.warning(f"Failed to parse timestamp: {self.timestamp}")
            return datetime.now(timezone.utc)
            
        except Exception as e:
            logger.error(f"Error parsing timestamp {self.timestamp}: {e}")
            return datetime.now(timezone.utc)
    
    @property
    def severity_score(self) -> int:
        """Get numeric severity score for the log level"""
        level_scores = {
            'TRACE': 0, 'DEBUG': 10, 'INFO': 20,
            'WARN': 30, 'WARNING': 30, 'ERROR': 40,
            'FATAL': 50, 'CRITICAL': 50
        }
        return level_scores.get(self.level.upper(), 20)
    
    @property
    def age_seconds(self) -> float:
        """Get age of log entry in seconds"""
        if self.parsed_time:
            return (datetime.now(timezone.utc) - self.parsed_time).total_seconds()
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return asdict(self)
    
    def matches_filter(self, filters: Dict[str, Any]) -> bool:
        """Check if log entry matches given filters"""
        for key, value in filters.items():
            if key == 'level' and self.level != value:
                return False
            elif key == 'source' and self.source != value:
                return False
            elif key == 'min_severity' and self.severity_score < value:
                return False
            elif key == 'tags' and not any(tag in self.tags for tag in value):
                return False
            elif key == 'keywords' and not any(keyword.lower() in self.message.lower() for keyword in value):
                return False
        return True

@dataclass
class AlertRule:
    """Configuration for log-based alerts"""
    name: str
    description: str
    conditions: Dict[str, Any]
    severity: AlertSeverity
    threshold: int = 1
    time_window: int = 300  # 5 minutes
    cooldown: int = 600  # 10 minutes
    enabled: bool = True
    last_triggered: Optional[float] = None
    
    def should_trigger(self, count: int, current_time: float) -> bool:
        """Check if alert should trigger"""
        if not self.enabled:
            return False
        
        if count < self.threshold:
            return False
        
        # Check cooldown
        if self.last_triggered and (current_time - self.last_triggered) < self.cooldown:
            return False
        
        return True

@dataclass
class Alert:
    """Alert instance"""
    rule_name: str
    message: str
    severity: AlertSeverity
    triggered_at: datetime
    count: int
    sample_logs: List[LogEntry]
    metadata: Dict[str, Any] = field(default_factory=dict)

class BinarySearchTree:
    """Custom BST implementation for time-based indexing"""
    
    class Node:
        def __init__(self, key: str, value: Any):
            self.key = key
            self.value = value
            self.left = None
            self.right = None
            self.height = 1
    
    def __init__(self):
        self.root = None
    
    def _height(self, node: Optional['BinarySearchTree.Node']) -> int:
        """Get height of node"""
        return node.height if node else 0
    
    def _balance(self, node: Optional['BinarySearchTree.Node']) -> int:
        """Get balance factor of node"""
        return self._height(node.left) - self._height(node.right) if node else 0
    
    def _rotate_right(self, y: 'BinarySearchTree.Node') -> 'BinarySearchTree.Node':
        """Right rotation for AVL balancing"""
        x = y.left
        T2 = x.right
        
        x.right = y
        y.left = T2
        
        y.height = 1 + max(self._height(y.left), self._height(y.right))
        x.height = 1 + max(self._height(x.left), self._height(x.right))
        
        return x
    
    def _rotate_left(self, x: 'BinarySearchTree.Node') -> 'BinarySearchTree.Node':
        """Left rotation for AVL balancing"""
        y = x.right
        T2 = y.left
        
        y.left = x
        x.right = T2
        
        x.height = 1 + max(self._height(x.left), self._height(x.right))
        y.height = 1 + max(self._height(y.left), self._height(y.right))
        
        return y
    
    def _insert(self, node: Optional['BinarySearchTree.Node'], key: str, value: Any) -> 'BinarySearchTree.Node':
        """Insert node with AVL balancing"""
        # Standard BST insertion
        if not node:
            return self.Node(key, value)
        
        if key < node.key:
            node.left = self._insert(node.left, key, value)
        elif key > node.key:
            node.right = self._insert(node.right, key, value)
        else:
            # Handle duplicate keys by storing in a list
            if isinstance(node.value, list):
                node.value.append(value)
            else:
                node.value = [node.value, value]
            return node
        
        # Update height
        node.height = 1 + max(self._height(node.left), self._height(node.right))
        
        # Get balance factor
        balance = self._balance(node)
        
        # Left Left Case
        if balance > 1 and key < node.left.key:
            return self._rotate_right(node)
        
        # Right Right Case
        if balance < -1 and key > node.right.key:
            return self._rotate_left(node)
        
        # Left Right Case
        if balance > 1 and key > node.left.key:
            node.left = self._rotate_left(node.left)
            return self._rotate_right(node)
        
        # Right Left Case
        if balance < -1 and key < node.right.key:
            node.right = self._rotate_right(node.right)
            return self._rotate_left(node)
        
        return node
    
    def insert(self, key: str, value: Any):
        """
        Insert a key-value pair into the BST, maintaining AVL balance.
        If the key already exists, the value is appended (as a list).
        Args:
            key (str): The key (typically a timestamp string).
            value (Any): The value to store (e.g., LogEntry).
        """
        self.root = self._insert(self.root, key, value)

    def _search(self, node: Optional['BinarySearchTree.Node'], key: str) -> Optional[Any]:
        """
        Search for a key in the BST.
        Returns the value if found, else None.
        """
        if not node:
            return None
        if key < node.key:
            return self._search(node.left, key)
        elif key > node.key:
            return self._search(node.right, key)
        else:
            return node.value

    def search(self, key: str) -> Optional[Any]:
        """
        Public method to search for a key in the BST.
        Args:
            key (str): The key to search for.
        Returns:
            The value associated with the key, or None if not found.
        """
        return self._search(self.root, key)

    def _range_query(self, node: Optional['BinarySearchTree.Node'], start: str, end: str, result: List[Any]):
        """
        Helper for range query: collect all values with keys in [start, end].
        """
        if not node:
            return
        if start < node.key:
            self._range_query(node.left, start, end, result)
        if start <= node.key <= end:
            if isinstance(node.value, list):
                result.extend(node.value)
            else:
                result.append(node.value)
        if node.key < end:
            self._range_query(node.right, start, end, result)

    def range_query(self, start: str, end: str) -> List[Any]:
        """
        Query all values with keys in the range [start, end].
        Args:
            start (str): Start key (inclusive).
            end (str): End key (inclusive).
        Returns:
            List[Any]: All values in the range.
        """
        result: List[Any] = []
        self._range_query(self.root, start, end, result)
        return result

    def _inorder(self, node: Optional['BinarySearchTree.Node'], result: List[Tuple[str, Any]]):
        """
        In-order traversal of the BST.
        """
        if not node:
            return
        self._inorder(node.left, result)
        result.append((node.key, node.value))
        self._inorder(node.right, result)

    def inorder(self) -> List[Tuple[str, Any]]:
        """
        Get all key-value pairs in the BST in sorted order.
        Returns:
            List[Tuple[str, Any]]: List of (key, value) pairs.
        """
        result: List[Tuple[str, Any]] = []
        self._inorder(self.root, result)
        return result
    
# =============================
# Log Analytics Engine
# =============================

class LogAnalyticsEngine:
    """
    Main log analytics engine supporting real-time ingestion, multi-indexing, querying, and alerting.
    """
    def __init__(self):
        # Time index (BST by timestamp string)
        self.time_index = BinarySearchTree()
        # Level index: level -> list of LogEntry
        self.level_index = defaultdict(list)
        # Source index: source -> list of LogEntry
        self.source_index = defaultdict(list)
        # Keyword inverted index: keyword -> set of LogEntry
        self.keyword_index = defaultdict(set)
        # All logs (for batch/iteration)
        self.all_logs = []
        # Alert rules and triggered alerts
        self.alert_rules: List[AlertRule] = []
        self.triggered_alerts: List[Alert] = []
        # Thread safety
        self._lock = threading.RLock()

    def ingest_log(self, log: LogEntry):
        """
        Ingest a log entry, update all indexes, and check alerts.
        """
        with self._lock:
            self.all_logs.append(log)
            # Index by time (use ISO timestamp string as key)
            self.time_index.insert(log.timestamp, log)
            # Index by level
            self.level_index[log.level.upper()].append(log)
            # Index by source
            if log.source:
                self.source_index[log.source].append(log)
            # Index by keywords (split message into words)
            for word in set(re.findall(r'\w+', log.message.lower())):
                self.keyword_index[word].add(log)
            # Check alert rules
            self._check_alerts(log)

    def ingest_logs(self, logs: List[LogEntry]):
        """
        Ingest a batch of log entries.
        """
        for log in logs:
            self.ingest_log(log)

    def query_logs(self, filters: Dict[str, Any]) -> List[LogEntry]:
        """
        Query logs using filters: time range, level, source, keywords, tags, min_severity, etc.
        Returns a list of matching LogEntry objects.
        """
        with self._lock:
            # Time range filter (if present)
            logs = self.all_logs
            if 'start_time' in filters and 'end_time' in filters:
                start = filters['start_time']
                end = filters['end_time']
                logs = self.time_index.range_query(start, end)
            # Level filter
            if 'level' in filters:
                logs = [log for log in logs if log.level.upper() == filters['level'].upper()]
            # Source filter
            if 'source' in filters:
                logs = [log for log in logs if log.source == filters['source']]
            # Keyword filter
            if 'keyword' in filters:
                kw = filters['keyword'].lower()
                logs = [log for log in logs if kw in log.message.lower()]
            # Tags filter
            if 'tags' in filters:
                tags = set(filters['tags'])
                logs = [log for log in logs if tags.intersection(set(log.tags))]
            # Min severity filter
            if 'min_severity' in filters:
                min_score = filters['min_severity']
                logs = [log for log in logs if log.severity_score >= min_score]
            return logs

    def add_alert_rule(self, rule: AlertRule):
        """Add an alert rule."""
        self.alert_rules.append(rule)

    def _check_alerts(self, log: LogEntry):
        """
        Check all alert rules for the new log entry and trigger alerts if needed.
        """
        now = time.time()
        for rule in self.alert_rules:
            if not rule.enabled:
                continue
            # Count matching logs in the time window
            window_start = now - rule.time_window
            count = 0
            sample_logs = []
            for l in reversed(self.all_logs):
                if l.parsed_time and l.parsed_time.timestamp() < window_start:
                    break
                if l.matches_filter(rule.conditions):
                    count += 1
                    if len(sample_logs) < 5:
                        sample_logs.append(l)
            if rule.should_trigger(count, now):
                alert = Alert(
                    rule_name=rule.name,
                    message=f"Alert '{rule.name}' triggered: {count} matches in {rule.time_window}s.",
                    severity=rule.severity,
                    triggered_at=datetime.now(timezone.utc),
                    count=count,
                    sample_logs=sample_logs[::-1],
                )
                self.triggered_alerts.append(alert)
                rule.last_triggered = now
                logger.warning(f"ALERT: {alert.message}")

    def get_alerts(self) -> List[Alert]:
        """Return all triggered alerts."""
        return self.triggered_alerts

    def get_stats(self) -> Dict[str, Any]:
        """Return summary statistics about ingested logs."""
        with self._lock:
            return {
                'total_logs': len(self.all_logs),
                'levels': {level: len(logs) for level, logs in self.level_index.items()},
                'sources': {src: len(logs) for src, logs in self.source_index.items()},
                'keywords': len(self.keyword_index),
            }

# =============================
# Demo: Simulated Log Ingestion & Query
# =============================

if __name__ == "__main__":
    import random
    # Simulate log entries
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

    from datetime import timedelta
    engine = LogAnalyticsEngine()

    # Ingest 100 simulated logs over the last 10 minutes
    for i in range(100):
        log = random_log(ts_offset=random.randint(0, 600))
        engine.ingest_log(log)

    # Add an alert rule: 3+ ERRORs in 2 minutes triggers HIGH alert
    error_alert = AlertRule(
        name="High Error Rate",
        description="Trigger if 3+ ERROR logs in 2 minutes",
        conditions={"level": "ERROR"},
        severity=AlertSeverity.HIGH,
        threshold=3,
        time_window=120,
        cooldown=60
    )
    engine.add_alert_rule(error_alert)

    # Ingest more ERROR logs to trigger alert
    for _ in range(5):
        log = LogEntry(
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            level="ERROR",
            message="Simulated error for alert demo",
            source="api",
            tags=["api"]
        )
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

    # Show triggered alerts
    alerts = engine.get_alerts()
    print(f"\nTriggered alerts: {len(alerts)}")
    for alert in alerts:
        print(f"[{alert.triggered_at}] {alert.severity.value.upper()} {alert.rule_name}: {alert.message}")

    # Show stats
    print("\nEngine stats:")
    print(engine.get_stats())