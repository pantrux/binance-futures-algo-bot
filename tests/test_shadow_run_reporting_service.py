from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.db.base import Base
from apps.api.app.db.models import Order, RiskEvent, TradePlan
from apps.api.app.services.shadow_run_reporting_service import ShadowRunReportingService


def build_db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def seed_trade_plan(
    db,
    *,
    symbol: str,
    side: str,
    status: str,
    entry_price: float,
    created_at: datetime,
) -> TradePlan:
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
        applied_risk_pct=1,
        max_position_notional=200,
        thesis="Shadow run seed",
        status=status,
        is_testnet=True,
    )
    plan.created_at = created_at
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def seed_order(db, trade_plan: TradePlan, *, status: str, price: float, created_at: datetime) -> None:
    order = Order(
        trade_plan_id=trade_plan.id,
        venue="binance_futures_testnet",
        external_order_id=f"ord-{trade_plan.id}-{status}",
        symbol=trade_plan.symbol,
        side=trade_plan.side,
        order_type="market",
        status=status,
        price=price,
        quantity=0.1,
        executed_quantity=0.1 if status == "filled" else 0,
        is_testnet=True,
    )
    order.created_at = created_at
    db.add(order)
    db.commit()


def seed_risk_event(db, trade_plan_id: int, *, severity: str, created_at: datetime) -> None:
    event = RiskEvent(
        trade_plan_id=trade_plan_id,
        event_type="shadow_run_check",
        severity=severity,
        message="evt",
    )
    event.created_at = created_at
    db.add(event)
    db.commit()



def test_shadow_run_summary_aggregates_pairs_fill_rate_slippage_and_risk() -> None:
    db = build_db()
    now = datetime.now(timezone.utc)
    paper = seed_trade_plan(db, symbol="BTCUSDT", side="long", status="paper_executed", entry_price=50000, created_at=now - timedelta(days=10))
    testnet = seed_trade_plan(db, symbol="BTCUSDT", side="long", status="testnet_executed", entry_price=50100, created_at=now - timedelta(days=9, hours=12))
    unmatched = seed_trade_plan(db, symbol="ETHUSDT", side="short", status="paper_executed", entry_price=3000, created_at=now - timedelta(days=2))

    seed_order(db, testnet, status="filled", price=50125, created_at=now - timedelta(hours=12))
    seed_order(db, unmatched, status="rejected", price=3000, created_at=now - timedelta(hours=10))
    seed_risk_event(db, testnet.id, severity="critical", created_at=now - timedelta(days=2))
    seed_risk_event(db, testnet.id, severity="warning", created_at=now - timedelta(days=1))

    summary = ShadowRunReportingService(db).build_summary(window_days=30)

    assert summary.paper_executed_trade_plans == 2
    assert summary.testnet_executed_trade_plans == 1
    assert summary.compared_pairs == 1
    assert summary.unmatched_paper == 1
    assert summary.unmatched_testnet == 0
    assert summary.shadow_run_duration_days >= 7
    assert summary.testnet_orders_total == 1
    assert summary.testnet_orders_filled == 1
    assert summary.testnet_fill_rate_pct == 100.0
    assert summary.avg_testnet_slippage_bps == 4.99
    assert summary.critical_risk_events_7d == 1
    assert summary.warning_risk_events_7d == 1
    assert summary.total_risk_events_30d == 2
    assert len(summary.symbols) == 2
    assert summary.symbols[0].symbol == "BTCUSDT"



def test_shadow_run_summary_does_not_pair_plans_beyond_max_temporal_delta() -> None:
    db = build_db()
    now = datetime.now(timezone.utc)
    seed_trade_plan(db, symbol="BTCUSDT", side="long", status="paper_executed", entry_price=50000, created_at=now - timedelta(days=10))
    seed_trade_plan(db, symbol="BTCUSDT", side="long", status="testnet_executed", entry_price=50010, created_at=now - timedelta(days=1))

    summary = ShadowRunReportingService(db).build_summary(window_days=30)

    assert summary.compared_pairs == 0
    assert summary.unmatched_paper == 1
    assert summary.unmatched_testnet == 1
    assert summary.avg_entry_price_diff_pct is None



def test_shadow_run_summary_prefers_matching_timeframe_over_closer_cross_timeframe_candidate() -> None:
    db = build_db()
    now = datetime.now(timezone.utc)
    paper = seed_trade_plan(
        db,
        symbol="BTCUSDT",
        side="long",
        status="paper_executed",
        entry_price=50000,
        created_at=now - timedelta(hours=4),
    )
    wrong_timeframe = seed_trade_plan(
        db,
        symbol="BTCUSDT",
        side="long",
        status="testnet_executed",
        entry_price=50020,
        created_at=now - timedelta(hours=3, minutes=55),
    )
    wrong_timeframe.timeframe = "1h"
    db.add(wrong_timeframe)
    matching_timeframe = seed_trade_plan(
        db,
        symbol="BTCUSDT",
        side="long",
        status="testnet_executed",
        entry_price=50040,
        created_at=now - timedelta(hours=3, minutes=40),
    )
    matching_timeframe.timeframe = paper.timeframe
    db.add(matching_timeframe)
    db.commit()

    summary = ShadowRunReportingService(db).build_summary(window_days=30)

    assert summary.compared_pairs == 1
    assert summary.unmatched_paper == 0
    assert summary.unmatched_testnet == 1
    assert summary.avg_entry_price_diff_pct == 0.08



