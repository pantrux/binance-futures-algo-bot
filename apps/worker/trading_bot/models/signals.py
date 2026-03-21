from dataclasses import dataclass


@dataclass
class SignalPack:
    technical: float
    fundamental: float
    sentiment: float
    confidence: float


@dataclass
class MarketContext:
    symbol: str
    timeframe: str
    volatility_pct: float
    trend_strength: float
    liquidity_score: float
    last_candle_close_ms: int | None = None
    market_regime: str | None = None
    regime_confidence: float | None = None
