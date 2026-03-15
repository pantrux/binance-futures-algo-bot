import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.db.base import Base
from apps.api.app.db.models import Order, Position, RiskEvent, TradePlan
from apps.api.app.services.binance_client import BinanceFuturesClient
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


class FakeBinanceClientRequiresOrderRefresh:
    async def get_symbol_step_size(self, symbol: str) -> float:
        return 0.001

    async def get_symbol_leverage(self, symbol: str, recv_window: int = 5000) -> int:
        return 5

    async def place_market_order(self, *, symbol: str, side: str, quantity: float, client_order_id: str, recv_window: int = 5000) -> dict:
        return {
            "orderId": 999,
            "clientOrderId": client_order_id,
            "avgPrice": "0",
            "executedQty": "0",
            "status": "NEW",
        }

    async def get_order(self, *, symbol: str, order_id: int | None = None, client_order_id: str | None = None, recv_window: int = 5000) -> dict:
        return {
            "orderId": order_id or 999,
            "clientOrderId": client_order_id,
            "avgPrice": "50123.45",
            "executedQty": "0.100",
            "status": "FILLED",
        }


class FakeBinanceClientRefreshWithCumQuote:
    async def get_symbol_step_size(self, symbol: str) -> float:
        return 0.001

    async def get_symbol_leverage(self, symbol: str, recv_window: int = 5000) -> int:
        return 5

    async def place_market_order(self, *, symbol: str, side: str, quantity: float, client_order_id: str, recv_window: int = 5000) -> dict:
        return {
            "orderId": 1001,
            "clientOrderId": client_order_id,
            "avgPrice": "0",
            "price": "0",
            "executedQty": "0",
            "status": "NEW",
        }

    async def get_order(self, *, symbol: str, order_id: int | None = None, client_order_id: str | None = None, recv_window: int = 5000) -> dict:
        return {
            "orderId": order_id or 1001,
            "clientOrderId": client_order_id,
            "avgPrice": "0",
            "price": "0",
            "cumQuote": "5012.345",
            "executedQty": "0.100",
            "status": "FILLED",
        }


class FakeBinanceClientRefreshFails:
    async def get_symbol_step_size(self, symbol: str) -> float:
        return 0.001

    async def get_symbol_leverage(self, symbol: str, recv_window: int = 5000) -> int:
        return 2

    async def place_market_order(self, *, symbol: str, side: str, quantity: float, client_order_id: str, recv_window: int = 5000) -> dict:
        return {
            "orderId": 1002,
            "clientOrderId": client_order_id,
            "avgPrice": "0",
            "executedQty": "0",
            "status": "NEW",
        }

    async def get_order(self, *, symbol: str, order_id: int | None = None, client_order_id: str | None = None, recv_window: int = 5000) -> dict:
        raise RuntimeError("timeout_refresh")


class FakeBinanceClientRefreshDegradesAvgPrice:
    async def get_symbol_step_size(self, symbol: str) -> float:
        return 0.001

    async def get_symbol_leverage(self, symbol: str, recv_window: int = 5000) -> int:
        return 5

    async def place_market_order(self, *, symbol: str, side: str, quantity: float, client_order_id: str, recv_window: int = 5000) -> dict:
        return {
            "orderId": 1003,
            "clientOrderId": client_order_id,
            "avgPrice": "50000",
            "executedQty": "0",
            "status": "NEW",
        }

    async def get_order(self, *, symbol: str, order_id: int | None = None, client_order_id: str | None = None, recv_window: int = 5000) -> dict:
        return {
            "orderId": order_id or 1003,
            "clientOrderId": client_order_id,
            "avgPrice": "0",
            "executedQty": "0.100",
            "status": "FILLED",
        }


