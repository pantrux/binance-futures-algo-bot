from pydantic import BaseModel, Field


class AlertItem(BaseModel):
    severity: str
    category: str
    message: str


class DailyProductionSummary(BaseModel):
    total_trade_plans: int
    approved_trade_plans: int
    blocked_trade_plans: int
    paper_executed_trade_plans: int
    testnet_executed_trade_plans: int
    avg_aggregate_score: float | None = None
    critical_risk_events_24h: int
    warning_risk_events_24h: int


class AlertEvaluationResponse(BaseModel):
    alerts: list[AlertItem] = Field(default_factory=list)
    healthy: bool
