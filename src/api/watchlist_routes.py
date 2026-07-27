"""Watchlist API — symbols being considered for purchase, no position."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..db_portfolio import PortfolioWriteError
from ..db_watchlist import (
    WatchlistItemNotFoundError,
    add_to_watchlist,
    get_watchlist,
    remove_from_watchlist,
)
from ..market_data import fetch_current_price
from ..models import AssetClass

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("")
async def list_watchlist():
    """Watchlist with live current prices, fetched concurrently.

    fetch_current_price() is a synchronous, blocking yfinance call — run
    each one in a thread and gather them so N items fetch in parallel
    instead of one slow/rate-limited symbol stalling the rest (the same
    class of bug fixed for the growth endpoint this session).
    """
    items = get_watchlist()

    async def _price(item: dict) -> float | None:
        return await asyncio.to_thread(fetch_current_price, item["symbol"], AssetClass(item["asset_class"]))

    prices = await asyncio.gather(*(_price(item) for item in items))

    return [
        {
            **item,
            "added_at": item["added_at"].isoformat(),
            "current_price": price,
        }
        for item, price in zip(items, prices)
    ]


class AddWatchlistRequest(BaseModel):
    symbol: str
    target_price: float | None = None
    notes: str | None = None
    # Only required when `symbol` is new to the system:
    name: str | None = None
    asset_class: str | None = None
    sector: str | None = None


@router.post("")
async def add_watchlist_item(req: AddWatchlistRequest):
    """Add a symbol to the watchlist. Adding one already on it updates
    target_price/notes instead of erroring."""
    try:
        add_to_watchlist(
            req.symbol,
            name=req.name,
            asset_class=req.asset_class,
            sector=req.sector,
            target_price=req.target_price,
            notes=req.notes,
        )
    except PortfolioWriteError as e:
        raise HTTPException(400, str(e))
    except Exception:
        logger.exception("Failed to add %s to watchlist", req.symbol)
        raise HTTPException(503, "Could not update watchlist — database unavailable")
    return {"status": "ok"}


@router.delete("/{symbol}")
async def delete_watchlist_item(symbol: str):
    try:
        remove_from_watchlist(symbol)
    except WatchlistItemNotFoundError as e:
        raise HTTPException(404, str(e))
    except Exception:
        logger.exception("Failed to remove %s from watchlist", symbol)
        raise HTTPException(503, "Could not update watchlist — database unavailable")
    return {"status": "ok"}
