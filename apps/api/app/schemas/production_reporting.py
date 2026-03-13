from typing import Literal

from pydantic import BaseModel, Field

AlertSeverity = Literal["critical", "warning"]
AlertCategory = Literal["risk_events", "trade_plan_conversion", "execution_mode", "signal_quality"]


class AlertItem(BaseModel):
    severity: AlertSeverity
    category: AlertCategory
    message: str


class DailyProductionSummary(BaseModel):
    total_trade_plans: int
    approved_trade_plans: int
    blocked_trade_plans: int
    paper_executed_trade_plans: int
    testnet_executed_trade_plans: int
    approved_trade_plans_24h: int
    blocked_trade_plans_24h: int
    paper_executed_trade_plans_24h: int
    testnet_executed_trade_plans_24h: int
    avg_aggregate_score: float | None = None
    critical_risk_events_24h: int
    warning_risk_events_24h: int


class AlertEvaluationResponse(BaseModel):
    alerts: list[AlertItem] = Field(default_factory=list)
    healthy: bool
