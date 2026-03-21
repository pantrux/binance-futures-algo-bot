import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.db.base import Base
from apps.api.app.db.models import Order, Position, RiskEvent, TradePlan
from apps.api.app.services.testnet_trading_service import BinanceTestnetTradingService


class FakeBinanceClientExitTriggered:
    async def get_order(self, *, symbol: str, order_id: int | None = None, client_order_id: str | None = None, recv_window: int = 5000) -> dict:
        if order_id == 111111 or client_order_id == "sl-1":
            return {"orderId": order_id, "clientOrderId": client_order_id, "status": "FILLED"}
        return {"orderId": order_id, "clientOrderId": client_order_id, "status": "NEW"}

    async def cancel_order(self, *, symbol: str, order_id: int | None = None, client_order_id: str | None = None, recv_window: int = 5000) -> dict:
        return {"orderId": order_id, "origClientOrderId": client_order_id, "status": "CANCELED"}


class FakeBinanceClientCancelFails(FakeBinanceClientExitTriggered):
    async def cancel_order(self, *, symbol: str, order_id: int | None = None, client_order_id: str | None = None, recv_window: int = 5000) -> dict:
        raise RuntimeError("cancel_failed")


class FakeBinanceClientNoExitTriggered(FakeBinanceClientExitTriggered):
    async def get_order(self, *, symbol: str, order_id: int | None = None, client_order_id: str | None = None, recv_window: int = 5000) -> dict:
        return {"orderId": order_id, "clientOrderId": client_order_id, "status": "NEW"}


class FakeBinanceClientRefreshFails(FakeBinanceClientExitTriggered):
    async def get_order(self, *, symbol: str, order_id: int | None = None, client_order_id: str | None = None, recv_window: int = 5000) -> dict:
        raise RuntimeError("refresh_failed")


class FakeBinanceClientNoCancel(FakeBinanceClientExitTriggered):
    cancel_order = None


class FakeBinanceClientSyncGenericFails(FakeBinanceClientExitTriggered):
    async def get_order(self, *, symbol: str, order_id: int | None = None, client_order_id: str | None = None, recv_window: int = 5000) -> dict:
        raise RuntimeError("generic_sync_failure")


class FakeBinanceClientLocalExit:
    async def get_position_risk(self, symbol: str, recv_window: int = 5000) -> dict:
        return {"symbol": symbol, "markPrice": "49700", "leverage": "10"}

    async def close_position_market(self, *, symbol: str, side: str, quantity: float, client_order_id: str, recv_window: int = 5000) -> dict:
        assert symbol == "BTCUSDT"
        assert side == "SELL"
        assert quantity == 0.1
        return {
            "orderId": 333333,
            "clientOrderId": client_order_id,
            "avgPrice": "49695",
            "executedQty": "0.1",
            "status": "FILLED",
        }

    async def get_order(self, *, symbol: str, order_id: int | None = None, client_order_id: str | None = None, recv_window: int = 5000) -> dict:
        return {
            "orderId": order_id,
            "clientOrderId": client_order_id,
            "avgPrice": "49695",
            "executedQty": "0.1",
            "status": "FILLED",
        }


class FakeBinanceClientLocalExitAck(FakeBinanceClientLocalExit):
    async def close_position_market(self, *, symbol: str, side: str, quantity: float, client_order_id: str, recv_window: int = 5000) -> dict:
        return {
            "orderId": 444444,
            "clientOrderId": client_order_id,
            "avgPrice": "0",
            "executedQty": "0",
            "status": "NEW",
        }

    async def get_order(self, *, symbol: str, order_id: int | None = None, client_order_id: str | None = None, recv_window: int = 5000) -> dict:
        return {
            "orderId": order_id,
            "clientOrderId": client_order_id,
            "avgPrice": "0",
            "executedQty": "0",
            "status": "NEW",
        }


