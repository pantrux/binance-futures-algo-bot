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


class DashboardCommandCenterOperationSnapshot(BaseModel):
    trade_plan_id: int
    symbol: str
    side: str
    status: str
    market_regime: str
    aggregate_score: float
    entry_price: float
    stop_loss: float
    take_profit: float
    applied_risk_pct: float
    max_position_notional: float
    latest_order_id: int | None = None
    latest_order_status: str | None = None
    latest_order_venue: str | None = None
    latest_order_price: float | None = None
    latest_order_executed_quantity: float | None = None
    latest_position_id: int | None = None
    latest_position_status: str | None = None
    latest_position_quantity: float | None = None
    latest_position_entry_price: float | None = None
    latest_position_mark_price: float | None = None
    latest_position_unrealized_pnl: float | None = None
    reconciliation_healthy: bool
    reconciliation_primary_severity: str | None = None
    reconciliation_primary_event: str | None = None
    reconciliation_primary_message: str | None = None
    risk_event_count: int = 0
    latest_risk_severity: str | None = None
    latest_risk_event_type: str | None = None
    latest_risk_message: str | None = None
    created_at: datetime


class DashboardCommandCenterResponse(BaseModel):
    generated_at: datetime
    summary: DashboardCommandCenterSummary
    shadow_run: DashboardCommandCenterShadowRun
    operation_snapshots: list[DashboardCommandCenterOperationSnapshot] = Field(default_factory=list)
    recent_trade_plans: list[DashboardCommandCenterTradePlan] = Field(default_factory=list)
    recent_orders: list[DashboardCommandCenterOrder] = Field(default_factory=list)
    open_positions: list[DashboardCommandCenterPosition] = Field(default_factory=list)
    recent_risk_events: list[DashboardCommandCenterRiskEvent] = Field(default_factory=list)
