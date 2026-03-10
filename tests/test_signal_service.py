from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.db.base import Base
from apps.api.app.db.models import MarketCandle
from apps.api.app.services.signal_service import SignalService


def test_signal_snapshot_computes_biases_and_features():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    pattern = [1.8, -1.1, 2.2, -0.9, 1.4, -1.6, 2.0, -0.7]
    close = 100.0
    for i in range(1, 70):
        step = pattern[i % len(pattern)]
        close = max(5.0, close + step)
        db.add(MarketCandle(
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
    db.commit()

    snapshot = SignalService(db).snapshot('BTCUSDT', '15m', 69)
    assert snapshot.symbol == 'BTCUSDT'
    assert snapshot.last_candle_close_ms == 70
    assert snapshot.trend_bias in {'bullish', 'bearish', 'neutral'}
    assert snapshot.momentum_bias in {'bullish', 'bearish', 'neutral'}
    assert snapshot.volatility_regime in {'low', 'medium', 'high'}
    assert snapshot.ema_spread_pct is not None
    assert snapshot.atr_pct is not None
    assert snapshot.rsi_14 is not None
    assert 0 < snapshot.rsi_14 < 100
    assert snapshot.momentum_10 is not None
    assert abs(snapshot.momentum_10) > 0


def test_signal_service_static_methods_handle_missing_inputs():
    assert SignalService._trend_bias(None, 100.0) == 'unknown'
    assert SignalService._momentum_bias(None, 1.0) == 'unknown'
    assert SignalService._volatility_regime(None) == 'unknown'