class FakeBinanceClientLocalExitSaferLevel(FakeBinanceClientLocalExit):
    async def get_position_risk(self, symbol: str, recv_window: int = 5000) -> dict:
        return {"symbol": symbol, "markPrice": "49740", "leverage": "10"}


def build_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def seed_trade_plan_with_open_position(db):
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
        status="testnet_executed",
        is_testnet=True,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    db.add_all(
        [
            Position(
                trade_plan_id=plan.id,
                symbol=plan.symbol,
                side=plan.side,
                quantity=0.1,
                entry_price=50000,
                mark_price=50010,
                unrealized_pnl=1.0,
                leverage=10,
                status="open",
                is_testnet=True,
            ),
            Order(
                trade_plan_id=plan.id,
                venue="binance_futures_testnet",
                external_order_id="111111",
                symbol=plan.symbol,
                side=plan.side,
                order_type="stop_market",
                status="new",
                price=49750,
                quantity=0.0,
                executed_quantity=0.0,
                is_testnet=True,
            ),
            Order(
                trade_plan_id=plan.id,
                venue="binance_futures_testnet",
                external_order_id="222222",
                symbol=plan.symbol,
                side=plan.side,
                order_type="take_profit_market",
                status="new",
                price=50600,
                quantity=0.0,
                executed_quantity=0.0,
                is_testnet=True,
            ),
        ]
    )
    db.commit()
    return plan


def test_sync_exit_orders_closes_position_and_cancels_sibling():
    db = build_db()
    plan = seed_trade_plan_with_open_position(db)
    service = BinanceTestnetTradingService(db, binance_client=FakeBinanceClientExitTriggered(), execution_enabled=True)

    result = asyncio.run(service.sync_exit_orders(plan.id))

    assert result["synced"] is True
    assert result["triggered_order_type"] == "stop_market"
    assert result["canceled_sibling_order_id"] == "222222"

    position = db.query(Position).filter(Position.trade_plan_id == plan.id).one()
    refreshed_plan = db.get(TradePlan, plan.id)
    orders = db.query(Order).filter(Order.trade_plan_id == plan.id).order_by(Order.id.asc()).all()
    assert position.status == "closed"
    assert refreshed_plan.status == "testnet_closed"
    assert orders[0].status == "filled"
    assert orders[1].status == "canceled"


def test_sync_exit_orders_returns_without_changes_when_no_exit_triggered():
    db = build_db()
    plan = seed_trade_plan_with_open_position(db)
    service = BinanceTestnetTradingService(db, binance_client=FakeBinanceClientNoExitTriggered(), execution_enabled=True)

    result = asyncio.run(service.sync_exit_orders(plan.id))

    assert result == {"synced": True, "reason": "no_triggered_exit"}
    position = db.query(Position).filter(Position.trade_plan_id == plan.id).one()
    assert position.status == "open"


def test_sync_exit_orders_closes_position_with_local_synthetic_exit_when_native_protection_is_missing():
    db = build_db()
    plan = seed_trade_plan_with_open_position(db)
    db.query(Order).filter(Order.trade_plan_id == plan.id).delete()
    db.commit()
    service = BinanceTestnetTradingService(db, binance_client=FakeBinanceClientLocalExit(), execution_enabled=True)

    result = asyncio.run(service.sync_exit_orders(plan.id))

    assert result["synced"] is True
    assert result["local_exit"] is True
    assert result["triggered_order_type"] == "stop_market"

    position = db.query(Position).filter(Position.trade_plan_id == plan.id).one()
    refreshed_plan = db.get(TradePlan, plan.id)
    local_exit_order = db.query(Order).filter(Order.trade_plan_id == plan.id).one()
    assert position.status == "closed"
    assert refreshed_plan.status == "testnet_closed"
    assert local_exit_order.status == "filled"
    assert local_exit_order.order_type == "stop_market"

    warning = (
        db.query(RiskEvent)
        .filter(RiskEvent.trade_plan_id == plan.id, RiskEvent.event_type == "testnet_local_exit_triggered")
        .one()
    )
    assert warning.severity == "warning"


