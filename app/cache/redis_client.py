import json
from decimal import Decimal
from typing import Optional

import redis.asyncio as aioredis

from app.core.config import settings

# Redis client — connects to Redis server
redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """Get Redis connection — creates one if not exists."""
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    return redis_client


async def close_redis():
    """Close Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


# Cache key patterns
def balance_key(wallet_id: str) -> str:
    return f"wallet:{wallet_id}:balance"


def currency_key(wallet_id: str) -> str:
    return f"wallet:{wallet_id}:currency"


# TTL: 5 minutes
BALANCE_TTL = 300


async def get_cached_balance(wallet_id: str) -> Optional[Decimal]:
    """
    Get wallet balance from Redis cache.
    Returns None on cache miss.
    """
    redis = await get_redis()
    cached = await redis.get(balance_key(wallet_id))
    if cached is not None:
        return Decimal(cached)
    return None


async def set_cached_balance(
    wallet_id: str,
    balance: Decimal,
    currency: str = "INR"
) -> None:
    """Store wallet balance in Redis with TTL."""
    redis = await get_redis()
    await redis.set(balance_key(wallet_id), str(balance), ex=BALANCE_TTL)
    await redis.set(currency_key(wallet_id), currency, ex=BALANCE_TTL)


async def invalidate_wallet_cache(wallet_id: str) -> None:
    """
    Delete cached balance for a wallet.
    Called after any write operation (transfer, deposit).
    """
    redis = await get_redis()
    await redis.delete(balance_key(wallet_id))
    await redis.delete(currency_key(wallet_id))