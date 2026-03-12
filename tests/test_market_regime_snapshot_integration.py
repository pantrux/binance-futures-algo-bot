from apps.api.app.schemas.indicators import IndicatorSnapshot
from apps.api.app.schemas.signals import SignalSnapshot
from apps.api.app.services.market_regime_service import MarketRegimeService


def test_market_regime_snapshot_uses_provided_snapshots() -> None:
    indicator = IndicatorSnapshot(
        symbol="BTCUSDT",
        timeframe="15m",
        candles_used=200,
        last_candle_close_ms=123,
        ema_9=101.0,
        ema_21=100.0,
        rsi_14=50.0,
        atr_14=1.0,
        momentum_10=0.5,  # USD (valor bruto). Con EMA21=100 => +0.5% (no satura)
    )

    signals = SignalSnapshot(
        symbol="BTCUSDT",
        timeframe="15m",
        last_candle_close_ms=123,
        trend_bias="bullish",
        momentum_bias="neutral",
        volatility_regime="medium",
        ema_spread_pct=1.2,
        atr_pct=1.2,
        rsi_14=50.0,
        momentum_10=0.5,
    )

    service = MarketRegimeService(db=None)  # usamos snapshots inyectados, no toca DB
    snapshot = service.snapshot(
        symbol="BTCUSDT",
        timeframe="15m",
        limit=200,
        indicator_snapshot=indicator,
        signal_snapshot=signals,
    )

    assert snapshot.symbol == "BTCUSDT"
    assert snapshot.timeframe == "15m"
    assert snapshot.last_candle_close_ms == 123
    assert snapshot.regime == "transicion"
    assert 0.0 <= snapshot.regime_confidence <= 100.0
