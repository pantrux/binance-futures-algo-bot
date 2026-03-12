from pydantic import BaseModel, Field

from apps.api.app.schemas.trading import MarketState, PortfolioState, SignalSnapshot


class TradePlanCreateRequest(BaseModel):
    symbol: str
    side: str
    entry_price: float = Field(gt=0)
    stop_loss: float = Field(gt=0)
    take_profit: float = Field(gt=0)
    capital_usdt: float = Field(gt=0)
    existing_risk_pct: float = Field(ge=0, le=100)
    thesis: str = Field(min_length=10)
    signals: SignalSnapshot
    market_state: MarketState
    portfolio_state: PortfolioState | None = None


class TradePlanCreateResponse(BaseModel):
    id: int
    status: str
    outline_url: str | None = None
    market_regime: str
    aggregate_score: float
    applied_risk_pct: float
    max_position_notional: float
