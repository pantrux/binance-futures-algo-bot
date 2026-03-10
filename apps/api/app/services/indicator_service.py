from statistics import fmean
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.db.models import MarketCandle
from apps.api.app.schemas.indicators import IndicatorSnapshot


class IndicatorService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _load_rows(self, symbol: str, timeframe: str, limit: int) -> list[MarketCandle]:
        return self.db.scalars(
            select(MarketCandle)
            .where(MarketCandle.symbol == symbol, MarketCandle.timeframe == timeframe)
            .order_by(MarketCandle.open_time_ms.desc())
            .limit(limit)
        ).all()[::-1]

    @staticmethod
    def _ema(values: list[float], period: int) -> float | None:
        if len(values) <= period:
            return None
        k = 2 / (period + 1)
        ema = fmean(values[:period])
        for price in values[period:]:
            ema = (price * k) + (ema * (1 - k))
        return round(ema, 6)

    @staticmethod
    def _rsi(values: list[float], period: int = 14) -> float | None:
        if len(values) <= period:
            return None
        gains, losses = [], []
        for i in range(1, len(values)):
            delta = values[i] - values[i - 1]
            gains.append(max(delta, 0))
            losses.append(abs(min(delta, 0)))
        avg_gain = fmean(gains[:period])
        avg_loss = fmean(losses[:period])
        for i in range(period, len(gains)):
            avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
            avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period
        if avg_loss == 0 and avg_gain == 0:
            return 50.0
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return round(100 - (100 / (1 + rs)), 6)

    @staticmethod
    def _atr(highs: list[float], lows: list[float], closes: list[float], period: int = 14) -> float | None:
        if len(closes) <= period:
            return None
        tr = []
        for i in range(1, len(closes)):
            high_low = highs[i] - lows[i]
            high_close = abs(highs[i] - closes[i - 1])
            low_close = abs(lows[i] - closes[i - 1])
            tr.append(max(high_low, high_close, low_close))
        atr = fmean(tr[:period])
        for i in range(period, len(tr)):
            atr = ((atr * (period - 1)) + tr[i]) / period
        return round(atr, 6)

    @staticmethod
    def _momentum(values: list[float], period: int = 10) -> float | None:
        if len(values) <= period:
            return None
        return round(values[-1] - values[-1 - period], 6)

    def snapshot(self, symbol: str, timeframe: str = '15m', limit: int = 200) -> IndicatorSnapshot:
        rows = self._load_rows(symbol, timeframe, limit)
        closes = [r.close_price for r in rows]
        highs = [r.high_price for r in rows]
        lows = [r.low_price for r in rows]
        return IndicatorSnapshot(
            symbol=symbol,
            timeframe=timeframe,
            candles_used=len(closes),
            last_candle_close_ms=rows[-1].close_time_ms if rows else None,
            ema_9=self._ema(closes, 9),
            ema_21=self._ema(closes, 21),
            rsi_14=self._rsi(closes, 14),
            atr_14=self._atr(highs, lows, closes, 14),
            momentum_10=self._momentum(closes, 10),
        )
