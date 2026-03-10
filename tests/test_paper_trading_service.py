from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.db.base import Base
from apps.api.app.db.models import TradePlan
from apps.api.app.services.paper_trading_service import PaperTradingService


def build_db():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_paper_trading_executes_approved_trade_plan():
    db = build_db()
    plan = TradePlan(
        symbol='BTCUSDT',
        side='long',
        timeframe='15m',
        market_regime='tendencia_fuerte',
        technical_score=80,
        fundamental_score=65,
        sentiment_score=72,
        confidence_score=78,
        aggregate_score=76,
        entry_price=50000,
        stop_loss=49750,
        take_profit=50600,
        capital_usdt=1000,
        applied_risk_pct=1,
        max_position_notional=200,
        thesis='Setup aprobado',
        status='approved',
        is_testnet=True,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    result = PaperTradingService(db).execute_trade_plan(plan.id)
    assert result['executed'] is True
    updated = db.get(TradePlan, plan.id)
    assert updated.status == 'paper_executed'
