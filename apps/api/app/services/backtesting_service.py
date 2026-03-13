from dataclasses import dataclass
from statistics import fmean

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.db.models import MarketCandle
from apps.api.app.schemas.backtesting import (
    BacktestMetrics,
    BacktestRunRequest,
    BacktestRunResponse,
    BacktestStrategyParameters,
    BacktestWindowResult,
    WalkForwardSummary,
)


@dataclass(frozen=True)
class _SimulationOutput:
    metrics: BacktestMetrics
    ending_capital: float
    trade_pnls: list[float]
    equity_curve: list[float]


class BacktestingService:
    STRATEGY_NAME = "ema_rsi_baseline"
    BENCHMARK_NAME = "buy_and_hold"
    CANDIDATE_PARAMETERS = (
        BacktestStrategyParameters(ema_fast_period=7, ema_slow_period=21, rsi_entry_min=52, rsi_exit_max=47),
        BacktestStrategyParameters(ema_fast_period=9, ema_slow_period=21, rsi_entry_min=55, rsi_exit_max=45),
        BacktestStrategyParameters(ema_fast_period=12, ema_slow_period=30, rsi_entry_min=58, rsi_exit_max=42),
    )

    def __init__(self, db: Session) -> None:
        self.db = db

    def run(self, payload: BacktestRunRequest) -> BacktestRunResponse:
        rows = self._load_rows(payload.symbol.upper(), payload.timeframe, payload.candles_limit)
        if not rows:
            raise ValueError(f"No hay candles para {payload.symbol.upper()} en timeframe {payload.timeframe}")
        if len(rows) < payload.training_window + payload.testing_window:
            raise ValueError(
                "Candles insuficientes para ejecutar walk-forward con las ventanas solicitadas"
            )

        closes = [row.close_price for row in rows]
        full_period_strategy = self._select_best_simulation(
            closes=closes,
            initial_capital=payload.initial_capital,
            fee_rate=payload.fee_rate,
        ).metrics
        full_period_benchmark = self._simulate_buy_and_hold(
            closes=closes,
            initial_capital=payload.initial_capital,
            fee_rate=payload.fee_rate,
        ).metrics

        windows: list[BacktestWindowResult] = []
        in_sample_returns: list[float] = []
        oos_trade_pnls: list[float] = []
        oos_equity_curve: list[float] = [payload.initial_capital]
        oos_capital = payload.initial_capital
        full_oos_benchmark_closes: list[float] = []

        last_window_start = len(rows) - (payload.training_window + payload.testing_window)
        window_index = 1
        max_warmup = max(parameter.ema_slow_period for parameter in self.CANDIDATE_PARAMETERS)
        for start in range(0, last_window_start + 1, payload.testing_window):
            training_rows = rows[start : start + payload.training_window]
            testing_rows = rows[start + payload.training_window : start + payload.training_window + payload.testing_window]
            if len(testing_rows) < payload.testing_window:
                continue

            training_closes = [row.close_price for row in training_rows]
            testing_closes = [row.close_price for row in testing_rows]

            selected_parameters, in_sample_strategy = self._select_best_simulation_with_parameters(
                closes=training_closes,
                initial_capital=payload.initial_capital,
                fee_rate=payload.fee_rate,
            )
            in_sample_returns.append(in_sample_strategy.metrics.total_return_pct)
            in_sample_benchmark = self._simulate_buy_and_hold(
                closes=training_closes,
                initial_capital=payload.initial_capital,
                fee_rate=payload.fee_rate,
            )

            warmup_start = max(0, start + payload.training_window - max_warmup)
            testing_with_warmup_rows = rows[warmup_start : start + payload.training_window + payload.testing_window]
            testing_with_warmup_closes = [row.close_price for row in testing_with_warmup_rows]
            warmup_offset = len(testing_with_warmup_closes) - len(testing_closes)
            window_start_capital = oos_capital
            out_of_sample_strategy = self._simulate_strategy(
                closes=testing_with_warmup_closes,
                parameters=selected_parameters,
                initial_capital=window_start_capital,
                fee_rate=payload.fee_rate,
                start_index=warmup_offset,
            )
            oos_capital = out_of_sample_strategy.ending_capital
            oos_trade_pnls.extend(out_of_sample_strategy.trade_pnls)
            oos_equity_curve.extend(out_of_sample_strategy.equity_curve[1:])

            full_oos_benchmark_closes.extend(testing_closes)
            out_of_sample_benchmark = self._simulate_buy_and_hold(
                closes=testing_closes,
                initial_capital=window_start_capital,
                fee_rate=payload.fee_rate,
            )

            windows.append(
                BacktestWindowResult(
                    window_index=window_index,
                    training_start_ms=training_rows[0].open_time_ms,
                    training_end_ms=training_rows[-1].close_time_ms,
                    testing_start_ms=testing_rows[0].open_time_ms,
                    testing_end_ms=testing_rows[-1].close_time_ms,
                    selected_parameters=selected_parameters,
                    in_sample_strategy=in_sample_strategy.metrics,
                    in_sample_benchmark=in_sample_benchmark.metrics,
                    out_of_sample_strategy=out_of_sample_strategy.metrics,
                    out_of_sample_benchmark=out_of_sample_benchmark.metrics,
                )
            )
            window_index += 1

        full_oos_benchmark = self._simulate_buy_and_hold(
            closes=full_oos_benchmark_closes,
            initial_capital=payload.initial_capital,
            fee_rate=payload.fee_rate,
        )

        walk_forward = WalkForwardSummary(
            windows_count=len(windows),
            in_sample_avg_return_pct=round(fmean(in_sample_returns), 6) if in_sample_returns else 0.0,
            out_of_sample_strategy=self._build_metrics(
                initial_capital=payload.initial_capital,
                ending_capital=oos_capital,
                trade_pnls=oos_trade_pnls,
                equity_curve=oos_equity_curve,
            ),
            out_of_sample_benchmark=full_oos_benchmark.metrics,
            windows=windows,
        )

        return BacktestRunResponse(
            symbol=payload.symbol.upper(),
            timeframe=payload.timeframe,
            strategy_name=self.STRATEGY_NAME,
            benchmark_name=self.BENCHMARK_NAME,
            candles_used=len(rows),
            candidate_parameters=list(self.CANDIDATE_PARAMETERS),
            full_period_strategy=full_period_strategy,
            full_period_benchmark=full_period_benchmark,
            walk_forward=walk_forward,
        )

    def _load_rows(self, symbol: str, timeframe: str, limit: int) -> list[MarketCandle]:
        return self.db.scalars(
            select(MarketCandle)
            .where(MarketCandle.symbol == symbol, MarketCandle.timeframe == timeframe)
            .order_by(MarketCandle.open_time_ms.desc())
            .limit(limit)
        ).all()[::-1]

    @staticmethod
    def _ema_series(values: list[float], period: int) -> list[float | None]:
        result: list[float | None] = [None] * len(values)
        if len(values) < period:
            return result
        multiplier = 2 / (period + 1)
        ema = fmean(values[:period])
        result[period - 1] = round(ema, 6)
        for index in range(period, len(values)):
            ema = (values[index] * multiplier) + (ema * (1 - multiplier))
            result[index] = round(ema, 6)
        return result

    @staticmethod
    def _rsi_series(values: list[float], period: int = 14) -> list[float | None]:
        result: list[float | None] = [None] * len(values)
        if len(values) <= period:
            return result

        gains: list[float] = []
        losses: list[float] = []
        for index in range(1, len(values)):
            delta = values[index] - values[index - 1]
            gains.append(max(delta, 0.0))
            losses.append(abs(min(delta, 0.0)))

        avg_gain = fmean(gains[:period])
        avg_loss = fmean(losses[:period])
        result[period] = BacktestingService._compute_rsi(avg_gain, avg_loss)
        for index in range(period, len(gains)):
            avg_gain = ((avg_gain * (period - 1)) + gains[index]) / period
            avg_loss = ((avg_loss * (period - 1)) + losses[index]) / period
            result[index + 1] = BacktestingService._compute_rsi(avg_gain, avg_loss)
        return result

    @staticmethod
    def _compute_rsi(avg_gain: float, avg_loss: float) -> float:
        if avg_loss == 0 and avg_gain == 0:
            return 50.0
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return round(100 - (100 / (1 + rs)), 6)

    def _select_best_simulation(
        self,
        closes: list[float],
        initial_capital: float,
        fee_rate: float,
    ) -> _SimulationOutput:
        return self._select_best_simulation_with_parameters(
            closes=closes,
            initial_capital=initial_capital,
            fee_rate=fee_rate,
        )[1]

    def _select_best_simulation_with_parameters(
        self,
        closes: list[float],
        initial_capital: float,
        fee_rate: float,
    ) -> tuple[BacktestStrategyParameters, _SimulationOutput]:
        best_parameters = self.CANDIDATE_PARAMETERS[0]
        best_result = self._simulate_strategy(
            closes=closes,
            parameters=best_parameters,
            initial_capital=initial_capital,
            fee_rate=fee_rate,
        )
        for parameters in self.CANDIDATE_PARAMETERS[1:]:
            candidate_result = self._simulate_strategy(
                closes=closes,
                parameters=parameters,
                initial_capital=initial_capital,
                fee_rate=fee_rate,
            )
            if self._is_better_result(candidate_result, best_result):
                best_parameters = parameters
                best_result = candidate_result
        return best_parameters, best_result

    @staticmethod
    def _is_better_result(candidate: _SimulationOutput, current: _SimulationOutput) -> bool:
        if candidate.metrics.total_return_pct != current.metrics.total_return_pct:
            return candidate.metrics.total_return_pct > current.metrics.total_return_pct
        if candidate.metrics.max_drawdown_pct != current.metrics.max_drawdown_pct:
            return candidate.metrics.max_drawdown_pct < current.metrics.max_drawdown_pct
        return candidate.metrics.trades_count > current.metrics.trades_count

    def _simulate_strategy(
        self,
        closes: list[float],
        parameters: BacktestStrategyParameters,
        initial_capital: float,
        fee_rate: float,
        start_index: int = 0,
    ) -> _SimulationOutput:
        ema_fast = self._ema_series(closes, parameters.ema_fast_period)
        ema_slow = self._ema_series(closes, parameters.ema_slow_period)
        rsi = self._rsi_series(closes, 14)

        entries = [False] * len(closes)
        exits = [False] * len(closes)
        for index in range(max(1, start_index), len(closes)):
            current_fast = ema_fast[index]
            current_slow = ema_slow[index]
            previous_fast = ema_fast[index - 1]
            previous_slow = ema_slow[index - 1]
            current_rsi = rsi[index]
            if None in (current_fast, current_slow, previous_fast, previous_slow, current_rsi):
                continue
            crossed_up = current_fast > current_slow and previous_fast <= previous_slow
            crossed_down = current_fast < current_slow and previous_fast >= previous_slow
            entries[index] = crossed_up and current_rsi >= parameters.rsi_entry_min
            exits[index] = crossed_down or current_rsi <= parameters.rsi_exit_max

        return self._simulate_from_signals(
            closes=closes,
            entries=entries,
            exits=exits,
            initial_capital=initial_capital,
            fee_rate=fee_rate,
            start_index=start_index,
        )

    def _simulate_buy_and_hold(
        self,
        closes: list[float],
        initial_capital: float,
        fee_rate: float,
    ) -> _SimulationOutput:
        entries = [False] * len(closes)
        exits = [False] * len(closes)
        if closes:
            entries[0] = True
            exits[-1] = True
        return self._simulate_from_signals(
            closes=closes,
            entries=entries,
            exits=exits,
            initial_capital=initial_capital,
            fee_rate=fee_rate,
        )

    def _simulate_from_signals(
        self,
        closes: list[float],
        entries: list[bool],
        exits: list[bool],
        initial_capital: float,
        fee_rate: float,
        start_index: int = 0,
    ) -> _SimulationOutput:
        cash = initial_capital
        units = 0.0
        entry_cost = 0.0
        trade_pnls: list[float] = []
        equity_curve = [initial_capital]

        for index, price in enumerate(closes):
            if index < start_index:
                continue

            if entries[index] and units == 0.0 and cash > 0:
                units = (cash * (1 - fee_rate)) / price
                entry_cost = cash
                cash = 0.0
            elif exits[index] and units > 0.0:
                cash = units * price * (1 - fee_rate)
                trade_pnls.append(cash - entry_cost)
                units = 0.0
                entry_cost = 0.0

            equity = cash if units == 0.0 else units * price
            equity_curve.append(round(equity, 6))

        if units > 0.0:
            final_cash = units * closes[-1] * (1 - fee_rate)
            trade_pnls.append(final_cash - entry_cost)
            cash = final_cash
            equity_curve[-1] = round(cash, 6)

        metrics = self._build_metrics(
            initial_capital=initial_capital,
            ending_capital=cash,
            trade_pnls=trade_pnls,
            equity_curve=equity_curve,
        )
        return _SimulationOutput(
            metrics=metrics,
            ending_capital=round(cash, 6),
            trade_pnls=trade_pnls,
            equity_curve=equity_curve,
        )

    @staticmethod
    def _build_metrics(
        initial_capital: float,
        ending_capital: float,
        trade_pnls: list[float],
        equity_curve: list[float],
    ) -> BacktestMetrics:
        wins = [pnl for pnl in trade_pnls if pnl > 0]
        losses = [pnl for pnl in trade_pnls if pnl < 0]
        profit_factor = round(sum(wins) / abs(sum(losses)), 6) if losses else None

        win_rate_pct = round((len(wins) / len(trade_pnls)) * 100, 6) if trade_pnls else 0.0
        max_drawdown_pct = BacktestingService._max_drawdown_pct(equity_curve)
        total_return_pct = round(((ending_capital / initial_capital) - 1) * 100, 6) if initial_capital else 0.0
        return BacktestMetrics(
            total_return_pct=total_return_pct,
            win_rate_pct=win_rate_pct,
            profit_factor=profit_factor,
            max_drawdown_pct=max_drawdown_pct,
            trades_count=len(trade_pnls),
            ending_capital=round(ending_capital, 6),
        )

    @staticmethod
    def _max_drawdown_pct(equity_curve: list[float]) -> float:
        peak = equity_curve[0] if equity_curve else 0.0
        max_drawdown = 0.0
        for equity in equity_curve:
            peak = max(peak, equity)
            if peak == 0:
                continue
            drawdown = ((peak - equity) / peak) * 100
            max_drawdown = max(max_drawdown, drawdown)
        return round(max_drawdown, 6)
