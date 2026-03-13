from pydantic import BaseModel, Field


class ExecutionDriftEvent(BaseModel):
    event_type: str
    severity: str
    message: str


class ReconciliationReport(BaseModel):
    trade_plan_id: int
    trade_plan_status: str
    healthy: bool
    order_count: int
    open_position_count: int
    filled_order_count: int
    drift_events: list[ExecutionDriftEvent] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
