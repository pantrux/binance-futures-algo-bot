from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.db.base import Base
from apps.api.app.db.models import Position, RiskEvent, TradePlan
from apps.api.app.services.dashboard_service import DashboardService


def test_dashboard_summary_counts_entities():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    db.add(TradePlan(symbol='BTCUSDT', side='long', timeframe='15m', market_regime='tendencia', technical_score=80, fundamental_score=60, sentiment_score=70, confidence_score=75, aggregate_score=74, entry_price=50000, stop_loss=49750, take_profit=50600, capital_usdt=1000, applied_risk_pct=1, max_position_notional=200, thesis='a'*20, status='approved', is_testnet=True))
    db.add(TradePlan(symbol='ETHUSDT', side='long', timeframe='15m', market_regime='tendencia', technical_score=78, fundamental_score=62, sentiment_score=69, confidence_score=72, aggregate_score=72, entry_price=3200, stop_loss=3175, take_profit=3260, capital_usdt=1000, applied_risk_pct=1, max_position_notional=180, thesis='b'*20, status='paper_executed', is_testnet=True))
    db.commit()
    db.add(Position(symbol='ETHUSDT', side='long', quantity=1, entry_price=3200, mark_price=3210, unrealized_pnl=10, leverage=1, status='open', is_testnet=True))
    db.add(RiskEvent(event_type='paper_execution_blocked', severity='warning', message='blocked'))
    db.commit()

    summary = DashboardService(db).summary()
    assert summary.trade_plans_total == 2
    assert summary.approved_trade_plans == 1
    assert summary.paper_executed_trade_plans == 1
    assert summary.open_positions == 1
    assert summary.risk_events_total == 1
