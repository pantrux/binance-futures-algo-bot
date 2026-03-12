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
    market_regime: str | None = None
    regime_confidence: float | None = None
