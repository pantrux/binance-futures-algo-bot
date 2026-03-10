from apps.api.app.schemas.indicators import IndicatorSnapshot
from apps.api.app.schemas.signals import SignalSnapshot
from apps.api.app.services.indicator_service import IndicatorService
from sqlalchemy.orm import Session


class SignalService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.indicators = IndicatorService(db)

    @staticmethod
    def _trend_bias(ema_9: float | None, ema_21: float | None) -> str:
        if ema_9 is None or ema_21 is None:
            return 'unknown'
        if ema_9 > ema_21:
            return 'bullish'
        if ema_9 < ema_21:
            return 'bearish'
        return 'neutral'

    @staticmethod
    def _momentum_bias(rsi_14: float | None, momentum_10: float | None) -> str:
        if rsi_14 is None or momentum_10 is None:
            return 'unknown'
        if rsi_14 >= 55 and momentum_10 > 0:
            return 'bullish'
        if rsi_14 <= 45 and momentum_10 < 0:
            return 'bearish'
        return 'neutral'

    @staticmethod
    def _volatility_regime(atr_pct: float | None) -> str:
        if atr_pct is None:
            return 'unknown'
        if atr_pct >= 2.5:
            return 'high'
        if atr_pct >= 1.0:
            return 'medium'
        return 'low'

    def snapshot(self, symbol: str, timeframe: str = '15m', limit: int = 200, indicator_snapshot: IndicatorSnapshot | None = None) -> SignalSnapshot:
        indicator_snapshot = indicator_snapshot or self.indicators.snapshot(symbol=symbol, timeframe=timeframe, limit=limit)
        ema_spread_pct = None
        atr_pct = None
        if indicator_snapshot.ema_9 is not None and indicator_snapshot.ema_21 not in (None, 0):
            ema_spread_pct = round(((indicator_snapshot.ema_9 - indicator_snapshot.ema_21) / indicator_snapshot.ema_21) * 100, 6)
        if indicator_snapshot.atr_14 is not None and indicator_snapshot.ema_21 not in (None, 0):
            atr_pct = round((indicator_snapshot.atr_14 / indicator_snapshot.ema_21) * 100, 6)

        return SignalSnapshot(
            symbol=symbol,
            timeframe=timeframe,
            last_candle_close_ms=indicator_snapshot.last_candle_close_ms,
            trend_bias=self._trend_bias(indicator_snapshot.ema_9, indicator_snapshot.ema_21),
            momentum_bias=self._momentum_bias(indicator_snapshot.rsi_14, indicator_snapshot.momentum_10),
            volatility_regime=self._volatility_regime(atr_pct),
            ema_spread_pct=ema_spread_pct,
            atr_pct=atr_pct,
            rsi_14=indicator_snapshot.rsi_14,
            momentum_10=indicator_snapshot.momentum_10,
        )
