"""
Message Queue System - Production-Ready Implementation

A comprehensive message queue implementation with multiple queue types,
persistence, monitoring, and enterprise-grade features.
"""

import asyncio
import heapq
import json
import logging
import pickle
import signal
import sys
import threading
import time
import uuid
from abc import ABC, abstractmethod
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Generic, List, Optional, TypeVar

# Type variables
T = TypeVar("T")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessagePriority(Enum):
    """Message priority levels"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class MessageStatus(Enum):
    """Message processing status"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class QueueType(Enum):
    """Queue implementation types"""

    FIFO = "fifo"
    LIFO = "lifo"
    PRIORITY = "priority"
    DELAY = "delay"


@dataclass
class Message:
    """Message data structure"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    payload: Any = None
    priority: MessagePriority = MessagePriority.NORMAL
    created_at: float = field(default_factory=time.time)
    processed_at: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    delay_until: Optional[float] = None
    headers: Dict[str, Any] = field(default_factory=dict)
    status: MessageStatus = MessageStatus.PENDING
    consumer_id: Optional[str] = None

    def __lt__(self, other):
        """Enable priority queue comparison"""
        if not isinstance(other, Message):
            return NotImplemented
        # Higher priority first, then older messages
        return (self.priority.value, -self.created_at) > (
            other.priority.value,
            -other.created_at,
        )


@dataclass
class ConsumerConfig:
    """Consumer configuration"""

    consumer_id: str
    batch_size: int = 1
    timeout: float = 30.0
    max_workers: int = 1
    auto_ack: bool = True


@dataclass
class QueueMetrics:
    """Queue metrics tracking"""

    messages_published: int = 0
    messages_consumed: int = 0
    messages_failed: int = 0
    messages_retried: int = 0
    queue_size: int = 0
    processing_count: int = 0
    dead_letter_count: int = 0
    avg_processing_time: float = 0.0
    last_activity: float = field(default_factory=time.time)


class MessageHandler(ABC):
    """Abstract message handler interface"""

    @abstractmethod
    async def handle(self, message: Message) -> bool:
        """Handle a message, return True if successful"""
        pass

    @abstractmethod
    async def on_failure(self, message: Message, error: Exception) -> None:
        """Handle message processing failure"""
        pass


class BaseQueue(ABC, Generic[T]):
    """Base queue interface"""

    @abstractmethod
    def put(self, item: T, timeout: Optional[float] = None) -> bool:
        """Add item to queue"""
        pass

    @abstractmethod
    def get(self, timeout: Optional[float] = None) -> Optional[T]:
        """Get item from queue"""
        pass

    @abstractmethod
    def size(self) -> int:
        """Get queue size"""
        pass

    @abstractmethod
    def empty(self) -> bool:
        """Check if queue is empty"""
        pass


class FIFOQueue(BaseQueue[Message]):
    """First In, First Out queue implementation"""

    def __init__(self, maxsize: int = 0):
        self._queue = deque()
        self._maxsize = maxsize
        self._lock = threading.RLock()

    def put(self, item: Message, timeout: Optional[float] = None) -> bool:
        with self._lock:
            if self._maxsize > 0 and len(self._queue) >= self._maxsize:
                return False
            self._queue.append(item)
            return True

    def get(self, timeout: Optional[float] = None) -> Optional[Message]:
        with self._lock:
            if not self._queue:
                return None
            return self._queue.popleft()

    def size(self) -> int:
        with self._lock:
            return len(self._queue)

    def empty(self) -> bool:
        with self._lock:
            return len(self._queue) == 0


class LIFOQueue(BaseQueue[Message]):
    """Last In, First Out queue implementation"""

    def __init__(self, maxsize: int = 0):
        self._queue = []
        self._maxsize = maxsize
        self._lock = threading.RLock()

    def put(self, item: Message, timeout: Optional[float] = None) -> bool:
        with self._lock:
            if self._maxsize > 0 and len(self._queue) >= self._maxsize:
                return False
            self._queue.append(item)
            return True

    def get(self, timeout: Optional[float] = None) -> Optional[Message]:
        with self._lock:
            if not self._queue:
                return None
            return self._queue.pop()

    def size(self) -> int:
        with self._lock:
            return len(self._queue)

    def empty(self) -> bool:
        with self._lock:
            return len(self._queue) == 0


class PriorityQueue(BaseQueue[Message]):
    """Priority queue implementation"""

    def __init__(self, maxsize: int = 0):
        self._heap = []
        self._maxsize = maxsize
        self._lock = threading.RLock()

    def put(self, item: Message, timeout: Optional[float] = None) -> bool:
        with self._lock:
            if self._maxsize > 0 and len(self._heap) >= self._maxsize:
                return False
            heapq.heappush(self._heap, item)
            return True

    def get(self, timeout: Optional[float] = None) -> Optional[Message]:
        with self._lock:
            if not self._heap:
                return None
            return heapq.heappop(self._heap)

    def size(self) -> int:
        with self._lock:
            return len(self._heap)

    def empty(self) -> bool:
        with self._lock:
            return len(self._heap) == 0


class DelayQueue(BaseQueue[Message]):
    """Delay queue implementation for scheduled messages"""

    def __init__(self, maxsize: int = 0):
        self._heap = []  # Min heap of (delay_until, message)
        self._maxsize = maxsize
        self._lock = threading.RLock()

    def put(self, item: Message, timeout: Optional[float] = None) -> bool:
        with self._lock:
            if self._maxsize > 0 and len(self._heap) >= self._maxsize:
                return False
            delay_until = item.delay_until or time.time()
            heapq.heappush(self._heap, (delay_until, item))
            return True

    def get(self, timeout: Optional[float] = None) -> Optional[Message]:
        with self._lock:
            now = time.time()
            while self._heap:
                delay_until, message = self._heap[0]
                if delay_until <= now:
                    heapq.heappop(self._heap)
                    return message
                break
            return None

    def size(self) -> int:
        with self._lock:
            return len(self._heap)

    def empty(self) -> bool:
        with self._lock:
            return len(self._heap) == 0


class PersistenceManager:
    """Handles message persistence to disk"""

    def __init__(self, storage_path: str = "./queue_data"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self._lock = threading.Lock()

    def save_message(self, queue_name: str, message: Message) -> bool:
        """Save a message to persistent storage"""
        try:
            with self._lock:
                queue_dir = self.storage_path / queue_name
                queue_dir.mkdir(exist_ok=True)

                message_file = queue_dir / f"{message.id}.pkl"
                with open(message_file, "wb") as f:
                    pickle.dump(message, f)
                return True
        except Exception as e:
            logger.error(f"Failed to save message {message.id}: {e}")
            return False

    def load_message(self, queue_name: str, message_id: str) -> Optional[Message]:
        """Load a message from persistent storage"""
        try:
            with self._lock:
                message_file = self.storage_path / queue_name / f"{message_id}.pkl"
                if not message_file.exists():
                    return None

                with open(message_file, "rb") as f:
                    return pickle.load(f)
        except Exception as e:
            logger.error(f"Failed to load message {message_id}: {e}")
            return None

    def delete_message(self, queue_name: str, message_id: str) -> bool:
        """Delete a message from persistent storage"""
        try:
            with self._lock:
                message_file = self.storage_path / queue_name / f"{message_id}.pkl"
                if message_file.exists():
                    message_file.unlink()
                return True
        except Exception as e:
            logger.error(f"Failed to delete message {message_id}: {e}")
            return False

    def load_all_messages(self, queue_name: str) -> List[Message]:
        """Load all messages for a queue"""
        messages = []
        try:
            with self._lock:
                queue_dir = self.storage_path / queue_name
                if not queue_dir.exists():
                    return messages

                for message_file in queue_dir.glob("*.pkl"):
                    try:
                        with open(message_file, "rb") as f:
                            message = pickle.load(f)
                            messages.append(message)
                    except Exception as e:
                        logger.error(f"Failed to load message from {message_file}: {e}")
        except Exception as e:
            logger.error(f"Failed to load messages for queue {queue_name}: {e}")

        return messages


class MessageQueue:
    """
    Production-ready message queue implementation with multiple queue types,
    persistence, monitoring, and enterprise features.
    """

    def __init__(
        self,
        name: str,
        queue_type: QueueType = QueueType.FIFO,
        maxsize: int = 0,
        enable_persistence: bool = False,
        storage_path: str = "./queue_data",
        enable_dead_letter: bool = True,
        dead_letter_maxsize: int = 1000,
    ):
        self.name = name
        self.queue_type = queue_type
        self.maxsize = maxsize
        self.enable_persistence = enable_persistence
        self.enable_dead_letter = enable_dead_letter

        # Initialize queue based on type
        self._queue = self._create_queue(queue_type, maxsize)
        self._dead_letter_queue = (
            FIFOQueue(dead_letter_maxsize) if enable_dead_letter else None
        )

        # Persistence
        self._persistence = (
            PersistenceManager(storage_path) if enable_persistence else None
        )

        # Metrics and monitoring
        self.metrics = QueueMetrics()
        self._processing_messages: Dict[str, Message] = {}
        self._consumers: Dict[str, ConsumerConfig] = {}
        self._message_handlers: Dict[str, MessageHandler] = {}

        # Threading
        self._lock = threading.RLock()
        self._shutdown_event = threading.Event()
        self._executor = ThreadPoolExecutor(
            max_workers=10, thread_name_prefix=f"mq-{name}"
        )

        # Health monitoring
        self._last_health_check = time.time()
        self._health_status = "healthy"

        # Load persisted messages on startup
        if self.enable_persistence:
            self._load_persisted_messages()

        # Start background tasks
        self._start_background_tasks()

        logger.info(f"MessageQueue '{name}' initialized with type {queue_type.value}")

    def _create_queue(self, queue_type: QueueType, maxsize: int) -> BaseQueue:
        """Create appropriate queue based on type"""
        if queue_type == QueueType.FIFO:
            return FIFOQueue(maxsize)
        elif queue_type == QueueType.LIFO:
            return LIFOQueue(maxsize)
        elif queue_type == QueueType.PRIORITY:
            return PriorityQueue(maxsize)
        elif queue_type == QueueType.DELAY:
            return DelayQueue(maxsize)
        else:
            raise ValueError(f"Unsupported queue type: {queue_type}")

    def _start_background_tasks(self):
        """Start background monitoring and cleanup tasks"""
        self._executor.submit(self._health_monitor)
        self._executor.submit(self._metrics_updater)
        if self.queue_type == QueueType.DELAY:
            self._executor.submit(self._delay_processor)

    def _health_monitor(self):
        """Background health monitoring"""
        while not self._shutdown_event.is_set():
            try:
                with self._lock:
                    # Update queue size metric
                    self.metrics.queue_size = self._queue.size()
                    self.metrics.processing_count = len(self._processing_messages)
                    self.metrics.dead_letter_count = (
                        self._dead_letter_queue.size() if self._dead_letter_queue else 0
                    )

                    # Determine health status
                    if time.time() - self.metrics.last_activity > 300:  # 5 minutes
                        self._health_status = "idle"
                    elif (
                        self.metrics.queue_size > self.maxsize * 0.9
                        and self.maxsize > 0
                    ):
                        self._health_status = "overloaded"
                    else:
                        self._health_status = "healthy"

                time.sleep(10)  # Check every 10 seconds
            except Exception as e:
                logger.error(f"Health monitor error: {e}")

    def _metrics_updater(self):
        """Background metrics calculation"""
        processing_times = deque(maxlen=1000)

        while not self._shutdown_event.is_set():
            try:
                # Calculate average processing time
                if processing_times:
                    self.metrics.avg_processing_time = sum(processing_times) / len(
                        processing_times
                    )

                time.sleep(5)  # Update every 5 seconds
            except Exception as e:
                logger.error(f"Metrics updater error: {e}")

    def _delay_processor(self):
        """Process delayed messages for DelayQueue"""
        while not self._shutdown_event.is_set():
            try:
                # This is handled by the DelayQueue.get() method
                time.sleep(1)
            except Exception as e:
                logger.error(f"Delay processor error: {e}")

    def _load_persisted_messages(self):
        """Load persisted messages on startup"""
        if not self._persistence:
            return

        try:
            messages = self._persistence.load_all_messages(self.name)
            for message in messages:
                if message.status == MessageStatus.PENDING:
                    self._queue.put(message)
                elif message.status == MessageStatus.PROCESSING:
                    # Requeue processing messages
                    message.status = MessageStatus.PENDING
                    message.retry_count += 1
                    self._queue.put(message)

            logger.info(
                f"Loaded {len(messages)} persisted messages for queue '{self.name}'"
            )
        except Exception as e:
            logger.error(f"Failed to load persisted messages: {e}")

    def publish(
        self,
        payload: Any,
        priority: MessagePriority = MessagePriority.NORMAL,
        delay: Optional[float] = None,
        headers: Optional[Dict[str, Any]] = None,
        message_id: Optional[str] = None,
    ) -> str:
        """
        Publish a message to the queue

        Args:
            payload: Message payload
            priority: Message priority
            delay: Delay in seconds before message becomes available
            headers: Additional message headers
            message_id: Custom message ID

        Returns:
            Message ID
        """
        message = Message(
            id=message_id or str(uuid.uuid4()),
            payload=payload,
            priority=priority,
            headers=headers or {},
            delay_until=time.time() + delay if delay else None,
        )

        with self._lock:
            success = self._queue.put(message)
            if not success:
                raise RuntimeError("Queue is full")

            # Persist message
            if self.enable_persistence:
                self._persistence.save_message(self.name, message)

            # Update metrics
            self.metrics.messages_published += 1
            self.metrics.last_activity = time.time()

        logger.debug(f"Published message {message.id} to queue '{self.name}'")
        return message.id

    def consume(
        self, consumer_id: str, timeout: Optional[float] = None, batch_size: int = 1
    ) -> List[Message]:
        """
        Consume messages from the queue

        Args:
            consumer_id: Unique consumer identifier
            timeout: Timeout in seconds
            batch_size: Number of messages to consume

        Returns:
            List of messages
        """
        messages = []

        with self._lock:
            for _ in range(batch_size):
                message = self._queue.get(timeout)
                if not message:
                    break

                # Mark as processing
                message.status = MessageStatus.PROCESSING
                message.consumer_id = consumer_id
                message.processed_at = time.time()
                self._processing_messages[message.id] = message

                # Update persistence
                if self.enable_persistence:
                    self._persistence.save_message(self.name, message)

                messages.append(message)

            # Update metrics
            self.metrics.messages_consumed += len(messages)
            self.metrics.last_activity = time.time()

        logger.debug(f"Consumer {consumer_id} consumed {len(messages)} messages")
        return messages

    def acknowledge(self, message_id: str) -> bool:
        """
        Acknowledge message processing completion

        Args:
            message_id: Message ID to acknowledge

        Returns:
            True if acknowledged successfully
        """
        with self._lock:
            if message_id not in self._processing_messages:
                return False

            message = self._processing_messages.pop(message_id)
            message.status = MessageStatus.COMPLETED

            # Remove from persistence
            if self.enable_persistence:
                self._persistence.delete_message(self.name, message_id)

            self.metrics.last_activity = time.time()

        logger.debug(f"Acknowledged message {message_id}")
        return True

    def nack(self, message_id: str, requeue: bool = True) -> bool:
        """
        Negative acknowledge - message processing failed

        Args:
            message_id: Message ID to nack
            requeue: Whether to requeue the message

        Returns:
            True if nacked successfully
        """
        with self._lock:
            if message_id not in self._processing_messages:
                return False

            message = self._processing_messages.pop(message_id)
            message.retry_count += 1

            if requeue and message.retry_count <= message.max_retries:
                # Requeue for retry
                message.status = MessageStatus.PENDING
                self._queue.put(message)
                self.metrics.messages_retried += 1
            else:
                # Move to dead letter queue or mark as failed
                message.status = MessageStatus.FAILED
                if self._dead_letter_queue:
                    message.status = MessageStatus.DEAD_LETTER
                    self._dead_letter_queue.put(message)

                self.metrics.messages_failed += 1

            # Update persistence
            if self.enable_persistence:
                if message.status in [MessageStatus.FAILED, MessageStatus.DEAD_LETTER]:
                    self._persistence.save_message(f"{self.name}_failed", message)
                else:
                    self._persistence.save_message(self.name, message)

            self.metrics.last_activity = time.time()

        logger.debug(f"Nacked message {message_id}, retry_count: {message.retry_count}")
        return True

    def register_handler(self, consumer_id: str, handler: MessageHandler):
        """Register a message handler for a consumer"""
        self._message_handlers[consumer_id] = handler
        logger.info(f"Registered handler for consumer {consumer_id}")

    async def start_consumer(self, config: ConsumerConfig):
        """Start an async consumer with registered handler"""
        if config.consumer_id not in self._message_handlers:
            raise ValueError(f"No handler registered for consumer {config.consumer_id}")

        handler = self._message_handlers[config.consumer_id]

        logger.info(f"Starting consumer {config.consumer_id}")

        while not self._shutdown_event.is_set():
            try:
                # Consume messages
                messages = self.consume(
                    config.consumer_id,
                    timeout=config.timeout,
                    batch_size=config.batch_size,
                )

                if not messages:
                    await asyncio.sleep(0.1)
                    continue

                # Process messages
                for message in messages:
                    start_time = time.time()
                    try:
                        success = await handler.handle(message)
                        processing_time = time.time() - start_time

                        if success and config.auto_ack:
                            self.acknowledge(message.id)
                        elif not success:
                            await handler.on_failure(
                                message, Exception("Handler returned False")
                            )
                            self.nack(message.id)

                    except Exception as e:
                        processing_time = time.time() - start_time  # noqa: F841
                        logger.error(f"Error processing message {message.id}: {e}")
                        await handler.on_failure(message, e)
                        self.nack(message.id)

            except Exception as e:
                logger.error(f"Consumer {config.consumer_id} error: {e}")
                await asyncio.sleep(1)

    def get_metrics(self) -> Dict[str, Any]:
        """Get current queue metrics"""
        with self._lock:
            return {
                "name": self.name,
                "type": self.queue_type.value,
                "metrics": asdict(self.metrics),
                "health_status": self._health_status,
                "consumers": list(self._consumers.keys()),
                "processing_messages": len(self._processing_messages),
            }

    def get_health(self) -> Dict[str, Any]:
        """Get queue health status"""
        return {
            "name": self.name,
            "status": self._health_status,
            "queue_size": self._queue.size(),
            "processing_count": len(self._processing_messages),
            "last_activity": self.metrics.last_activity,
            "uptime": time.time() - self._last_health_check,
        }

    def purge(self) -> int:
        """Purge all messages from the queue"""
        count = 0
        with self._lock:
            while not self._queue.empty():
                message = self._queue.get()
                if message and self.enable_persistence:
                    self._persistence.delete_message(self.name, message.id)
                count += 1

        logger.info(f"Purged {count} messages from queue '{self.name}'")
        return count

    def shutdown(self, timeout: float = 30.0):
        """Gracefully shutdown the queue"""
        logger.info(f"Shutting down queue '{self.name}'")

        self._shutdown_event.set()

        # Wait for background tasks to complete
        self._executor.shutdown(wait=True, timeout=timeout)

        # Persist any remaining processing messages
        if self.enable_persistence:
            with self._lock:
                for message in self._processing_messages.values():
                    message.status = (
                        MessageStatus.PENDING
                    )  # Will be reprocessed on restart
                    self._persistence.save_message(self.name, message)

        logger.info(f"Queue '{self.name}' shutdown complete")


# Signal handler for graceful shutdown
def signal_handler(signum, frame):
    logger.info("Received shutdown signal")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


if __name__ == "__main__":
    # Example usage
    async def main():
        # Create queue
        queue = MessageQueue(
            name="test_queue",
            queue_type=QueueType.PRIORITY,
            enable_persistence=True,
            enable_dead_letter=True,
        )

        # Publish messages
        queue.publish("Hello World!", priority=MessagePriority.HIGH)
        queue.publish("Low priority message", priority=MessagePriority.LOW)

        # Consume messages
        messages = queue.consume("consumer_1", batch_size=2)
        for message in messages:
            print(f"Consumed: {message.payload}")
            queue.acknowledge(message.id)

        # Get metrics
        metrics = queue.get_metrics()
        print(f"Metrics: {json.dumps(metrics, indent=2, default=str)}")

        # Shutdown
        queue.shutdown()

    asyncio.run(main())