def test_sync_exit_orders_logs_warning_when_cancel_sibling_fails():
    db = build_db()
    plan = seed_trade_plan_with_open_position(db)
    service = BinanceTestnetTradingService(db, binance_client=FakeBinanceClientCancelFails(), execution_enabled=True)

    result = asyncio.run(service.sync_exit_orders(plan.id))

    assert result["synced"] is True
    assert result["canceled_sibling_order_id"] is None
    sibling = db.query(Order).filter(Order.trade_plan_id == plan.id, Order.order_type == "take_profit_market").one()
    assert sibling.status == "new"
    warning = (
        db.query(RiskEvent)
        .filter(RiskEvent.trade_plan_id == plan.id, RiskEvent.event_type == "testnet_exit_sibling_cancel_failed")
        .one()
    )
    assert warning.severity == "warning"
    assert warning.context_json["sibling_order_id"] == "222222"


def test_sync_exit_orders_uses_effective_levels_to_avoid_false_local_exit():
    db = build_db()
    plan = seed_trade_plan_with_open_position(db)
    db.query(Order).filter(Order.trade_plan_id == plan.id).delete()
    db.add(
        RiskEvent(
            trade_plan_id=plan.id,
            event_type="testnet_protection_orders_failed",
            severity="critical",
            message="fallback levels",
            context_json={"effective_stop_loss": 49500.0, "effective_take_profit": 50800.0},
        )
    )
    db.commit()
    service = BinanceTestnetTradingService(db, binance_client=FakeBinanceClientLocalExitSaferLevel(), execution_enabled=True)

    result = asyncio.run(service.sync_exit_orders(plan.id))

    assert result == {"synced": True, "reason": "no_triggered_exit"}
    position = db.query(Position).filter(Position.trade_plan_id == plan.id).one()
    refreshed_plan = db.get(TradePlan, plan.id)
    assert position.status == "open"
    assert refreshed_plan.status == "testnet_executed"


def test_sync_exit_orders_does_not_close_local_position_when_local_exit_is_unconfirmed():
    db = build_db()
    plan = seed_trade_plan_with_open_position(db)
    db.query(Order).filter(Order.trade_plan_id == plan.id).delete()
    db.add(
        RiskEvent(
            trade_plan_id=plan.id,
            event_type="testnet_protection_orders_failed",
            severity="critical",
            message="fallback levels",
            context_json={"effective_stop_loss": 49725.0, "effective_take_profit": 50650.0},
        )
    )
    db.commit()
    service = BinanceTestnetTradingService(db, binance_client=FakeBinanceClientLocalExitAck(), execution_enabled=True)

    result = asyncio.run(service.sync_exit_orders(plan.id))

    assert result == {"synced": False, "reason": "local_exit_not_filled"}
    position = db.query(Position).filter(Position.trade_plan_id == plan.id).one()
    refreshed_plan = db.get(TradePlan, plan.id)
    assert position.status == "open"
    assert refreshed_plan.status == "testnet_executed"
    warning = (
        db.query(RiskEvent)
        .filter(RiskEvent.trade_plan_id == plan.id, RiskEvent.event_type == "testnet_local_exit_not_filled")
        .one()
    )
    assert warning.severity == "critical"


def test_sync_exit_orders_respects_execution_disabled_flag():
    db = build_db()
    plan = seed_trade_plan_with_open_position(db)
    service = BinanceTestnetTradingService(db, binance_client=FakeBinanceClientExitTriggered(), execution_enabled=False)

    result = asyncio.run(service.sync_exit_orders(plan.id))

    assert result == {"synced": False, "reason": "testnet_execution_disabled"}


