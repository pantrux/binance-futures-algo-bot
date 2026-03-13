from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.db.base import Base
from apps.api.app.db.models import Order, Position, TradePlan
from apps.api.app.services.execution_state_machine_service import ExecutionStateMachineService


def build_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def seed_trade_plan(db, *, status: str = "testnet_executed") -> TradePlan:
    plan = TradePlan(
        symbol="BTCUSDT",
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
        thesis="Plan de prueba",
        status=status,
        is_testnet=True,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def test_reconcile_reports_healthy_when_order_and_position_match():
    db = build_db()
    plan = seed_trade_plan(db)

    db.add(
        Order(
            trade_plan_id=plan.id,
            venue="binance_futures_testnet",
            external_order_id="abc",
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

    report = ExecutionStateMachineService(db).reconcile_trade_plan(plan.id)

    assert report.healthy is True
    assert report.recommended_actions == ["none"]


def test_reconcile_detects_missing_position_and_order_for_executed_plan():
    db = build_db()
    plan = seed_trade_plan(db)

    report = ExecutionStateMachineService(db).reconcile_trade_plan(plan.id)

    assert report.healthy is False
    assert {event.event_type for event in report.drift_events} == {
        "missing_filled_order",
        "missing_position_association",
    }
    assert "replay_execution_audit" in report.recommended_actions
    assert "rebuild_position_state" in report.recommended_actions


def test_reconcile_detects_multiple_open_positions():
    db = build_db()
    plan = seed_trade_plan(db)

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
    db.add_all(
        [
            Position(
                trade_plan_id=plan.id,
                symbol=plan.symbol,
                side=plan.side,
                quantity=0.05,
                entry_price=50000,
                mark_price=50000,
                unrealized_pnl=0,
                leverage=3,
                status="open",
                is_testnet=True,
            ),
            Position(
                trade_plan_id=plan.id,
                symbol=plan.symbol,
                side=plan.side,
                quantity=0.05,
                entry_price=50010,
                mark_price=50010,
                unrealized_pnl=0,
                leverage=3,
                status="open",
                is_testnet=True,
            ),
        ]
    )
    db.commit()

    report = ExecutionStateMachineService(db).reconcile_trade_plan(plan.id)

    assert report.healthy is False
    assert any(event.event_type == "multiple_open_positions" for event in report.drift_events)


def test_reconcile_detects_rejected_order_on_executed_plan():
    db = build_db()
    plan = seed_trade_plan(db)

    db.add_all(
        [
            Order(
                trade_plan_id=plan.id,
                venue="binance_futures_testnet",
                external_order_id="ord-fill",
                symbol=plan.symbol,
                side=plan.side,
                order_type="market",
                status="filled",
                price=50000,
                quantity=0.1,
                executed_quantity=0.1,
                is_testnet=True,
            ),
            Order(
                trade_plan_id=plan.id,
                venue="binance_futures_testnet",
                external_order_id="ord-rej",
                symbol=plan.symbol,
                side=plan.side,
                order_type="market",
                status="rejected",
                price=50000,
                quantity=0.1,
                executed_quantity=0.0,
                is_testnet=True,
            ),
        ]
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
            leverage=3,
            status="open",
            is_testnet=True,
        )
    )
    db.commit()

    report = ExecutionStateMachineService(db).reconcile_trade_plan(plan.id)

    assert report.healthy is False
    assert any(event.event_type == "executed_with_rejected_orders" for event in report.drift_events)


def test_reconcile_returns_healthy_for_non_executed_plan_without_orders():
    db = build_db()
    plan = seed_trade_plan(db, status="approved")

    report = ExecutionStateMachineService(db).reconcile_trade_plan(plan.id)

    assert report.healthy is True
    assert report.recommended_actions == ["none"]


def test_reconcile_raises_for_missing_trade_plan():
    db = build_db()

    try:
        ExecutionStateMachineService(db).reconcile_trade_plan(999)
    except ValueError as exc:
        assert "Trade plan no encontrado" in str(exc)
    else:
        raise AssertionError("Se esperaba ValueError para trade plan inexistente")


def test_reconcile_warns_when_position_was_closed_but_plan_stays_executed():
    db = build_db()
    plan = seed_trade_plan(db)

    db.add(
        Order(
            trade_plan_id=plan.id,
            venue="binance_futures_testnet",
            external_order_id="ord-fill",
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
            leverage=3,
            status="closed",
            is_testnet=True,
        )
    )
    db.commit()

    report = ExecutionStateMachineService(db).reconcile_trade_plan(plan.id)

    assert report.healthy is False
    assert any(event.event_type == "position_closed_but_plan_still_executed" for event in report.drift_events)
    assert "sync_trade_plan_terminal_status" in report.recommended_actions
