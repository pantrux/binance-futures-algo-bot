import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.db.base import Base
from apps.api.app.db.models import TradePlan
from apps.api.app.services.testnet_trading_service import BinanceTestnetTradingService


class FakeBinanceClient:
    async def place_market_order(self, *, symbol: str, side: str, quantity: float, client_order_id: str, recv_window: int = 5000) -> dict:
        assert symbol
        assert side in {"BUY", "SELL"}
        assert quantity > 0
        assert client_order_id
        assert recv_window >= 0
        return {
            "orderId": 987654321,
            "clientOrderId": client_order_id,
            "avgPrice": "50000",
            "executedQty": f"{quantity}",
            "status": "FILLED",
        }


def build_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _seed_trade_plan(db, *, status: str = "approved") -> TradePlan:
    plan = TradePlan(
        symbol="BTCUSDT",
        side="long",
        timeframe="15m",
        market_regime="tendencia_alcista",
        technical_score=80,
        fundamental_score=65,
        sentiment_score=72,
        confidence_score=78,
        aggregate_score=76,
        entry_price=50000,
        stop_loss=49750,
        take_profit=50600,
        capital_usdt=1000,
        applied_risk_pct=1,
        max_position_notional=200,
        thesis="Setup aprobado",
        status=status,
        is_testnet=True,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def test_testnet_trading_executes_approved_trade_plan_when_enabled():
    db = build_db()
    plan = _seed_trade_plan(db, status="approved")
    service = BinanceTestnetTradingService(
        db,
        binance_client=FakeBinanceClient(),
        execution_enabled=True,
    )

    result = asyncio.run(service.execute_trade_plan(plan.id))

    assert result["executed"] is True
    assert result["external_order_id"] == "987654321"

    updated = db.get(TradePlan, plan.id)
    assert updated.status == "testnet_executed"


def test_testnet_trading_blocks_when_disabled():
    db = build_db()
    plan = _seed_trade_plan(db, status="approved")
    service = BinanceTestnetTradingService(
        db,
        binance_client=FakeBinanceClient(),
        execution_enabled=False,
    )

    result = asyncio.run(service.execute_trade_plan(plan.id))

    assert result["executed"] is False
    assert result["reason"] == "testnet_execution_disabled"


def test_testnet_trading_blocks_not_approved_trade_plan():
    db = build_db()
    plan = _seed_trade_plan(db, status="blocked")
    service = BinanceTestnetTradingService(
        db,
        binance_client=FakeBinanceClient(),
        execution_enabled=True,
    )

    result = asyncio.run(service.execute_trade_plan(plan.id))

    assert result["executed"] is False
    assert result["reason"] == "trade_plan_not_approved"
