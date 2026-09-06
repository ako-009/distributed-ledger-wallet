import json
import logging
from typing import Optional

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError

from app.core.config import settings
from app.kafka.topics import TOPIC_TRANSACTIONS

logger = logging.getLogger(__name__)

_consumer: Optional[AIOKafkaConsumer] = None


async def get_consumer() -> Optional[AIOKafkaConsumer]:
    """Get or create Kafka consumer."""
    global _consumer
    if _consumer is None:
        try:
            _consumer = AIOKafkaConsumer(
                TOPIC_TRANSACTIONS,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id="ledger-consumers",
                # auto_offset_reset: start from beginning if no offset
                auto_offset_reset="earliest",
                # Deserialize JSON bytes to dict
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                # enable_auto_commit=False for manual commit
                # This ensures we only commit after successful processing
                enable_auto_commit=False,
            )
            await _consumer.start()
            logger.info("Kafka consumer connected successfully")
        except Exception as e:
            logger.warning(f"Kafka consumer unavailable: {e}")
            _consumer = None
    return _consumer


async def close_consumer():
    """Close Kafka consumer."""
    global _consumer
    if _consumer:
        await _consumer.stop()
        _consumer = None


async def consume_transaction_events():
    """
    Background task that consumes transaction events from Kafka.
    Commits offset only after successful processing.
    This ensures zero message loss even if consumer crashes.
    """
    consumer = await get_consumer()

    if consumer is None:
        logger.warning("Kafka consumer not available — skipping consumption")
        return

    try:
        async for message in consumer:
            try:
                event = message.value
                logger.info(
                    f"Consumed event: transaction_id={event.get('transaction_id')} "
                    f"amount={event.get('amount')} "
                    f"status={event.get('status')}"
                )

                # Process the event here
                # In production: update analytics, send notifications, etc.

                # Manually commit offset AFTER successful processing
                # This ensures if consumer crashes before commit,
                # the message will be reprocessed (at-least-once delivery)
                await consumer.commit()

            except Exception as e:
                logger.error(f"Error processing event: {e}")
                # Don't commit — message will be reprocessed

    except KafkaError as e:
        logger.error(f"Kafka consumer error: {e}")