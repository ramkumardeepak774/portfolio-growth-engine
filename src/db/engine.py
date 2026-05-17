"""SQLAlchemy database engine and session management."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    pass


# Async engine (for FastAPI)
def get_async_engine():
    settings = get_settings()
    return create_async_engine(settings.database_url, echo=False)


def get_async_session_factory():
    engine = get_async_engine()
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Sync engine (for CLI, Celery, Alembic)
def get_sync_engine():
    settings = get_settings()
    return create_engine(settings.database_url_sync, echo=False)


def get_sync_session_factory():
    engine = get_sync_engine()
    return sessionmaker(engine, class_=Session, expire_on_commit=False)
