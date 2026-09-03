from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# The engine is the connection pool to PostgreSQL
# pool_size=20: keep 20 connections open and ready
# max_overflow=0: never exceed 20 connections
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=0,
    echo=False,  # Set True to see SQL queries in terminal (useful for debugging)
)

# Session factory — creates new DB sessions
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit
)


# Base class that all our models will inherit from
class Base(DeclarativeBase):
    pass


# Dependency function — used by FastAPI to give each request its own DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()