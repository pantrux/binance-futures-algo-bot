from pydantic import BaseModel


class DashboardSummary(BaseModel):
    trade_plans_total: int
    approved_trade_plans: int
    paper_executed_trade_plans: int
    open_positions: int
    risk_events_total: int
