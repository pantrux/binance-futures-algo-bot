from pydantic import BaseModel, Field


class ParityPairDiff(BaseModel):
    paper_trade_plan_id: int
    testnet_trade_plan_id: int
    side: str
    entry_price_diff_pct: float
    applied_risk_diff_pct: float
    max_notional_diff_pct: float


class ExecutionParityReport(BaseModel):
    symbol: str
    compared_pairs: int
    unmatched_paper: int
    unmatched_testnet: int
    avg_entry_price_diff_pct: float | None = None
    avg_applied_risk_diff_pct: float | None = None
    avg_max_notional_diff_pct: float | None = None
    pairs: list[ParityPairDiff] = Field(default_factory=list)
