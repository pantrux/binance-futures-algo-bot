from datetime import datetime
from pydantic import BaseModel


class TradePlanRead(BaseModel):
    id: int
    symbol: str
    side: str
    timeframe: str
    market_regime: str
    aggregate_score: float
    applied_risk_pct: float
    max_position_notional: float
    status: str
    outline_url: str | None
    created_at: datetime
