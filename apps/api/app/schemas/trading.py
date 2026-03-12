from typing import Literal
from pydantic import BaseModel, Field


class SignalSnapshot(BaseModel):
    technical: float = Field(ge=0, le=100)
    fundamental: float = Field(ge=0, le=100)
    sentiment: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=100)


class MarketState(BaseModel):
    symbol: str
    timeframe: str
    volatility_pct: float = Field(ge=0)
    trend_strength: float = Field(ge=0, le=100)
    liquidity_score: float = Field(ge=0, le=100)
    market_regime: str | None = None
    regime_confidence: float | None = Field(default=None, ge=0, le=100)


class TradePlanRequest(BaseModel):
    symbol: str
    side: Literal["long", "short"]
    entry_price: float = Field(gt=0)
    stop_loss: float = Field(gt=0)
    take_profit: float = Field(gt=0)
    capital_usdt: float = Field(gt=0)
    existing_risk_pct: float = Field(ge=0, le=100)
    signals: SignalSnapshot
    market_state: MarketState


class RiskDecision(BaseModel):
    approved: bool
    max_position_notional: float
    suggested_risk_pct: float
    reason: str
    market_regime: str
    score: float
