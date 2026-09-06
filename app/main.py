from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.api.routes import auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs on startup and shutdown."""
    print("Starting up Distributed Ledger API...")
    yield
    print("Shutting down...")


app = FastAPI(
    title="Distributed Ledger & Wallet System",
    description="High throughput distributed ledger with ACID compliance",
    version="1.0.0",
    lifespan=lifespan
)

# Register routers
app.include_router(auth.router)


@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "distributed-ledger-api"}