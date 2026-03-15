import argparse
import asyncio
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

ROOT = Path(__file__).resolve().parents[1]
import sys
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.core.settings import settings
from apps.api.app.db.models import Order, Position  # noqa: E402
from apps.api.app.services.binance_client import BinanceFuturesClient  # noqa: E402
from apps.api.app.services.testnet_trading_service import BinanceTestnetTradingService  # noqa: E402


async def backfill(limit: int, dry_run: bool) -> int:
    engine = create_engine(settings.postgres_dsn)
    SessionLocal = sessionmaker(bind=engine)
    client = BinanceFuturesClient()
    helper = BinanceTestnetTradingService(db=None, binance_client=client, execution_enabled=True)

    updated = 0
    with SessionLocal() as db:  # type: Session
        orders = db.execute(
            select(Order)
            .where(Order.is_testnet.is_(True), Order.status.in_(["filled", "partially_filled"]))
            .order_by(Order.id.desc())
            .limit(limit)
        ).scalars().all()

        for order in orders:
            if not order.external_order_id or not str(order.external_order_id).isdigit():
                continue
            trades = await client.get_order_trades(symbol=order.symbol, order_id=int(order.external_order_id))
            fill_price = helper._extract_fill_price_from_trades(trades, fallback=order.price)
            executed_qty = helper._extract_executed_quantity_from_trades(trades, fallback=order.executed_quantity)
            if fill_price <= 0:
                continue

            position = db.execute(
                select(Position)
                .where(Position.trade_plan_id == order.trade_plan_id)
                .order_by(Position.id.desc())
            ).scalars().first()

            position_risk = await client.get_position_risk(order.symbol)
            mark_price = position.mark_price if position else fill_price
            leverage = position.leverage if position else 1
            if isinstance(position_risk, dict):
                live_mark_price = helper._to_float(position_risk.get("markPrice"), fallback=0.0)
                if live_mark_price > 0:
                    mark_price = live_mark_price
                leverage = int(helper._to_float(position_risk.get("leverage"), fallback=float(leverage)) or leverage)

            changed = False
            if round(order.price, 8) != round(fill_price, 8):
                order.price = fill_price
                changed = True
            if round(order.executed_quantity, 8) != round(executed_qty, 8):
                order.executed_quantity = executed_qty
                changed = True

            if position is not None:
                direction = 1 if position.side == "long" else -1
                unrealized_pnl = round((mark_price - fill_price) * position.quantity * direction, 8)
                if round(position.entry_price, 8) != round(fill_price, 8):
                    position.entry_price = fill_price
                    changed = True
                if round(position.mark_price, 8) != round(mark_price, 8):
                    position.mark_price = mark_price
                    changed = True
                if round(position.unrealized_pnl, 8) != round(unrealized_pnl, 8):
                    position.unrealized_pnl = unrealized_pnl
                    changed = True
                if int(position.leverage) != int(leverage):
                    position.leverage = leverage
                    changed = True

            if changed:
                updated += 1
                print(f"updated trade_plan_id={order.trade_plan_id} symbol={order.symbol} fill_price={fill_price} executed_qty={executed_qty}")

        if dry_run:
            db.rollback()
        else:
            db.commit()

    return updated


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill real Binance fill prices for persisted testnet orders/positions")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    updated = asyncio.run(backfill(limit=args.limit, dry_run=args.dry_run))
    print(f"backfill_updates={updated} dry_run={args.dry_run}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
