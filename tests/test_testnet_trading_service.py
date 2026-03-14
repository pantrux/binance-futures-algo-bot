import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.db.base import Base
from apps.api.app.db.models import Order, Position, TradePlan
from apps.api.app.services.testnet_trading_service import BinanceTestnetTradingService


class FakeBinanceClient:
    async def get_symbol_step_size(self, symbol: str) -> float:
        assert symbol
        return 0.001

    async def get_symbol_leverage(self, symbol: str, recv_window: int = 5000) -> int:
        assert symbol
        assert recv_window >= 0
        return 10

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


class FakeBinanceClientZeroAvgPrice:
    async def get_symbol_step_size(self, symbol: str) -> float:
        return 0.001

    async def get_symbol_leverage(self, symbol: str, recv_window: int = 5000) -> int:
        return 3

    async def place_market_order(self, *, symbol: str, side: str, quantity: float, client_order_id: str, recv_window: int = 5000) -> dict:
        return {
            "orderId": 123,
            "clientOrderId": client_order_id,
            "avgPrice": "0",
            "executedQty": "0",
            "status": "NEW",
        }


class FakeBinanceClientNewStatusButExecuted:
    async def get_symbol_step_size(self, symbol: str) -> float:
        return 0.001

    async def get_symbol_leverage(self, symbol: str, recv_window: int = 5000) -> int:
        return 5

    async def place_market_order(self, *, symbol: str, side: str, quantity: float, client_order_id: str, recv_window: int = 5000) -> dict:
        return {
            "orderId": 456,
            "clientOrderId": client_order_id,
            "avgPrice": "50010",
            "executedQty": f"{quantity}",
            "status": "NEW",
        }


class FakeBinanceClientMissingCredentials:
    async def get_symbol_step_size(self, symbol: str) -> float:
        return 0.001

    async def get_symbol_leverage(self, symbol: str, recv_window: int = 5000) -> int:
        return 1

    async def place_market_order(self, *, symbol: str, side: str, quantity: float, client_order_id: str, recv_window: int = 5000) -> dict:
        raise RuntimeError("binance_credentials_missing")


class FakeBinanceClientMissingStepSize:
    async def get_symbol_step_size(self, symbol: str) -> float:
        raise RuntimeError("symbol_step_size_not_found:BTCUSDT")

    async def get_symbol_leverage(self, symbol: str, recv_window: int = 5000) -> int:
        return 1

    async def place_market_order(self, *, symbol: str, side: str, quantity: float, client_order_id: str, recv_window: int = 5000) -> dict:
        raise AssertionError("No debería llamar place_market_order cuando falta step size")


def build_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _seed_trade_plan(db, *, status: str = "approved", side: str = "long") -> TradePlan:
    plan = TradePlan(
        symbol="BTCUSDT",
        side=side,
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

    position = db.query(Position).filter(Position.trade_plan_id == plan.id).one()
    assert position.leverage == 10


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


def test_testnet_trading_blocks_invalid_side():
    db = build_db()
    plan = _seed_trade_plan(db, status="approved", side="weird")
    service = BinanceTestnetTradingService(
        db,
        binance_client=FakeBinanceClient(),
        execution_enabled=True,
    )

    result = asyncio.run(service.execute_trade_plan(plan.id))

    assert result["executed"] is False
    assert result["reason"] == "invalid_side"


def test_testnet_trading_falls_back_to_trade_plan_price_when_avg_price_is_zero():
    db = build_db()
    plan = _seed_trade_plan(db, status="approved")
    service = BinanceTestnetTradingService(
        db,
        binance_client=FakeBinanceClientZeroAvgPrice(),
        execution_enabled=True,
    )

    result = asyncio.run(service.execute_trade_plan(plan.id))

    assert result["executed"] is True
    updated = db.get(TradePlan, plan.id)
    assert updated.status == "testnet_executed"

    position = db.query(Position).filter(Position.trade_plan_id == plan.id).one()
    assert position.entry_price == plan.entry_price
    assert position.quantity > 0


def test_testnet_trading_normalizes_new_status_with_executed_qty_as_filled():
    db = build_db()
    plan = _seed_trade_plan(db, status="approved")
    service = BinanceTestnetTradingService(
        db,
        binance_client=FakeBinanceClientNewStatusButExecuted(),
        execution_enabled=True,
    )

    result = asyncio.run(service.execute_trade_plan(plan.id))

    assert result["executed"] is True
    order = db.query(Order).filter(Order.trade_plan_id == plan.id).one()
    assert order.status == "filled"
    assert order.executed_quantity > 0



def test_testnet_trading_returns_explicit_reason_when_credentials_are_missing():
    db = build_db()
    plan = _seed_trade_plan(db, status="approved")
    service = BinanceTestnetTradingService(
        db,
        binance_client=FakeBinanceClientMissingCredentials(),
        execution_enabled=True,
    )

    result = asyncio.run(service.execute_trade_plan(plan.id))

    assert result["executed"] is False
    assert result["reason"] == "testnet_credentials_missing"


def test_testnet_trading_returns_explicit_reason_when_step_size_is_unavailable():
    db = build_db()
    plan = _seed_trade_plan(db, status="approved")
    service = BinanceTestnetTradingService(
        db,
        binance_client=FakeBinanceClientMissingStepSize(),
        execution_enabled=True,
    )

    result = asyncio.run(service.execute_trade_plan(plan.id))

    assert result["executed"] is False
    assert result["reason"] == "symbol_step_size_unavailable"
