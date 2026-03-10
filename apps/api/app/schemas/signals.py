from pydantic import BaseModel


class SignalSnapshot(BaseModel):
    symbol: str
    timeframe: str
    last_candle_close_ms: int | None
    trend_bias: str
    momentum_bias: str
    volatility_regime: str
    ema_spread_pct: float | None
    atr_pct: float | None
    rsi_14: float | None
    momentum_10: float | None
