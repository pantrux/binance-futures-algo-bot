from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from apps.api.app.api.routes import router
from apps.api.app.db.base import Base
from apps.api.app.db.models import Order, Position, TradePlan
from apps.api.app.api.deps import get_db
from fastapi import FastAPI


def make_client(db_session: Session) -> TestClient:
    app = FastAPI()
    app.include_router(router)

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def seed_trade_plan(db: Session, *, symbol: str, status: str, side: str = "long") -> TradePlan:
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
        entry_price=50000,
        stop_loss=49750,
        take_profit=50600,
        capital_usdt=1000,
        applied_risk_pct=1,
        max_position_notional=200,
        thesis="Route seed",
        status=status,
        is_testnet=True,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def test_reconcile_execution_route_returns_report():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    plan = seed_trade_plan(db, symbol="BTCUSDT", status="testnet_executed")
    db.add(
        Order(
            trade_plan_id=plan.id,
            venue="binance_futures_testnet",
            external_order_id="ord-1",
            symbol=plan.symbol,
            side=plan.side,
            order_type="market",
            status="filled",
            price=50000,
            quantity=0.1,
            executed_quantity=0.1,
            is_testnet=True,
        )
    )
    db.add(
        Position(
            trade_plan_id=plan.id,
            symbol=plan.symbol,
            side=plan.side,
            quantity=0.1,
            entry_price=50000,
            mark_price=50000,
            unrealized_pnl=0,
            leverage=5,
            status="open",
            is_testnet=True,
        )
    )
    db.commit()

    client = make_client(db)
    response = client.get(f"/execution/reconcile/{plan.id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["healthy"] is True
    assert payload["trade_plan_id"] == plan.id


def test_execution_parity_route_returns_pairs():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    seed_trade_plan(db, symbol="ETHUSDT", status="paper_executed", side="long")
    seed_trade_plan(db, symbol="ETHUSDT", status="testnet_executed", side="long")

    client = make_client(db)
    response = client.get("/execution/parity/ETHUSDT?limit=50")

    assert response.status_code == 200
    payload = response.json()
    assert payload["symbol"] == "ETHUSDT"
    assert payload["compared_pairs"] == 1
