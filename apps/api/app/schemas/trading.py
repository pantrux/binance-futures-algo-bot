from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator


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


class PositionExposure(BaseModel):
    symbol: str
    side: Literal["long", "short"]
    notional_usdt: float = Field(ge=0)
    risk_pct: float = Field(ge=0, le=100)


class PortfolioState(BaseModel):
    positions: list[PositionExposure] = Field(default_factory=list)
    max_portfolio_risk_pct: float = Field(default=5.0, gt=0, le=100)
    max_cluster_risk_pct: float = Field(default=2.5, gt=0, le=100)
    max_symbol_risk_pct: float = Field(default=1.5, gt=0, le=100)
    correlation_guard_enabled: bool = True

    @model_validator(mode="after")
    def validate_risk_limit_hierarchy(self) -> "PortfolioState":
        if self.max_symbol_risk_pct > self.max_cluster_risk_pct:
            raise ValueError(
                f"max_symbol_risk_pct ({self.max_symbol_risk_pct}) no puede superar "
                f"max_cluster_risk_pct ({self.max_cluster_risk_pct})"
            )
        if self.max_cluster_risk_pct > self.max_portfolio_risk_pct:
            raise ValueError(
                f"max_cluster_risk_pct ({self.max_cluster_risk_pct}) no puede superar "
                f"max_portfolio_risk_pct ({self.max_portfolio_risk_pct})"
            )
        return self


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
    portfolio_state: PortfolioState | None = None


class RiskEventDetail(BaseModel):
    event_type: str
    severity: Literal["info", "warning", "critical"]
    message: str
    context: dict[str, Any] = Field(default_factory=dict)


class RiskDecision(BaseModel):
    approved: bool
    max_position_notional: float
    suggested_risk_pct: float
    reason: str
    market_regime: str
    score: float
    regime_confidence: float | None = Field(default=None, ge=0, le=100)
    portfolio_risk_pct_before: float | None = Field(default=None, ge=0, le=100)
    portfolio_risk_pct_after: float | None = Field(default=None, ge=0, le=100)
    cluster_key: str | None = None
    cluster_risk_pct_before: float | None = Field(default=None, ge=0, le=100)
    cluster_risk_pct_after: float | None = Field(default=None, ge=0, le=100)
    symbol_risk_pct_before: float | None = Field(default=None, ge=0, le=100)
    symbol_risk_pct_after: float | None = Field(default=None, ge=0, le=100)
    correlation_multiplier: float | None = Field(default=None, ge=0, le=1.0)
    final_gate_score: float | None = None
    final_gate_passed: bool | None = None
    final_gate_reason: str | None = None
    final_gate_pre_rejected_by_engine: bool | None = None
    triggered_breakers: list[str] = Field(default_factory=list)
    risk_events: list[RiskEventDetail] = Field(default_factory=list)
