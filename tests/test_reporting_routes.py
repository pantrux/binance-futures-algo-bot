from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from apps.api.app.api.routes import router
from apps.api.app.db.base import Base
from apps.api.app.db.models import RiskEvent, TradePlan
from apps.api.app.api.deps import get_db


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


def seed_trade_plan(db, *, status: str, score: float):
    plan = TradePlan(
        symbol="BTCUSDT",
        side="long",
        timeframe="15m",
        market_regime="tendencia_alcista",
        technical_score=score,
        fundamental_score=score,
        sentiment_score=score,
        confidence_score=score,
        aggregate_score=score,
        entry_price=50000,
        stop_loss=49750,
        take_profit=50600,
        capital_usdt=1000,
        applied_risk_pct=1,
        max_position_notional=200,
        thesis="route reporting",
        status=status,
        is_testnet=True,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def test_reporting_daily_summary_route_returns_payload():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()

    seed_trade_plan(db, status="approved", score=70)
    seed_trade_plan(db, status="blocked", score=50)

    client = make_client(db)
    response = client.get("/reporting/daily-summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_trade_plans"] == 2
    assert payload["approved_trade_plans"] == 1
    assert payload["blocked_trade_plans"] == 1
    assert payload["approved_trade_plans_24h"] == 1
    assert payload["blocked_trade_plans_24h"] == 1


def test_alerts_evaluate_route_returns_non_healthy_when_critical_events_high():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()

    plan = seed_trade_plan(db, status="blocked", score=40)
    for _ in range(5):
        event = RiskEvent(trade_plan_id=plan.id, event_type="e", severity="critical", message="m")
        event.created_at = datetime.now(timezone.utc) - timedelta(hours=1)
        db.add(event)
    db.commit()

    client = make_client(db)
    response = client.get("/alerts/evaluate")

    assert response.status_code == 200
    payload = response.json()
    assert payload["healthy"] is False
    assert any(alert["category"] == "risk_events" for alert in payload["alerts"])
