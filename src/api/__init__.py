"""API router package."""

from .data_routes import router as data_router
from .research_routes import router as research_router
from .portfolio_routes import router as portfolio_router
from .journal_routes import router as journal_router

__all__ = ["data_router", "research_router", "portfolio_router", "journal_router"]
