from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.db.base import Base
from apps.api.app.db.models import RiskEvent, TradePlan
from apps.api.app.services.production_reporting_service import ProductionReportingService


def build_db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


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
        thesis="reporting seed",
        status=status,
        is_testnet=True,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def seed_risk_event(db, trade_plan_id: int, *, severity: str, hours_ago: int = 1):
    event = RiskEvent(
        trade_plan_id=trade_plan_id,
        event_type="test_event",
        severity=severity,
        message="evt",
    )
    event.created_at = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    db.add(event)
    db.commit()


def test_daily_summary_aggregates_counts_and_scores():
    db = build_db()
    p1 = seed_trade_plan(db, status="approved", score=70)
    p2 = seed_trade_plan(db, status="blocked", score=50)
    seed_trade_plan(db, status="paper_executed", score=65)
    seed_trade_plan(db, status="testnet_executed", score=75)

    seed_risk_event(db, p1.id, severity="critical", hours_ago=1)
    seed_risk_event(db, p2.id, severity="warning", hours_ago=2)

    summary = ProductionReportingService(db).daily_summary()

    assert summary.total_trade_plans == 4
    assert summary.approved_trade_plans == 1
    assert summary.blocked_trade_plans == 1
    assert summary.paper_executed_trade_plans == 1
    assert summary.testnet_executed_trade_plans == 1
    assert summary.approved_trade_plans_24h == 1
    assert summary.blocked_trade_plans_24h == 1
    assert summary.paper_executed_trade_plans_24h == 1
    assert summary.testnet_executed_trade_plans_24h == 1
    assert summary.avg_aggregate_score == 65.0
    assert summary.critical_risk_events_24h == 1
    assert summary.warning_risk_events_24h == 1


def test_alerts_evaluate_flags_expected_conditions():
    db = build_db()
    p1 = seed_trade_plan(db, status="blocked", score=40)
    seed_trade_plan(db, status="blocked", score=42)
    seed_trade_plan(db, status="blocked", score=44)
    seed_trade_plan(db, status="blocked", score=46)
    seed_trade_plan(db, status="approved", score=45)
    seed_trade_plan(db, status="paper_executed", score=48)
    seed_trade_plan(db, status="paper_executed", score=50)

    for _ in range(5):
        seed_risk_event(db, p1.id, severity="critical", hours_ago=1)

    result = ProductionReportingService(db).evaluate_alerts()

    assert result.healthy is False
    categories = {alert.category for alert in result.alerts}
    assert "risk_events" in categories
    assert "trade_plan_conversion" in categories
    assert "execution_mode" in categories
    assert "signal_quality" in categories
