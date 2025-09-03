"""
Message Queue System - Comprehensive Test Suite

Tests covering all functionality including queue types, persistence,
monitoring, error handling, and performance benchmarks.

Author: Backend Infrastructure Toolkit
Version: 1.0.0
"""

import asyncio
import concurrent.futures
import shutil

# Import the message queue components
import sys
import tempfile
import time
from pathlib import Path
from typing import List

import pytest

sys.path.append(".")

from message_queue import (
    ConsumerConfig,
    DelayQueue,
    FIFOQueue,
    LIFOQueue,
    Message,
    MessageHandler,
    MessagePriority,
    MessageQueue,
    MessageStatus,
    PersistenceManager,
    PriorityQueue,
    QueueType,
)


class TestMessageHandler(MessageHandler):
    """Test message handler implementation"""

    def __init__(self, should_succeed: bool = True, processing_delay: float = 0.0):
        self.should_succeed = should_succeed
        self.processing_delay = processing_delay
        self.processed_messages = []
        self.failed_messages = []

    async def handle(self, message: Message) -> bool:
        if self.processing_delay > 0:
            await asyncio.sleep(self.processing_delay)

        self.processed_messages.append(message)
        return self.should_succeed

    async def on_failure(self, message: Message, error: Exception) -> None:
        self.failed_messages.append((message, error))


class TestMessage:
    """Test Message class functionality"""

    def test_message_creation(self):
        message = Message(payload="test payload")
        assert message.payload == "test payload"
        assert message.priority == MessagePriority.NORMAL
        assert message.status == MessageStatus.PENDING
        assert message.retry_count == 0
        assert message.id is not None
        assert message.created_at > 0

    def test_message_with_custom_fields(self):
        message = Message(
            id="custom_id",
            payload={"key": "value"},
            priority=MessagePriority.HIGH,
            max_retries=5,
            headers={"source": "test"},
        )
        assert message.id == "custom_id"
        assert message.payload == {"key": "value"}
        assert message.priority == MessagePriority.HIGH
        assert message.max_retries == 5
        assert message.headers == {"source": "test"}

    def test_message_comparison_for_priority(self):
        """Test message comparison for priority queue"""
        high_msg = Message(payload="high", priority=MessagePriority.HIGH)
        normal_msg = Message(payload="normal", priority=MessagePriority.NORMAL)

        # Higher priority should come first (less than)
        assert high_msg < normal_msg

        # Same priority, older message should come first
        time.sleep(0.001)  # Ensure different timestamps
        newer_high_msg = Message(payload="newer_high", priority=MessagePriority.HIGH)
        assert high_msg < newer_high_msg


class TestQueueImplementations:
    """Test different queue type implementations"""

    def test_fifo_queue(self):
        queue = FIFOQueue(maxsize=3)

        # Test basic operations
        msg1 = Message(payload="first")
        msg2 = Message(payload="second")
        msg3 = Message(payload="third")

        assert queue.put(msg1)
        assert queue.put(msg2)
        assert queue.put(msg3)
        assert queue.size() == 3

        # Test maxsize limit
        msg4 = Message(payload="fourth")
        assert not queue.put(msg4)

        # Test FIFO order
        assert queue.get().payload == "first"
        assert queue.get().payload == "second"
        assert queue.get().payload == "third"
        assert queue.get() is None
        assert queue.empty()

    def test_lifo_queue(self):
        queue = LIFOQueue(maxsize=3)

        msg1 = Message(payload="first")
        msg2 = Message(payload="second")
        msg3 = Message(payload="third")

        queue.put(msg1)
        queue.put(msg2)
        queue.put(msg3)

        # Test LIFO order
        assert queue.get().payload == "third"
        assert queue.get().payload == "second"
        assert queue.get().payload == "first"

    def test_priority_queue(self):
        queue = PriorityQueue()

        normal_msg = Message(payload="normal", priority=MessagePriority.NORMAL)
        high_msg = Message(payload="high", priority=MessagePriority.HIGH)
        urgent_msg = Message(payload="urgent", priority=MessagePriority.URGENT)
        low_msg = Message(payload="low", priority=MessagePriority.LOW)

        # Add in random order
        queue.put(normal_msg)
        queue.put(low_msg)
        queue.put(urgent_msg)
        queue.put(high_msg)

        # Should get in priority order
        assert queue.get().payload == "urgent"
        assert queue.get().payload == "high"
        assert queue.get().payload == "normal"
        assert queue.get().payload == "low"

    def test_delay_queue(self):
        queue = DelayQueue()

        now = time.time()
        immediate_msg = Message(payload="immediate", delay_until=now)
        delayed_msg = Message(payload="delayed", delay_until=now + 0.1)

        queue.put(delayed_msg)
        queue.put(immediate_msg)

        # Should get immediate message first
        msg = queue.get()
        assert msg is not None
        assert msg.payload == "immediate"

        # Delayed message not yet available
        assert queue.get() is None

        # Wait and try again
        time.sleep(0.15)
        msg = queue.get()
        assert msg is not None
        assert msg.payload == "delayed"


