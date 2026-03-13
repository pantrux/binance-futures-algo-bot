from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.db.base import Base
from apps.api.app.db.models import TradePlan
from apps.api.app.services.execution_parity_service import ExecutionParityService


def build_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def seed_plan(
    db,
    *,
    symbol: str,
    side: str,
    status: str,
    entry_price: float,
    risk_pct: float,
    notional: float,
    created_at: datetime | None = None,
):
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
        entry_price=entry_price,
        stop_loss=entry_price * 0.995,
        take_profit=entry_price * 1.01,
        capital_usdt=1000,
        applied_risk_pct=risk_pct,
        max_position_notional=notional,
        thesis="Parity seed",
        status=status,
        is_testnet=True,
    )
    if created_at is not None:
        plan.created_at = created_at

    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def test_execution_parity_builds_pairs_and_averages():
    db = build_db()
    seed_plan(db, symbol="BTCUSDT", side="long", status="paper_executed", entry_price=50000, risk_pct=1.0, notional=200)
    seed_plan(db, symbol="BTCUSDT", side="long", status="testnet_executed", entry_price=50100, risk_pct=0.9, notional=190)
    seed_plan(db, symbol="BTCUSDT", side="short", status="paper_executed", entry_price=49500, risk_pct=1.1, notional=210)
    seed_plan(db, symbol="BTCUSDT", side="short", status="testnet_executed", entry_price=49400, risk_pct=1.0, notional=205)

    report = ExecutionParityService(db).build_report(symbol="BTCUSDT", limit=50)

    assert report.compared_pairs == 2
    assert report.unmatched_paper == 0
    assert report.unmatched_testnet == 0
    assert report.avg_entry_price_diff_pct is not None
    assert report.avg_applied_risk_diff_pct is not None
    assert report.avg_max_notional_diff_pct is not None


def test_execution_parity_reports_unmatched_runs():
    db = build_db()
    seed_plan(db, symbol="ETHUSDT", side="long", status="paper_executed", entry_price=3000, risk_pct=1.0, notional=150)

    report = ExecutionParityService(db).build_report(symbol="ETHUSDT", limit=50)

    assert report.compared_pairs == 0
    assert report.unmatched_paper == 1
    assert report.unmatched_testnet == 0
    assert report.avg_entry_price_diff_pct is None


def test_execution_parity_pct_diff_handles_zero_values_safely():
    service = ExecutionParityService(build_db())

    assert service._pct_diff(0, 0) == 0.0
    assert service._pct_diff(0, 10) == 100.0
    assert service._pct_diff(10, 0) == 100.0


def test_execution_parity_pairs_by_nearest_timestamp_for_same_side():
    db = build_db()
    base = datetime(2026, 3, 13, 0, 0, tzinfo=timezone.utc)

    paper = seed_plan(
        db,
        symbol="BTCUSDT",
        side="long",
        status="paper_executed",
        entry_price=50000,
        risk_pct=1.0,
        notional=200,
        created_at=base,
    )
    far = seed_plan(
        db,
        symbol="BTCUSDT",
        side="long",
        status="testnet_executed",
        entry_price=51000,
        risk_pct=1.0,
        notional=200,
        created_at=base + timedelta(minutes=30),
    )
    near = seed_plan(
        db,
        symbol="BTCUSDT",
        side="long",
        status="testnet_executed",
        entry_price=50050,
        risk_pct=1.0,
        notional=200,
        created_at=base + timedelta(minutes=1),
    )

    report = ExecutionParityService(db).build_report(symbol="BTCUSDT", limit=50)

    assert report.compared_pairs == 1
    assert report.pairs[0].paper_trade_plan_id == paper.id
    assert report.pairs[0].testnet_trade_plan_id == near.id
    assert report.unmatched_testnet == 1
    assert far.id != report.pairs[0].testnet_trade_plan_id
