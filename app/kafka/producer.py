import json
import logging
from typing import Optional
from decimal import Decimal

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

from app.core.config import settings
from app.kafka.topics import TOPIC_TRANSACTIONS

logger = logging.getLogger(__name__)

# Global producer instance
_producer: Optional[AIOKafkaProducer] = None


async def get_producer() -> Optional[AIOKafkaProducer]:
    """Get or create Kafka producer. Returns None if Kafka unavailable."""
    global _producer
    if _producer is None:
        try:
            _producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                acks="all",
                enable_idempotence=True,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
            )
            await _producer.start()
            logger.info("Kafka producer connected successfully")
        except Exception as e:
            logger.warning(f"Kafka unavailable: {e}. Events will be logged locally.")
            _producer = None
    return _producer


async def close_producer():
    """Close Kafka producer connection."""
    global _producer
    if _producer:
        await _producer.stop()
        _producer = None


async def publish_transaction_event(
    transaction_id: str,
    sender_wallet_id: str,
    receiver_wallet_id: str,
    amount: Decimal,
    status: str = "completed"
) -> bool:
    """
    Publish transaction event to Kafka.

    Returns True if published successfully, False if Kafka unavailable.
    Note: Transfer is already committed to DB at this point.
    Kafka failure does NOT rollback the transfer.
    """
    event = {
        "transaction_id": transaction_id,
        "sender_wallet_id": sender_wallet_id,
        "receiver_wallet_id": receiver_wallet_id,
        "amount": str(amount),
        "status": status,
        "event_type": "TRANSFER_COMPLETED"
    }

    producer = await get_producer()

    if producer is None:
        # Kafka unavailable — log locally as fallback
        logger.warning(
            f"KAFKA_FALLBACK: Transaction {transaction_id} "
            f"amount={amount} from {sender_wallet_id} to {receiver_wallet_id}"
        )
        return False

    try:
        # Send with transaction_id as key
        # This ensures events for same transaction go to same partition
        await producer.send_and_wait(
            TOPIC_TRANSACTIONS,
            key=transaction_id,
            value=event
        )
        logger.info(f"Published transaction event: {transaction_id}")
        return True

    except KafkaError as e:
        logger.error(f"Failed to publish to Kafka: {e}")
        # Log locally as fallback
        logger.warning(f"KAFKA_FALLBACK: {event}")
        return False