import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.routes import auth, wallet, transactions, ledger
from app.kafka.producer import close_producer
from app.kafka.consumer import close_consumer
from app.cache.redis_client import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up Distributed Ledger API...")
    yield
    print("Shutting down...")
    await close_producer()
    await close_consumer()
    await close_redis()


app = FastAPI(
    title="Distributed Ledger & Wallet System",
    description="High throughput distributed ledger with ACID compliance",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(auth.router)
app.include_router(wallet.router)
app.include_router(transactions.router)
app.include_router(ledger.router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "distributed-ledger-api"}