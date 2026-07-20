"""FastAPI application — main entry point."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Portfolio Growth Engine",
        description="Research, analyze, and grow your investment portfolio",
        version="0.2.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Register routers ---
    from .api import portfolio_router, research_router, journal_router, data_router
    app.include_router(data_router, prefix="/api/data", tags=["Layer 1 — Data"])
    app.include_router(research_router, prefix="/api/research", tags=["Layer 2 — Research"])
    app.include_router(portfolio_router, prefix="/api/portfolio", tags=["Layer 3 — Portfolio"])
    app.include_router(journal_router, prefix="/api/journal", tags=["Layer 4 — Journal"])

    @app.get("/health")
    async def health():
        return {"status": "ok", "env": settings.app_env}

    return app


app = create_app()
