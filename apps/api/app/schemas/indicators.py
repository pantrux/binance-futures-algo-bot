from pydantic import BaseModel


class IndicatorSnapshot(BaseModel):
    symbol: str
    timeframe: str
    candles_used: int
    last_candle_close_ms: int | None
    ema_9: float | None
    ema_21: float | None
    rsi_14: float | None
    atr_14: float | None
    momentum_10: float | None
