from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.core.settings import settings
from apps.api.app.db.base import Base
from apps.api.app.db.models import Order, Position, RiskEvent, TradePlan
from apps.api.app.services.dashboard_command_center_service import DashboardCommandCenterService
from apps.api.app.services.shadow_run_reporting_service import ShadowRunReportingService


def build_db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def seed_trade_plan(db, *, status: str, created_at: datetime, symbol: str = "BTCUSDT") -> TradePlan:
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
        entry_price=50000,
        stop_loss=49750,
        take_profit=50600,
        capital_usdt=1000,
        applied_risk_pct=1,
        max_position_notional=200,
        thesis="seed",
        status=status,
        is_testnet=True,
    )
    plan.created_at = created_at
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def seed_order(db, plan: TradePlan, *, status: str, created_at: datetime):
    order = Order(
        trade_plan_id=plan.id,
        venue="binance_futures_testnet",
        external_order_id=f"ord-{plan.id}-{status}",
        symbol=plan.symbol,
        side=plan.side,
        order_type="market",
        status=status,
        price=50000,
        quantity=0.1,
        executed_quantity=0.1 if status == "filled" else 0.0,
        is_testnet=True,
    )
    order.created_at = created_at
    db.add(order)
    db.commit()


def seed_position(db, plan: TradePlan, *, status: str, opened_at: datetime):
    position = Position(
        trade_plan_id=plan.id,
        symbol=plan.symbol,
        side=plan.side,
        quantity=0.1,
        entry_price=50000,
        mark_price=50010,
        unrealized_pnl=1.0,
        leverage=5,
        status=status,
        is_testnet=True,
    )
    position.opened_at = opened_at
    db.add(position)
    db.commit()


def seed_risk_event(db, plan: TradePlan, *, created_at: datetime, event_type: str = "shadow_run_check"):
    event = RiskEvent(
        trade_plan_id=plan.id,
        event_type=event_type,
        severity="warning",
        message="evt",
    )
    event.created_at = created_at
    db.add(event)
    db.commit()


def test_shadow_run_summary_respects_operational_cutover():
    db = build_db()
    now = datetime.now(timezone.utc)
    legacy_time = now - timedelta(days=10)
    fresh_time = now - timedelta(days=1)

    seed_trade_plan(db, status="paper_executed", created_at=legacy_time, symbol="BTCUSDT")
    seed_trade_plan(db, status="testnet_executed", created_at=legacy_time + timedelta(hours=1), symbol="BTCUSDT")
    fresh_paper = seed_trade_plan(db, status="paper_executed", created_at=fresh_time, symbol="ETHUSDT")
    fresh_testnet = seed_trade_plan(db, status="testnet_executed", created_at=fresh_time + timedelta(minutes=30), symbol="ETHUSDT")
    seed_order(db, fresh_testnet, status="filled", created_at=fresh_time + timedelta(minutes=31))

    old_cutover = settings.operational_cutover_at
    settings.operational_cutover_at = now - timedelta(days=2)
    try:
        summary = ShadowRunReportingService(db).build_summary(window_days=30)
    finally:
        settings.operational_cutover_at = old_cutover

    assert summary.paper_executed_trade_plans == 1
    assert summary.testnet_executed_trade_plans == 1
    assert summary.compared_pairs == 1
    assert summary.avg_risk_events_per_day_30d == 0.0
    assert all(symbol.symbol == "ETHUSDT" for symbol in summary.symbols)



def test_command_center_respects_operational_cutover(monkeypatch):
    db = build_db()
    now = datetime.now(timezone.utc)
    legacy_time = now - timedelta(days=7)
    fresh_time = now - timedelta(hours=3)

    legacy = seed_trade_plan(db, status="testnet_executed", created_at=legacy_time, symbol="BTCUSDT")
    seed_order(db, legacy, status="filled", created_at=legacy_time + timedelta(minutes=1))
    seed_position(db, legacy, status="open", opened_at=legacy_time + timedelta(minutes=2))
    seed_risk_event(db, legacy, created_at=legacy_time + timedelta(minutes=3))

    fresh = seed_trade_plan(db, status="testnet_executed", created_at=fresh_time, symbol="ETHUSDT")
    seed_order(db, fresh, status="filled", created_at=fresh_time + timedelta(minutes=1))
    seed_position(db, fresh, status="open", opened_at=fresh_time + timedelta(minutes=2))
    seed_risk_event(db, fresh, created_at=fresh_time + timedelta(minutes=3))

    old_cutover = settings.operational_cutover_at
    settings.operational_cutover_at = now - timedelta(days=1)
    try:
        payload = DashboardCommandCenterService(db).build()
    finally:
        settings.operational_cutover_at = old_cutover

    assert payload.operational_cutover_at == now - timedelta(days=1)
    assert payload.summary.trade_plans_total == 1
    assert payload.summary.open_positions == 1
    assert payload.summary.risk_events_total == 1
    assert payload.recent_trade_plans[0].symbol == "ETHUSDT"
    assert all(plan.symbol != "BTCUSDT" for plan in payload.recent_trade_plans)


def test_command_center_excludes_mitigation_noise_from_operational_risk_counts():
    db = build_db()
    now = datetime.now(timezone.utc)
    fresh = seed_trade_plan(db, status="testnet_executed", created_at=now - timedelta(hours=2), symbol="ETHUSDT")
    seed_order(db, fresh, status="filled", created_at=now - timedelta(hours=2) + timedelta(minutes=1))
    seed_position(db, fresh, status="open", opened_at=now - timedelta(hours=2) + timedelta(minutes=2))
    seed_risk_event(db, fresh, created_at=now - timedelta(hours=2) + timedelta(minutes=3), event_type="testnet_protection_orders_failed")
    seed_risk_event(db, fresh, created_at=now - timedelta(hours=2) + timedelta(minutes=4), event_type="testnet_local_exit_triggered")
    seed_risk_event(db, fresh, created_at=now - timedelta(hours=2) + timedelta(minutes=5), event_type="shadow_run_check")

    old_cutover = settings.operational_cutover_at
    settings.operational_cutover_at = now - timedelta(days=1)
    try:
        payload = DashboardCommandCenterService(db).build()
    finally:
        settings.operational_cutover_at = old_cutover

    assert payload.summary.risk_events_total == 1
    assert len(payload.recent_risk_events) == 1
    assert payload.recent_risk_events[0].event_type == "shadow_run_check"