class TestPersistenceManager:
    """Test persistence functionality"""

    def test_save_and_load_message(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            persistence = PersistenceManager(temp_dir)

            message = Message(payload="test message", priority=MessagePriority.HIGH)

            # Save message
            assert persistence.save_message("test_queue", message)

            # Load message
            loaded_message = persistence.load_message("test_queue", message.id)
            assert loaded_message is not None
            assert loaded_message.id == message.id
            assert loaded_message.payload == message.payload
            assert loaded_message.priority == message.priority

    def test_delete_message(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            persistence = PersistenceManager(temp_dir)

            message = Message(payload="test message")

            # Save and then delete
            persistence.save_message("test_queue", message)
            assert persistence.delete_message("test_queue", message.id)

            # Message should no longer exist
            loaded_message = persistence.load_message("test_queue", message.id)
            assert loaded_message is None

    def test_load_all_messages(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            persistence = PersistenceManager(temp_dir)

            messages = [Message(payload=f"message_{i}") for i in range(5)]

            # Save all messages
            for msg in messages:
                persistence.save_message("test_queue", msg)

            # Load all messages
            loaded_messages = persistence.load_all_messages("test_queue")
            assert len(loaded_messages) == 5

            loaded_payloads = {msg.payload for msg in loaded_messages}
            expected_payloads = {f"message_{i}" for i in range(5)}
            assert loaded_payloads == expected_payloads


class TestMessageQueue:
    """Test MessageQueue main functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Cleanup after each test"""
        if hasattr(self, "temp_dir") and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_queue_creation(self):
        queue = MessageQueue("test_queue", queue_type=QueueType.FIFO)
        assert queue.name == "test_queue"
        assert queue.queue_type == QueueType.FIFO
        queue.shutdown()

    def test_publish_and_consume(self):
        queue = MessageQueue("test_queue")

        # Publish message
        message_id = queue.publish("Hello World!")
        assert message_id is not None

        # Consume message
        messages = queue.consume("consumer_1")
        assert len(messages) == 1
        assert messages[0].payload == "Hello World!"
        assert messages[0].id == message_id

        # Acknowledge message
        assert queue.acknowledge(message_id)

        queue.shutdown()

    def test_batch_consume(self):
        queue = MessageQueue("test_queue")

        # Publish multiple messages
        message_ids = []
        for i in range(5):
            msg_id = queue.publish(f"Message {i}")
            message_ids.append(msg_id)

        # Consume in batch
        messages = queue.consume("consumer_1", batch_size=3)
        assert len(messages) == 3

        # Consume remaining
        messages = queue.consume("consumer_1", batch_size=5)
        assert len(messages) == 2

        queue.shutdown()

    def test_message_retry_logic(self):
        queue = MessageQueue("test_queue", enable_dead_letter=True)

        # Publish message
        message_id = queue.publish("test message")

        # Consume and nack multiple times
        messages = queue.consume("consumer_1")
        message = messages[0]  # noqa: F841

        # Nack with requeue (should retry)
        assert queue.nack(message_id, requeue=True)

        # Consume again
        messages = queue.consume("consumer_1")
        assert len(messages) == 1
        assert messages[0].retry_count == 1

        queue.shutdown()

    def test_dead_letter_queue(self):
        queue = MessageQueue("test_queue", enable_dead_letter=True)

        # Publish message with low max_retries
        message_id = queue.publish("test message")

        # Consume and modify max_retries for testing
        messages = queue.consume("consumer_1")
        message = messages[0]
        message.max_retries = 1
        queue._processing_messages[message_id] = message

        # Exceed retry limit
        queue.nack(message_id, requeue=True)  # retry_count = 1

        messages = queue.consume("consumer_1")
        if messages:
            queue.nack(
                messages[0].id, requeue=True
            )  # retry_count = 2, should go to DLQ

        # Check dead letter queue
        assert queue._dead_letter_queue.size() >= 1

        queue.shutdown()

    def test_priority_queue_ordering(self):
        queue = MessageQueue("test_queue", queue_type=QueueType.PRIORITY)

        # Publish messages with different priorities
        queue.publish("low", priority=MessagePriority.LOW)
        queue.publish("normal", priority=MessagePriority.NORMAL)
        queue.publish("high", priority=MessagePriority.HIGH)
        queue.publish("urgent", priority=MessagePriority.URGENT)

        # Consume in priority order
        messages = queue.consume("consumer_1", batch_size=4)
        payloads = [msg.payload for msg in messages]

        assert payloads == ["urgent", "high", "normal", "low"]

        queue.shutdown()

    def test_delayed_messages(self):
        queue = MessageQueue("test_queue", queue_type=QueueType.DELAY)

        # Publish immediate and delayed messages
        queue.publish("immediate")
        queue.publish("delayed", delay=0.1)

        # Should only get immediate message
        messages = queue.consume("consumer_1", batch_size=2)
        assert len(messages) == 1
        assert messages[0].payload == "immediate"

        # Wait and consume delayed message
        time.sleep(0.15)
        messages = queue.consume("consumer_1")
        assert len(messages) == 1
        assert messages[0].payload == "delayed"

        queue.shutdown()

    def test_persistence(self):
        # Create queue with persistence
        queue1 = MessageQueue(
            "persistent_queue", enable_persistence=True, storage_path=self.temp_dir
        )

        # Publish messages
        message_ids = []
        for i in range(3):
            msg_id = queue1.publish(f"Message {i}")
            message_ids.append(msg_id)

        queue1.shutdown()

        # Create new queue instance (simulating restart)
        queue2 = MessageQueue(
            "persistent_queue", enable_persistence=True, storage_path=self.temp_dir
        )

        # Should have loaded persisted messages
        messages = queue2.consume("consumer_1", batch_size=5)
        assert len(messages) == 3

        payloads = {msg.payload for msg in messages}
        expected_payloads = {f"Message {i}" for i in range(3)}
        assert payloads == expected_payloads

        queue2.shutdown()

    def test_metrics_tracking(self):
        queue = MessageQueue("test_queue")

        # Initial metrics
        metrics = queue.get_metrics()
        assert metrics["metrics"]["messages_published"] == 0
        assert metrics["metrics"]["messages_consumed"] == 0

        # Publish and consume
        queue.publish("test message")
        messages = queue.consume("consumer_1")
        queue.acknowledge(messages[0].id)

        # Check updated metrics
        metrics = queue.get_metrics()
        assert metrics["metrics"]["messages_published"] == 1
        assert metrics["metrics"]["messages_consumed"] == 1

        queue.shutdown()

    def test_health_check(self):
        queue = MessageQueue("test_queue")

        health = queue.get_health()
        assert health["name"] == "test_queue"
        assert health["status"] == "healthy"
        assert health["queue_size"] == 0

        queue.shutdown()

    @pytest.mark.asyncio
    async def test_async_consumer(self):
        queue = MessageQueue("test_queue")
        handler = TestMessageHandler(should_succeed=True)

        # Register handler
        queue.register_handler("async_consumer", handler)

        # Publish messages
        for i in range(3):
            queue.publish(f"Message {i}")

        # Start consumer
        config = ConsumerConfig(consumer_id="async_consumer", batch_size=1, timeout=1.0)

        # Run consumer for a short time
        consumer_task = asyncio.create_task(queue.start_consumer(config))
        await asyncio.sleep(0.5)  # Let it process some messages
        consumer_task.cancel()

        try:
            await consumer_task
        except asyncio.CancelledError:
            pass

        # Check processed messages
        assert len(handler.processed_messages) > 0

        queue.shutdown()

    def test_concurrent_access(self):
        queue = MessageQueue("test_queue", maxsize=1000)

        def producer(producer_id: str, count: int):
            for i in range(count):
                queue.publish(f"Producer {producer_id} - Message {i}")

        def consumer(consumer_id: str, count: int) -> List[str]:
            consumed = []
            for _ in range(count):
                messages = queue.consume(consumer_id)
                for msg in messages:
                    consumed.append(msg.payload)
                    queue.acknowledge(msg.id)
            return consumed

        # Start multiple producers and consumers
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Start producers
            producer_futures = []
            for i in range(3):
                future = executor.submit(producer, f"producer_{i}", 10)
                producer_futures.append(future)

            # Wait for producers to finish
            for future in concurrent.futures.as_completed(producer_futures):
                future.result()

            # Start consumers
            consumer_futures = []
            for i in range(2):
                future = executor.submit(consumer, f"consumer_{i}", 15)
                consumer_futures.append(future)

            # Collect results
            all_consumed = []
            for future in concurrent.futures.as_completed(consumer_futures):
                consumed = future.result()
                all_consumed.extend(consumed)

        # Verify all messages were consumed
        assert len(all_consumed) == 30  # 3 producers * 10 messages each

        queue.shutdown()

    def test_queue_purge(self):
        queue = MessageQueue("test_queue")

        # Publish messages
        for i in range(5):
            queue.publish(f"Message {i}")

        assert queue._queue.size() == 5

        # Purge queue
        purged_count = queue.purge()
        assert purged_count == 5
        assert queue._queue.size() == 0

        queue.shutdown()


class TestPerformance:
    """Performance and load testing"""

    def test_high_throughput_publishing(self):
        queue = MessageQueue("perf_test", maxsize=10000)

        start_time = time.time()
        message_count = 1000

        # Publish many messages
        for i in range(message_count):
            queue.publish(f"Message {i}")

        end_time = time.time()
        throughput = message_count / (end_time - start_time)

        print(f"Publishing throughput: {throughput:.2f} messages/second")
        assert throughput > 100  # Should handle at least 100 msg/s

        queue.shutdown()

    def test_high_throughput_consuming(self):
        queue = MessageQueue("perf_test", maxsize=10000)

        message_count = 1000

        # Publish messages
        for i in range(message_count):
            queue.publish(f"Message {i}")

        start_time = time.time()

        # Consume all messages
        consumed_count = 0
        while consumed_count < message_count:
            messages = queue.consume("perf_consumer", batch_size=50)
            for msg in messages:
                queue.acknowledge(msg.id)
            consumed_count += len(messages)

        end_time = time.time()
        throughput = message_count / (end_time - start_time)

        print(f"Consuming throughput: {throughput:.2f} messages/second")
        assert throughput > 100  # Should handle at least 100 msg/s

        queue.shutdown()

    def test_memory_usage_large_queue(self):
        """Test memory efficiency with large number of messages"""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        queue = MessageQueue("memory_test", maxsize=50000)

        # Add many small messages
        for i in range(10000):
            queue.publish(f"Small message {i}")

        current_memory = process.memory_info().rss
        memory_increase = current_memory - initial_memory

        # Memory increase should be reasonable (less than 100MB for 10k small messages)
        assert memory_increase < 100 * 1024 * 1024

        queue.shutdown()


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_queue_full_behavior(self):
        queue = MessageQueue("test_queue", maxsize=2)

        # Fill queue to capacity
        queue.publish("Message 1")
        queue.publish("Message 2")

        # Next publish should raise an exception
        with pytest.raises(RuntimeError, match="Queue is full"):
            queue.publish("Message 3")

        queue.shutdown()

    def test_acknowledge_nonexistent_message(self):
        queue = MessageQueue("test_queue")

        # Try to acknowledge non-existent message
        result = queue.acknowledge("nonexistent_id")
        assert result is False

        queue.shutdown()

    def test_nack_nonexistent_message(self):
        queue = MessageQueue("test_queue")

        # Try to nack non-existent message
        result = queue.nack("nonexistent_id")
        assert result is False

        queue.shutdown()

    @pytest.mark.asyncio
    async def test_handler_exception_handling(self):
        queue = MessageQueue("test_queue")

        # Handler that always raises an exception
        class FailingHandler(MessageHandler):
            async def handle(self, message: Message) -> bool:
                raise ValueError("Simulated processing error")

            async def on_failure(self, message: Message, error: Exception) -> None:
                self.last_error = error

        handler = FailingHandler()
        queue.register_handler("failing_consumer", handler)

        # Publish message
        queue.publish("test message")

        # Start consumer
        config = ConsumerConfig(consumer_id="failing_consumer", timeout=0.1)

        consumer_task = asyncio.create_task(queue.start_consumer(config))
        await asyncio.sleep(0.2)  # Let it process the message
        consumer_task.cancel()

        try:
            await consumer_task
        except asyncio.CancelledError:
            pass

        # Check that error was handled
        assert hasattr(handler, "last_error")
        assert isinstance(handler.last_error, ValueError)

        queue.shutdown()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
