from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.db.base import Base
from apps.api.app.db.models import Order, Position, RiskEvent, TradePlan
from apps.api.app.services.dashboard_command_center_service import DashboardCommandCenterService


def build_db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()



def seed_trade_plan(db, *, symbol: str, status: str, created_at: datetime) -> TradePlan:
    plan = TradePlan(
        symbol=symbol,
        side="long",
        timeframe="15m",
        market_regime="tendencia_alcista",
        technical_score=80,
        fundamental_score=70,
        sentiment_score=75,
        confidence_score=78,
        aggregate_score=77,
        entry_price=50000 if symbol == "BTCUSDT" else 3200,
        stop_loss=49750 if symbol == "BTCUSDT" else 3175,
        take_profit=50600 if symbol == "BTCUSDT" else 3260,
        capital_usdt=1000,
        applied_risk_pct=1,
        max_position_notional=200,
        thesis="dashboard command center",
        status=status,
        is_testnet=True,
    )
    plan.created_at = created_at
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan



def test_dashboard_command_center_builds_operational_snapshot():
    db = build_db()
    now = datetime.now(timezone.utc)
    paper = seed_trade_plan(db, symbol="BTCUSDT", status="paper_executed", created_at=now - timedelta(days=2))
    testnet = seed_trade_plan(db, symbol="BTCUSDT", status="testnet_executed", created_at=now - timedelta(hours=2))
    approved = seed_trade_plan(db, symbol="ETHUSDT", status="approved", created_at=now - timedelta(hours=1))

    old_order = Order(
        trade_plan_id=testnet.id,
        venue="binance_futures_testnet",
        external_order_id="ord-0",
        symbol="BTCUSDT",
        side="long",
        order_type="market",
        status="new",
        price=49990,
        quantity=0.1,
        executed_quantity=0,
        is_testnet=True,
    )
    old_order.created_at = now - timedelta(hours=2)
    db.add(old_order)

    order = Order(
        trade_plan_id=testnet.id,
        venue="binance_futures_testnet",
        external_order_id="ord-1",
        symbol="BTCUSDT",
        side="long",
        order_type="market",
        status="filled",
        price=50010,
        quantity=0.1,
        executed_quantity=0.1,
        is_testnet=True,
    )
    order.created_at = now - timedelta(hours=1)
    db.add(order)

    old_position = Position(
        trade_plan_id=testnet.id,
        symbol="BTCUSDT",
        side="long",
        quantity=0.1,
        entry_price=49990,
        mark_price=50000,
        unrealized_pnl=4,
        leverage=5,
        status="closed",
        is_testnet=True,
    )
    old_position.opened_at = now - timedelta(hours=2)
    db.add(old_position)

    position = Position(
        trade_plan_id=testnet.id,
        symbol="BTCUSDT",
        side="long",
        quantity=0.1,
        entry_price=50000,
        mark_price=50010,
        unrealized_pnl=10,
        leverage=5,
        status="open",
        is_testnet=True,
    )
    position.opened_at = now - timedelta(hours=1)
    db.add(position)

    old_event = RiskEvent(
        trade_plan_id=testnet.id,
        event_type="preflight_note",
        severity="info",
        message="all good",
        context_json={"source": "runbook", "checkpoint": "preflight"},
    )
    old_event.created_at = now - timedelta(minutes=80)
    db.add(old_event)

    event = RiskEvent(trade_plan_id=approved.id, event_type="shadow_run_check", severity="warning", message="warning")
    event.created_at = now - timedelta(minutes=30)
    db.add(event)
    db.commit()

    payload = DashboardCommandCenterService(db).build()

    assert payload.summary.trade_plans_total == 3
    assert payload.summary.approved_trade_plans == 1
    assert payload.summary.paper_executed_trade_plans == 1
    assert payload.summary.testnet_executed_trade_plans == 1
    assert payload.summary.open_positions == 1
    assert payload.summary.risk_events_total == 2
    assert payload.shadow_run.testnet_orders_total == 2
    assert payload.shadow_run.testnet_orders_filled == 1
    assert payload.shadow_run.testnet_fill_rate_pct == 50.0
    assert payload.operation_snapshots[0].trade_plan_id == approved.id
    assert payload.operation_snapshots[1].trade_plan_id == testnet.id
    assert payload.operation_snapshots[1].latest_order_status == "filled"
    assert payload.operation_snapshots[1].latest_position_status == "open"
    assert payload.operation_snapshots[1].reconciliation_healthy is True
    assert payload.operation_snapshots[1].technical_score == 80
    assert payload.operation_snapshots[1].timeframe == "15m"
    assert payload.operation_snapshots[1].thesis == "dashboard command center"
    assert payload.operation_snapshots[1].reconciliation_order_count == 2
    assert payload.operation_snapshots[1].reconciliation_filled_order_count == 1
    assert len(payload.operation_snapshots[1].order_history) == 2
    assert payload.operation_snapshots[1].order_history[0].status == "filled"
    assert len(payload.operation_snapshots[1].position_history) == 2
    assert payload.operation_snapshots[1].position_history[0].status == "open"
    assert len(payload.operation_snapshots[1].risk_event_history) == 1
    assert payload.operation_snapshots[1].risk_event_history[0].event_type == "preflight_note"
    assert payload.operation_snapshots[1].risk_event_history[0].context["checkpoint"] == "preflight"
    assert payload.operation_snapshots[1].latest_risk_context["checkpoint"] == "preflight"
    assert len(payload.operation_snapshots[1].timeline_history) >= 4
    assert payload.operation_snapshots[0].latest_risk_event_type == "shadow_run_check"
    assert payload.timeline[0].trade_plan_id in {approved.id, testnet.id}
    assert {item.entity_kind for item in payload.timeline} >= {"trade_plan", "order", "position", "risk_event"}
    assert payload.recent_trade_plans[0].id == approved.id
    assert payload.recent_orders[0].trade_plan_id == testnet.id
    assert payload.open_positions[0].trade_plan_id == testnet.id
    assert payload.recent_risk_events[0].trade_plan_id == approved.id
