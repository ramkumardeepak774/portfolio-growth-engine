"""One-time migration: seed Postgres (Stock/Position/Transaction) from data/portfolio.yaml.

Run once after deploying the DB-backed portfolio storage:
    uv run python scripts/seed_portfolio_from_yaml.py

Safe to re-run — skips any holding that already has a Position in the DB,
so it won't create duplicate transactions.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.db.engine import get_sync_session_factory  # noqa: E402
from src.db.models import AssetClassEnum, Position, Stock  # noqa: E402
from src.db.models import Transaction as DBTransaction  # noqa: E402
from src.db.models import TxnType  # noqa: E402
from src.portfolio import load_portfolio  # noqa: E402


def main() -> None:
    portfolio = load_portfolio()
    if not portfolio.holdings:
        print("data/portfolio.yaml has no holdings — nothing to seed.")
        return

    session_factory = get_sync_session_factory()
    created, skipped = 0, 0

    with session_factory() as session:
        for holding in portfolio.holdings:
            existing_stock = session.query(Stock).filter_by(symbol=holding.symbol).one_or_none()
            if existing_stock is not None:
                existing_position = session.query(Position).filter_by(stock_id=existing_stock.id).one_or_none()
                if existing_position is not None:
                    print(f"skip {holding.symbol} — already in DB")
                    skipped += 1
                    continue

            stock = existing_stock or Stock(
                symbol=holding.symbol,
                name=holding.name,
                asset_class=AssetClassEnum(holding.asset_class.value),
                sector=holding.sector,
            )
            if existing_stock is None:
                session.add(stock)
                session.flush()

            position = Position(
                stock_id=stock.id,
                current_price=holding.current_price,
                notes=holding.notes,
                is_active=True,
            )
            session.add(position)
            session.flush()

            for t in holding.transactions:
                session.add(
                    DBTransaction(
                        position_id=position.id,
                        txn_type=TxnType(t.type.value),
                        date=t.date,
                        quantity=t.quantity,
                        price=t.price,
                        charges=t.charges,
                        amount=t.amount,
                    )
                )

            print(f"seeded {holding.symbol} — {len(holding.transactions)} transaction(s)")
            created += 1

        session.commit()

    print(f"\nDone. {created} holding(s) seeded, {skipped} already present.")


if __name__ == "__main__":
    main()
