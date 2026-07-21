"""SQLAlchemy database engine and session management.

Engines are cached (lru_cache) rather than created fresh per call — each
create_engine() sets up its own connection pool, and against a remote/
serverless Postgres (Neon) a fresh connection means a full TCP+SSL
handshake plus possible compute cold-start every time. Reusing one engine
per process lets the pool actually pool.
"""

from __future__ import annotations

from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from ..config import get_settings


class Base(DeclarativeBase):
    pass


# Async engine (for FastAPI)
@lru_cache()
def get_async_engine() -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(settings.database_url, echo=False)


def get_async_session_factory():
    engine = get_async_engine()
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Sync engine (for CLI, Celery, Alembic, and the price cache)
@lru_cache()
def get_sync_engine():
    settings = get_settings()
    return create_engine(settings.database_url_sync, echo=False, pool_pre_ping=True)


def get_sync_session_factory():
    engine = get_sync_engine()
    return sessionmaker(engine, class_=Session, expire_on_commit=False)
