from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.routes import auth, wallet, transactions, ledger


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up Distributed Ledger API...")
    yield
    print("Shutting down...")


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