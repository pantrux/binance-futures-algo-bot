from typing import Literal

from pydantic import BaseModel, Field


class MarketRegimeSnapshot(BaseModel):
    symbol: str
    timeframe: str
    last_candle_close_ms: int | None
    regime: Literal[
        "tendencia_alcista",
        "tendencia_bajista",
        "rango_lateral",
        "transicion",
        "alta_volatilidad",
        "unknown",
    ]
    trend_bias: Literal["bullish", "bearish", "neutral", "unknown"]
    momentum_bias: Literal["bullish", "bearish", "neutral", "unknown"]
    volatility_regime: Literal["high", "medium", "low", "unknown"]
    trend_strength: float = Field(ge=0, le=100)
    volatility_score: float = Field(ge=0, le=100)
    momentum_score: float = Field(ge=0, le=100)
    regime_confidence: float = Field(ge=0, le=100)
    ema_spread_pct: float | None
    atr_pct: float | None
    rsi_14: float | None
    momentum_10: float | None
