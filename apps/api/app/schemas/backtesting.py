from pydantic import BaseModel, Field, model_validator


class BacktestStrategyParameters(BaseModel):
    ema_fast_period: int = Field(ge=2)
    ema_slow_period: int = Field(ge=3)
    rsi_entry_min: float = Field(ge=0, le=100)
    rsi_exit_max: float = Field(ge=0, le=100)

    @model_validator(mode="after")
    def validate_periods(self) -> "BacktestStrategyParameters":
        if self.ema_fast_period >= self.ema_slow_period:
            raise ValueError("ema_fast_period debe ser menor que ema_slow_period")
        if self.rsi_entry_min <= self.rsi_exit_max:
            raise ValueError("rsi_entry_min debe ser mayor que rsi_exit_max")
        return self


class BacktestMetrics(BaseModel):
    total_return_pct: float
    win_rate_pct: float
    profit_factor: float | None
    max_drawdown_pct: float
    trades_count: int
    ending_capital: float


class BacktestWindowResult(BaseModel):
    window_index: int
    training_start_ms: int
    training_end_ms: int
    testing_start_ms: int
    testing_end_ms: int
    selected_parameters: BacktestStrategyParameters
    in_sample_strategy: BacktestMetrics
    in_sample_benchmark: BacktestMetrics
    out_of_sample_strategy: BacktestMetrics
    out_of_sample_benchmark: BacktestMetrics


class WalkForwardSummary(BaseModel):
    windows_count: int
    in_sample_avg_return_pct: float
    out_of_sample_strategy: BacktestMetrics
    out_of_sample_benchmark: BacktestMetrics
    windows: list[BacktestWindowResult]


class BacktestRunRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    timeframe: str = Field(default="15m", min_length=1, max_length=16)
    candles_limit: int = Field(default=600, ge=50, le=5000)
    training_window: int = Field(default=200, ge=30, le=2000)
    testing_window: int = Field(default=100, ge=10, le=1000)
    initial_capital: float = Field(default=1000.0, gt=0)
    fee_rate: float = Field(default=0.0004, ge=0, le=0.05)

    @model_validator(mode="after")
    def validate_windows(self) -> "BacktestRunRequest":
        if self.training_window >= self.candles_limit:
            raise ValueError("training_window debe ser menor que candles_limit")
        if self.training_window + self.testing_window > self.candles_limit:
            raise ValueError("training_window + testing_window no puede exceder candles_limit")
        if self.training_window + (2 * self.testing_window) > self.candles_limit:
            raise ValueError("Se requieren al menos dos ventanas out-of-sample para ejecutar walk-forward")
        return self


class BacktestRunResponse(BaseModel):
    symbol: str
    timeframe: str
    strategy_name: str
    benchmark_name: str
    candles_used: int
    candidate_parameters: list[BacktestStrategyParameters]
    full_period_strategy: BacktestMetrics
    full_period_benchmark: BacktestMetrics
    walk_forward: WalkForwardSummary