class FakeBinanceClientRejectedOrder:
    async def get_symbol_step_size(self, symbol: str) -> float:
        return 0.001

    async def get_symbol_leverage(self, symbol: str, recv_window: int = 5000) -> int:
        return 1

    async def place_market_order(self, *, symbol: str, side: str, quantity: float, client_order_id: str, recv_window: int = 5000) -> dict:
        return {
            "orderId": 789,
            "clientOrderId": client_order_id,
            "avgPrice": "0",
            "executedQty": "0",
            "status": "REJECTED",
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



def test_confirm_exchange_order_refreshes_missing_fill_fields():
    db = build_db()
    service = BinanceTestnetTradingService(
        db,
        binance_client=FakeBinanceClientRequiresOrderRefresh(),
        execution_enabled=True,
    )

    payload = asyncio.run(
        service._confirm_exchange_order(
            trade_plan_id=None,
            symbol="BTCUSDT",
            exchange_order={
                "orderId": 999,
                "clientOrderId": "cid-1",
                "avgPrice": "0",
                "executedQty": "0",
                "status": "NEW",
            },
            client_order_id="cid-1",
        )
    )

    assert payload["status"] == "FILLED"
    assert payload["avgPrice"] == "50123.45"
    assert payload["executedQty"] == "0.100"



def test_testnet_trading_derives_fill_price_from_cum_quote_when_avg_price_is_zero():
    db = build_db()
    service = BinanceTestnetTradingService(
        db,
        binance_client=FakeBinanceClientRefreshWithCumQuote(),
        execution_enabled=True,
    )

    exchange_order = asyncio.run(
        service._confirm_exchange_order(
            trade_plan_id=None,
            symbol="BTCUSDT",
            exchange_order={
                "orderId": 1001,
                "clientOrderId": "cid-2",
                "avgPrice": "0",
                "price": "0",
                "executedQty": "0",
                "status": "NEW",
            },
            client_order_id="cid-2",
        )
    )

    price = service._extract_fill_price(exchange_order, fallback=12345.0)

    assert round(price, 3) == 50123.45


def test_confirm_exchange_order_does_not_degrade_existing_avg_price_with_zero_from_refresh():
    db = build_db()
    service = BinanceTestnetTradingService(
        db,
        binance_client=FakeBinanceClientRefreshDegradesAvgPrice(),
        execution_enabled=True,
    )

    payload = asyncio.run(
        service._confirm_exchange_order(
            trade_plan_id=None,
            symbol="BTCUSDT",
            exchange_order={
                "orderId": 1003,
                "clientOrderId": "cid-3",
                "avgPrice": "50000",
                "executedQty": "0",
                "status": "NEW",
            },
            client_order_id="cid-3",
        )
    )

    assert payload["avgPrice"] == "50000"
    assert payload["executedQty"] == "0.100"



def test_prefer_refresh_value_does_not_swap_unknown_status_with_other_unknown_status():
    db = build_db()
    service = BinanceTestnetTradingService(
        db,
        binance_client=FakeBinanceClient(),
        execution_enabled=True,
    )

    should_replace = service._prefer_refresh_value("status", "PENDING_CANCEL", "SOME_FUTURE_STATUS")

    assert should_replace is False



def test_get_order_requires_at_least_one_exchange_identifier():
    client = BinanceFuturesClient()
    client.api_key = "test-key"
    client.api_secret = "test-secret"

    try:
        asyncio.run(client.get_order(symbol="BTCUSDT", order_id=None, client_order_id=None))
        raise AssertionError("Se esperaba ValueError cuando faltan order_id y client_order_id")
    except ValueError as exc:
        assert "get_order requiere" in str(exc)



def test_testnet_trading_persists_refreshed_fill_price_and_status_end_to_end():
    db = build_db()
    plan = _seed_trade_plan(db, status="approved")
    service = BinanceTestnetTradingService(
        db,
        binance_client=FakeBinanceClientRequiresOrderRefresh(),
        execution_enabled=True,
    )

    result = asyncio.run(service.execute_trade_plan(plan.id))

    assert result["executed"] is True
    order = db.query(Order).filter(Order.trade_plan_id == plan.id).one()
    position = db.query(Position).filter(Position.trade_plan_id == plan.id).one()
    assert order.status == "filled"
    assert order.price == 50123.45
    assert order.executed_quantity == 0.1
    assert position.entry_price == 50123.45
    assert position.quantity == 0.1



def test_testnet_trading_logs_warning_when_order_refresh_fails_and_falls_back_to_plan_price():
    db = build_db()
    plan = _seed_trade_plan(db, status="approved")
    service = BinanceTestnetTradingService(
        db,
        binance_client=FakeBinanceClientRefreshFails(),
        execution_enabled=True,
    )

    result = asyncio.run(service.execute_trade_plan(plan.id))

    assert result["executed"] is True
    order = db.query(Order).filter(Order.trade_plan_id == plan.id).one()
    position = db.query(Position).filter(Position.trade_plan_id == plan.id).one()
    warning = (
        db.query(RiskEvent)
        .filter(RiskEvent.trade_plan_id == plan.id, RiskEvent.event_type == "testnet_order_refresh_failed")
        .one()
    )
    assert order.price == plan.entry_price
    assert position.entry_price == plan.entry_price
    assert warning.severity == "warning"
    assert "timeout_refresh" in warning.message



def test_testnet_trading_preserves_rejected_status_without_reclassifying_as_fill():
    db = build_db()
    plan = _seed_trade_plan(db, status="approved")
    service = BinanceTestnetTradingService(
        db,
        binance_client=FakeBinanceClientRejectedOrder(),
        execution_enabled=True,
    )

    result = asyncio.run(service.execute_trade_plan(plan.id))

    assert result["executed"] is True
    order = db.query(Order).filter(Order.trade_plan_id == plan.id).one()
    assert order.status == "rejected"
    assert order.executed_quantity == 0



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
