from typing import Literal

from pydantic import BaseModel, Field


ExecutionDriftType = Literal[
    "missing_filled_order",
    "missing_position_association",
    "position_closed_but_plan_still_executed",
    "multiple_open_positions",
    "executed_with_rejected_orders",
]
ExecutionSeverity = Literal["critical", "warning", "info"]


class ExecutionDriftEvent(BaseModel):
    event_type: ExecutionDriftType
    severity: ExecutionSeverity
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
