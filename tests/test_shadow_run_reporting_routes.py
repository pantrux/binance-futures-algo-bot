from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from apps.api.app.api.deps import get_db
from apps.api.app.api.routes import require_metrics_auth, router
from apps.api.app.db.base import Base
from apps.api.app.db.models import Order, RiskEvent, TradePlan



def make_client(db_session) -> TestClient:
    app = FastAPI()
    app.include_router(router)

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_require_metrics_auth() -> None:
        return None

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[require_metrics_auth] = override_require_metrics_auth
    return TestClient(app)



def seed_trade_plan(db, *, symbol: str, status: str, side: str, created_at: datetime) -> TradePlan:
    plan = TradePlan(
        symbol=symbol,
        side=side,
        timeframe="15m",
        market_regime="tendencia_alcista",
        technical_score=80,
        fundamental_score=70,
        sentiment_score=75,
        confidence_score=78,
        aggregate_score=77,
        entry_price=50000 if symbol == "BTCUSDT" else 3000,
        stop_loss=49750 if symbol == "BTCUSDT" else 2980,
        take_profit=50600 if symbol == "BTCUSDT" else 3040,
        capital_usdt=1000,
        applied_risk_pct=1,
        max_position_notional=200,
        thesis="shadow route",
        status=status,
        is_testnet=True,
    )
    plan.created_at = created_at
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan



def test_reporting_shadow_run_summary_route_returns_payload() -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    now = datetime.now(timezone.utc)

    paper = seed_trade_plan(db, symbol="BTCUSDT", status="paper_executed", side="long", created_at=now - timedelta(days=8))
    testnet = seed_trade_plan(db, symbol="BTCUSDT", status="testnet_executed", side="long", created_at=now - timedelta(days=1))

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
    order.created_at = now - timedelta(hours=2)
    db.add(order)

    event = RiskEvent(trade_plan_id=paper.id, event_type="shadow", severity="warning", message="m")
    event.created_at = now - timedelta(days=1)
    db.add(event)
    db.commit()

    client = make_client(db)
    response = client.get("/reporting/shadow-run-summary?window_days=30")

    assert response.status_code == 200
    payload = response.json()
    assert payload["window_days"] == 30
    assert payload["paper_executed_trade_plans"] == 1
    assert payload["testnet_executed_trade_plans"] == 1
    assert payload["compared_pairs"] == 1
    assert payload["testnet_orders_total"] == 1
    assert payload["warning_risk_events_7d"] == 1
    assert payload["symbols"][0]["symbol"] == "BTCUSDT"
