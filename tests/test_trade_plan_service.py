import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.db.base import Base
from apps.api.app.db.models import RiskEvent, TradePlan
from apps.api.app.schemas.trade_plan import TradePlanCreateRequest
from apps.api.app.schemas.trading import MarketState, PortfolioState, PositionExposure, SignalSnapshot
from apps.api.app.services.trade_plan_service import TradePlanService


class DummyOutlineService:
    async def create_trade_plan_document(self, request, risk_summary):
        return {"data": {"url": "/doc/fake-trade-plan"}}


async def _create_plan(*, market_state: MarketState | None = None):
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    service = TradePlanService(db=db, outline_service=DummyOutlineService())
    payload = TradePlanCreateRequest(
        symbol='BTCUSDT',
        side='long',
        entry_price=50000,
        stop_loss=49750,
        take_profit=50600,
        capital_usdt=1000,
        existing_risk_pct=1.0,
        thesis='Ruptura con confirmación de volumen y régimen favorable.',
        signals=SignalSnapshot(technical=81, fundamental=66, sentiment=74, confidence=79),
        market_state=market_state or MarketState(symbol='BTCUSDT', timeframe='15m', volatility_pct=2.4, trend_strength=73, liquidity_score=92),
        portfolio_state=PortfolioState(
            positions=[
                PositionExposure(symbol='ETHUSDT', side='long', notional_usdt=800, risk_pct=1.0),
            ],
            max_portfolio_risk_pct=5.0,
            max_cluster_risk_pct=3.0,
            max_symbol_risk_pct=2.0,
        ),
    )
    result = await service.create_trade_plan(payload)
    return result, db


def test_trade_plan_service_persists_and_returns_outline_url():
    import asyncio

    result, db = asyncio.run(_create_plan())
    assert result.id == 1
    assert result.status == 'approved'
    assert result.outline_url == '/doc/fake-trade-plan'
    assert result.final_gate_passed is True
    assert result.final_gate_pre_rejected_by_engine is False
    assert result.final_gate_score is not None
    assert result.final_gate_reason == 'Gate final aprobado'

    events = db.query(RiskEvent).filter(RiskEvent.trade_plan_id == result.id).all()
    assert len(events) >= 1
    assert any(event.event_type in {'portfolio_risk_approved', 'correlation_pressure', 'final_gate_pass'} for event in events)

    persisted = db.query(TradePlan).filter(TradePlan.id == result.id).one()
    assert persisted.final_gate_passed is True
    assert persisted.final_gate_reason == 'Gate final aprobado'
    assert json.loads(persisted.triggered_breakers or '[]') == []


def test_trade_plan_service_blocks_when_final_gate_triggers_breaker():
    import asyncio

    high_vol_state = MarketState(symbol='BTCUSDT', timeframe='15m', volatility_pct=6.3, trend_strength=70, liquidity_score=90)
    result, db = asyncio.run(_create_plan(market_state=high_vol_state))

    assert result.status == 'blocked'
    assert result.max_position_notional == 0
    assert result.applied_risk_pct == 0
    assert result.final_gate_passed is False
    assert result.final_gate_pre_rejected_by_engine is False
    assert 'Bloqueado por circuit breaker' in (result.final_gate_reason or '')
    assert 'extreme_volatility' in result.triggered_breakers

    events = db.query(RiskEvent).filter(RiskEvent.trade_plan_id == result.id).all()
    assert any(event.event_type == 'circuit_breaker_extreme_volatility' for event in events)

    persisted = db.query(TradePlan).filter(TradePlan.id == result.id).one()
    assert persisted.final_gate_passed is False
    assert 'extreme_volatility' in json.loads(persisted.triggered_breakers or '[]')


def test_trade_plan_service_marks_pre_rejected_by_engine_in_final_gate_metadata():
    import asyncio

    weak_state = MarketState(symbol='BTCUSDT', timeframe='15m', volatility_pct=1.5, trend_strength=45, liquidity_score=45)

    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    service = TradePlanService(db=db, outline_service=DummyOutlineService())

    payload = TradePlanCreateRequest(
        symbol='BTCUSDT',
        side='long',
        entry_price=50000,
        stop_loss=49750,
        take_profit=50600,
        capital_usdt=1000,
        existing_risk_pct=1.0,
        thesis='Setup débil para validar pre-rechazo.',
        signals=SignalSnapshot(technical=40, fundamental=42, sentiment=44, confidence=43),
        market_state=weak_state,
    )

    result = asyncio.run(service.create_trade_plan(payload))

    assert result.status == 'blocked'
    assert result.final_gate_pre_rejected_by_engine is True
    assert result.final_gate_reason == 'Pre-rechazado por el motor de riesgo'

    persisted = db.query(TradePlan).filter(TradePlan.id == result.id).one()
    assert persisted.final_gate_pre_rejected_by_engine is True
