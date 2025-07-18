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