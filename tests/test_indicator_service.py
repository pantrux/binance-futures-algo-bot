from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.db.base import Base
from apps.api.app.db.models import MarketCandle
from apps.api.app.services.indicator_service import IndicatorService


def test_indicator_snapshot_computes_values():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    candles = []
    base = 100.0
    pattern = [1.8, -1.1, 2.2, -0.9, 1.4, -1.6, 2.0, -0.7]
    for i in range(1, 70):
        step = pattern[i % len(pattern)]
        close = base + step * i
        candles.append(MarketCandle(
            symbol='BTCUSDT',
            timeframe='15m',
            open_time_ms=i,
            close_time_ms=i + 1,
            open_price=close - 0.5,
            high_price=close + 0.8,
            low_price=close - 1.2,
            close_price=close,
            volume=100 + i,
            quote_volume=1000 + i,
            trades_count=10 + i,
            source='binance',
        ))
    db.add_all(candles)
    db.commit()

    snapshot = IndicatorService(db).snapshot('BTCUSDT', '15m', 100)
    assert snapshot.candles_used == 69
    assert snapshot.ema_9 is not None
    assert snapshot.ema_21 is not None
    assert snapshot.rsi_14 is not None
    assert 0 < snapshot.rsi_14 < 100
    assert snapshot.atr_14 is not None
    assert snapshot.momentum_10 is not None
