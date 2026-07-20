"""API router package."""

from .auth_routes import router as auth_router
from .data_routes import router as data_router
from .research_routes import router as research_router
from .portfolio_routes import router as portfolio_router
from .journal_routes import router as journal_router

__all__ = ["auth_router", "data_router", "research_router", "portfolio_router", "journal_router"]
