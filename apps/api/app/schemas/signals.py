from typing import Literal

from pydantic import BaseModel


class SignalSnapshot(BaseModel):
    symbol: str
    timeframe: str
    last_candle_close_ms: int | None
    trend_bias: Literal['bullish', 'bearish', 'neutral', 'unknown']
    momentum_bias: Literal['bullish', 'bearish', 'neutral', 'unknown']
    volatility_regime: Literal['high', 'medium', 'low', 'unknown']
    ema_spread_pct: float | None
    atr_pct: float | None
    rsi_14: float | None
    momentum_10: float | None