def test_shadow_run_summary_does_not_pair_same_symbol_side_when_timeframe_differs() -> None:
    db = build_db()
    now = datetime.now(timezone.utc)
    paper = seed_trade_plan(
        db,
        symbol="ETHUSDT",
        side="short",
        status="paper_executed",
        entry_price=3000,
        created_at=now - timedelta(hours=6),
    )
    testnet = seed_trade_plan(
        db,
        symbol="ETHUSDT",
        side="short",
        status="testnet_executed",
        entry_price=3010,
        created_at=now - timedelta(hours=5, minutes=58),
    )
    paper.timeframe = "15m"
    testnet.timeframe = "4h"
    db.add_all([paper, testnet])
    db.commit()

    summary = ShadowRunReportingService(db).build_summary(window_days=30)

    assert summary.compared_pairs == 0
    assert summary.unmatched_paper == 1
    assert summary.unmatched_testnet == 1
    assert summary.avg_entry_price_diff_pct is None



def test_shadow_run_summary_returns_zeroed_metrics_when_no_data() -> None:
    db = build_db()

    summary = ShadowRunReportingService(db).build_summary(window_days=30)

    assert summary.paper_executed_trade_plans == 0
    assert summary.testnet_executed_trade_plans == 0
    assert summary.compared_pairs == 0
    assert summary.testnet_fill_rate_pct is None
    assert summary.avg_testnet_slippage_bps is None
    assert summary.shadow_run_start_at is None
    assert summary.symbols == []


def test_shadow_run_summary_filters_by_timeframe_when_requested() -> None:
    db = build_db()
    now = datetime.now(timezone.utc)
    seed_trade_plan(db, symbol="BTCUSDT", side="long", status="paper_executed", entry_price=50000, created_at=now - timedelta(days=10))
    seed_trade_plan(db, symbol="BTCUSDT", side="long", status="testnet_executed", entry_price=50100, created_at=now - timedelta(days=9, hours=12))
    paper_1h = seed_trade_plan(db, symbol="BTCUSDT", side="long", status="paper_executed", entry_price=51000, created_at=now - timedelta(days=8))
    testnet_1h = seed_trade_plan(db, symbol="BTCUSDT", side="long", status="testnet_executed", entry_price=51100, created_at=now - timedelta(days=7, hours=12))
    paper_1h.timeframe = "1h"
    testnet_1h.timeframe = "1h"
    db.add_all([paper_1h, testnet_1h])
    db.commit()

    summary = ShadowRunReportingService(db).build_summary(window_days=30, timeframe="1h")

    assert summary.timeframe == "1h"
    assert summary.paper_executed_trade_plans == 1
    assert summary.testnet_executed_trade_plans == 1
    assert summary.compared_pairs == 1
    assert len(summary.symbols) == 1
    assert summary.symbols[0].symbol == "BTCUSDT"


def test_shadow_run_summary_returns_empty_filtered_summary_when_timeframe_has_no_matches() -> None:
    db = build_db()
    now = datetime.now(timezone.utc)
    seed_trade_plan(db, symbol="ETHUSDT", side="long", status="paper_executed", entry_price=3000, created_at=now - timedelta(days=2))

    summary = ShadowRunReportingService(db).build_summary(window_days=30, timeframe="4h")

    assert summary.timeframe == "4h"
    assert summary.paper_executed_trade_plans == 0
    assert summary.testnet_executed_trade_plans == 0
    assert summary.compared_pairs == 0
    assert summary.symbols == []



def test_shadow_run_summary_filters_order_aggregates_by_timeframe_when_requested() -> None:
    db = build_db()
    now = datetime.now(timezone.utc)
    paper_15m = seed_trade_plan(
        db,
        symbol="BTCUSDT",
        side="long",
        status="paper_executed",
        entry_price=50000,
        created_at=now - timedelta(days=10),
    )
    testnet_15m = seed_trade_plan(
        db,
        symbol="BTCUSDT",
        side="long",
        status="testnet_executed",
        entry_price=50100,
        created_at=now - timedelta(days=9, hours=12),
    )
    paper_1h = seed_trade_plan(
        db,
        symbol="BTCUSDT",
        side="long",
        status="paper_executed",
        entry_price=51000,
        created_at=now - timedelta(days=8),
    )
    testnet_1h = seed_trade_plan(
        db,
        symbol="BTCUSDT",
        side="long",
        status="testnet_executed",
        entry_price=51100,
        created_at=now - timedelta(days=7, hours=12),
    )
    paper_1h.timeframe = "1h"
    testnet_1h.timeframe = "1h"
    db.add_all([paper_1h, testnet_1h])
    db.commit()

    seed_order(db, testnet_15m, status="filled", price=50125, created_at=now - timedelta(hours=12))
    seed_order(db, testnet_1h, status="filled", price=51120, created_at=now - timedelta(hours=11))

    summary = ShadowRunReportingService(db).build_summary(window_days=30, timeframe="1h")

    assert summary.timeframe == "1h"
    assert summary.paper_executed_trade_plans == 1
    assert summary.testnet_executed_trade_plans == 1
    assert summary.testnet_orders_total == 1
    assert summary.testnet_orders_filled == 1
    assert summary.testnet_fill_rate_pct == 100.0
    assert summary.avg_testnet_slippage_bps == 3.9139
