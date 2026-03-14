from datetime import datetime

from pydantic import BaseModel, Field


class DashboardCommandCenterSummary(BaseModel):
    trade_plans_total: int
    approved_trade_plans: int
    paper_executed_trade_plans: int
    testnet_executed_trade_plans: int
    open_positions: int
    risk_events_total: int


class DashboardCommandCenterTradePlan(BaseModel):
    id: int
    symbol: str
    side: str
    market_regime: str
    aggregate_score: float
    applied_risk_pct: float
    max_position_notional: float
    status: str
    created_at: datetime


class DashboardCommandCenterOrder(BaseModel):
    id: int
    trade_plan_id: int
    symbol: str
    side: str
    venue: str
    status: str
    price: float
    quantity: float
    executed_quantity: float
    created_at: datetime


class DashboardCommandCenterPosition(BaseModel):
    id: int
    trade_plan_id: int | None = None
    symbol: str
    side: str
    quantity: float
    entry_price: float
    mark_price: float
    unrealized_pnl: float
    leverage: int
    status: str
    opened_at: datetime


class DashboardCommandCenterRiskEvent(BaseModel):
    id: int
    trade_plan_id: int | None = None
    event_type: str
    severity: str
    message: str
    created_at: datetime


class DashboardCommandCenterShadowRun(BaseModel):
    shadow_run_duration_days: float
    paper_executed_trade_plans: int
    testnet_executed_trade_plans: int
    compared_pairs: int
    unmatched_paper: int
    unmatched_testnet: int
    testnet_orders_total: int
    testnet_orders_filled: int
    testnet_fill_rate_pct: float | None = None
    avg_testnet_slippage_bps: float | None = None
    critical_risk_events_7d: int
    warning_risk_events_7d: int


class DashboardCommandCenterResponse(BaseModel):
    generated_at: datetime
    summary: DashboardCommandCenterSummary
    shadow_run: DashboardCommandCenterShadowRun
    recent_trade_plans: list[DashboardCommandCenterTradePlan] = Field(default_factory=list)
    recent_orders: list[DashboardCommandCenterOrder] = Field(default_factory=list)
    open_positions: list[DashboardCommandCenterPosition] = Field(default_factory=list)
    recent_risk_events: list[DashboardCommandCenterRiskEvent] = Field(default_factory=list)