def test_sync_open_testnet_exits_continues_when_one_plan_fails_with_generic_exception():
    db = build_db()
    failing_plan = seed_trade_plan_with_open_position(db)

    second_plan = TradePlan(
        symbol="ETHUSDT",
        side="long",
        timeframe="15m",
        market_regime="tendencia_alcista",
        technical_score=80,
        fundamental_score=65,
        sentiment_score=72,
        confidence_score=78,
        aggregate_score=76,
        entry_price=3000,
        stop_loss=2970,
        take_profit=3060,
        capital_usdt=1000,
        applied_risk_pct=1,
        max_position_notional=200,
        thesis="Setup aprobado",
        status="testnet_executed",
        is_testnet=True,
    )
    db.add(second_plan)
    db.commit()
    db.refresh(second_plan)
    db.add(
        Position(
            trade_plan_id=second_plan.id,
            symbol=second_plan.symbol,
            side=second_plan.side,
            quantity=0.1,
            entry_price=3000,
            mark_price=3010,
            unrealized_pnl=1.0,
            leverage=10,
            status="open",
            is_testnet=True,
        )
    )
    db.commit()

    service = BinanceTestnetTradingService(db, binance_client=FakeBinanceClientExitTriggered(), execution_enabled=True)

    async def fake_sync_exit_orders(trade_plan_id: int) -> dict:
        if trade_plan_id == failing_plan.id:
            raise RuntimeError("generic_sync_failure")
        return {"synced": False, "reason": "no_protection_orders"}

    service.sync_exit_orders = fake_sync_exit_orders  # type: ignore[method-assign]

    result = asyncio.run(service.sync_open_testnet_exits())

    assert result["synced"] is True
    assert result["checked_count"] == 2
    failing_item = next(item for item in result["results"] if item["trade_plan_id"] == failing_plan.id)
    second_item = next(item for item in result["results"] if item["trade_plan_id"] == second_plan.id)
    assert failing_item["reason"] == "sync_item_failed"
    assert second_item["reason"] == "no_protection_orders"

    warning = (
        db.query(RiskEvent)
        .filter(RiskEvent.trade_plan_id == failing_plan.id, RiskEvent.event_type == "testnet_open_exits_sync_item_failed")
        .one()
    )
    assert warning.severity == "warning"



def test_sync_exit_orders_logs_warning_when_cancel_order_is_unavailable():
    db = build_db()
    plan = seed_trade_plan_with_open_position(db)
    service = BinanceTestnetTradingService(db, binance_client=FakeBinanceClientNoCancel(), execution_enabled=True)

    result = asyncio.run(service.sync_exit_orders(plan.id))

    assert result["synced"] is True
    assert result["canceled_sibling_order_id"] is None
    warning = (
        db.query(RiskEvent)
        .filter(RiskEvent.trade_plan_id == plan.id, RiskEvent.event_type == "testnet_exit_sibling_cancel_unavailable")
        .one()
    )
    assert warning.severity == "warning"
    assert warning.context_json["sibling_order_ids"] == ["222222"]



def test_sync_exit_orders_returns_reason_when_trade_plan_already_closed():
    db = build_db()
    plan = seed_trade_plan_with_open_position(db)
    plan.status = "testnet_closed"
    db.commit()
    service = BinanceTestnetTradingService(db, binance_client=FakeBinanceClientExitTriggered(), execution_enabled=True)

    result = asyncio.run(service.sync_exit_orders(plan.id))

    assert result == {"synced": False, "reason": "trade_plan_already_closed"}



def test_sync_exit_orders_returns_warning_reason_when_refresh_fails():
    db = build_db()
    plan = seed_trade_plan_with_open_position(db)
    service = BinanceTestnetTradingService(db, binance_client=FakeBinanceClientRefreshFails(), execution_enabled=True)

    result = asyncio.run(service.sync_exit_orders(plan.id))

    assert result == {"synced": False, "reason": "exit_order_refresh_failed"}
    warning = (
        db.query(RiskEvent)
        .filter(RiskEvent.trade_plan_id == plan.id, RiskEvent.event_type == "testnet_exit_order_refresh_failed")
        .one()
    )
    assert warning.severity == "warning"
    assert warning.context_json["order_id"] == "111111"
