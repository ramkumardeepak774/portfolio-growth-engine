"""Celery worker for background data collection tasks."""

from __future__ import annotations

import logging

from celery import Celery
from celery.schedules import crontab

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

celery_app = Celery(
    "portfolio_engine",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# --- Scheduled tasks ---
celery_app.conf.beat_schedule = {
    # Collect prices daily at 4 PM IST (after market close)
    "collect-prices-daily": {
        "task": "src.tasks.collect_prices_all",
        "schedule": crontab(hour=16, minute=15),
    },
    # Collect fundamentals weekly on Sunday
    "collect-fundamentals-weekly": {
        "task": "src.tasks.collect_fundamentals_all",
        "schedule": crontab(day_of_week=0, hour=10, minute=0),
    },
    # Collect news every 6 hours
    "collect-news-6h": {
        "task": "src.tasks.collect_news_all",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    # Collect Reddit sentiment daily at 9 PM IST
    "collect-reddit-daily": {
        "task": "src.tasks.collect_reddit_sentiment",
        "schedule": crontab(hour=21, minute=0),
    },
    # Take portfolio snapshot daily at 5 PM IST
    "portfolio-snapshot-daily": {
        "task": "src.tasks.take_portfolio_snapshot",
        "schedule": crontab(hour=17, minute=0),
    },
}
