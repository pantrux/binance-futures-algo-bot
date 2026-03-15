from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from apps.api.app.api.deps import get_db
from apps.api.app.api.routes import router
from apps.api.app.db.base import Base
from apps.api.app.db.models import Order, Position, RiskEvent, TradePlan



def make_client(db_session) -> TestClient:
    app = FastAPI()
    app.include_router(router)

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)



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
        entry_price=50000,
        stop_loss=49750,
        take_profit=50600,
        capital_usdt=1000,
        applied_risk_pct=1,
        max_position_notional=200,
        thesis="dashboard route",
        status=status,
        is_testnet=True,
    )
    plan.created_at = created_at
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan



def test_dashboard_command_center_route_returns_payload():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    now = datetime.now(timezone.utc)

    plan = seed_trade_plan(db, symbol="BTCUSDT", status="testnet_executed", created_at=now - timedelta(hours=1))

    order = Order(
        trade_plan_id=plan.id,
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
    order.created_at = now - timedelta(minutes=50)
    db.add(order)

    position = Position(
        trade_plan_id=plan.id,
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
    position.opened_at = now - timedelta(minutes=45)
    db.add(position)

    event = RiskEvent(trade_plan_id=plan.id, event_type="shadow_run_check", severity="warning", message="warning")
    event.created_at = now - timedelta(minutes=30)
    db.add(event)
    db.commit()

    client = make_client(db)
    response = client.get("/dashboard/command-center")

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["testnet_executed_trade_plans"] == 1
    assert payload["shadow_run"]["testnet_orders_total"] == 1
    assert payload["shadow_run"]["testnet_fill_rate_pct"] == 100.0
    assert payload["operation_snapshots"][0]["trade_plan_id"] == plan.id
    assert payload["operation_snapshots"][0]["latest_order_status"] == "filled"
    assert payload["operation_snapshots"][0]["latest_position_status"] == "open"
    assert payload["operation_snapshots"][0]["reconciliation_healthy"] is True
    assert payload["operation_snapshots"][0]["technical_score"] == 80
    assert payload["operation_snapshots"][0]["timeframe"] == "15m"
    assert payload["operation_snapshots"][0]["thesis"] == "dashboard route"
    assert payload["timeline"][0]["trade_plan_id"] == plan.id
    assert len(payload["timeline"]) >= 4
    assert payload["recent_trade_plans"][0]["id"] == plan.id
    assert payload["recent_orders"][0]["trade_plan_id"] == plan.id
    assert payload["open_positions"][0]["trade_plan_id"] == plan.id
    assert payload["recent_risk_events"][0]["trade_plan_id"] == plan.id
