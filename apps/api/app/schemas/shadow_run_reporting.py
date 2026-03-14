from datetime import datetime

from pydantic import BaseModel, Field


class ShadowRunSymbolSummary(BaseModel):
    symbol: str
    paper_executed_trade_plans: int
    testnet_executed_trade_plans: int
    compared_pairs: int
    unmatched_paper: int
    unmatched_testnet: int
    avg_entry_price_diff_pct: float | None = None
    avg_applied_risk_diff_pct: float | None = None
    avg_max_notional_diff_pct: float | None = None


class ShadowRunSummary(BaseModel):
    evaluated_at: datetime
    window_days: int
    shadow_run_start_at: datetime | None = None
    shadow_run_end_at: datetime | None = None
    shadow_run_duration_days: float = 0.0
    paper_executed_trade_plans: int
    testnet_executed_trade_plans: int
    compared_pairs: int
    unmatched_paper: int
    unmatched_testnet: int
    avg_entry_price_diff_pct: float | None = None
    avg_applied_risk_diff_pct: float | None = None
    avg_max_notional_diff_pct: float | None = None
    testnet_orders_total: int
    testnet_orders_filled: int
    testnet_fill_rate_pct: float | None = None
    avg_testnet_slippage_bps: float | None = None
    critical_risk_events_7d: int
    warning_risk_events_7d: int
    total_risk_events_30d: int
    avg_risk_events_per_day_30d: float
    symbols: list[ShadowRunSymbolSummary] = Field(default_factory=list)
