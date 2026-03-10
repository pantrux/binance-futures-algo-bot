from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.db.base import Base
from apps.api.app.schemas.trade_plan import TradePlanCreateRequest
from apps.api.app.schemas.trading import MarketState, SignalSnapshot
from apps.api.app.services.trade_plan_service import TradePlanService


class DummyOutlineService:
    async def create_trade_plan_document(self, request, risk_summary):
        return {"data": {"url": "/doc/fake-trade-plan"}}


async def _create_plan():
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
        market_state=MarketState(symbol='BTCUSDT', timeframe='15m', volatility_pct=2.4, trend_strength=73, liquidity_score=92),
    )
    return await service.create_trade_plan(payload)


def test_trade_plan_service_persists_and_returns_outline_url():
    import asyncio
    result = asyncio.run(_create_plan())
    assert result.id == 1
    assert result.status == 'approved'
    assert result.outline_url == '/doc/fake-trade-plan'
