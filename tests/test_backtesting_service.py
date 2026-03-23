from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.db.base import Base
from apps.api.app.schemas.backtesting import BacktestMetrics, BacktestRunRequest, BacktestStrategyParameters
from apps.api.app.services.backtesting_service import BacktestingService
from tests.conftest import seed_walk_forward_candles


def test_backtesting_service_returns_metrics_and_walk_forward_windows():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        seed_walk_forward_candles(db)

        response = BacktestingService(db).run(
            BacktestRunRequest(
                symbol="BTCUSDT",
                timeframe="15m",
                candles_limit=300,
                training_window=120,
                testing_window=60,
                initial_capital=1000.0,
                fee_rate=0.0004,
            )
        )

        assert response.symbol == "BTCUSDT"
        assert response.strategy_name == "ema_rsi_baseline"
        assert response.benchmark_name == "buy_and_hold"
        assert response.candles_used == 300
        assert len(response.candidate_parameters) == 3
        assert response.full_period_strategy.trades_count > 0
        assert response.full_period_strategy.max_drawdown_pct >= 0
        assert response.full_period_strategy_is_in_sample is True
        assert "in-sample" in response.full_period_strategy_note
        assert response.full_period_benchmark.trades_count == 1
        assert response.walk_forward.windows_count >= 2
        assert len(response.walk_forward.windows) == response.walk_forward.windows_count
        assert response.walk_forward.out_of_sample_strategy.trades_count > 0
        assert response.walk_forward.out_of_sample_benchmark.ending_capital > 0
        assert response.walk_forward.out_of_sample_benchmark.trades_count == 1
        first_window = response.walk_forward.windows[0]
        assert first_window.training_start_ms < first_window.training_end_ms
        assert first_window.testing_start_ms < first_window.testing_end_ms
        assert first_window.selected_parameters.ema_fast_period < first_window.selected_parameters.ema_slow_period
    finally:
        db.close()


def test_backtesting_service_raises_when_walk_forward_windows_do_not_fit():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        seed_walk_forward_candles(db, candles=65)

        try:
            BacktestingService(db).run(
                BacktestRunRequest(
                    symbol="BTCUSDT",
                    timeframe="15m",
                    candles_limit=110,
                    training_window=50,
                    testing_window=20,
                )
            )
        except ValueError as exc:
            assert "Candles insuficientes" in str(exc)
        else:
            raise AssertionError("Se esperaba ValueError por ventanas incompatibles")
    finally:
        db.close()


def test_backtesting_service_raises_when_database_has_only_one_possible_oos_window():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        seed_walk_forward_candles(db, candles=170)

        try:
            BacktestingService(db).run(
                BacktestRunRequest(
                    symbol="BTCUSDT",
                    timeframe="15m",
                    candles_limit=240,
                    training_window=120,
                    testing_window=30,
                )
            )
        except ValueError as exc:
            assert "Candles insuficientes" in str(exc)
        else:
            raise AssertionError("Se esperaba ValueError cuando la base solo permite una ventana OOS")
    finally:
        db.close()


def test_backtest_strategy_parameters_reject_inverted_ema_periods():
    try:
        BacktestStrategyParameters(
            ema_fast_period=21,
            ema_slow_period=21,
            rsi_entry_min=55,
            rsi_exit_max=45,
        )
    except ValueError as exc:
        assert "ema_fast_period debe ser menor" in str(exc)
    else:
        raise AssertionError("Se esperaba ValueError para EMA rápida no menor a EMA lenta")


def test_backtest_strategy_parameters_require_entry_rsi_above_exit_rsi():
    try:
        BacktestStrategyParameters(
            ema_fast_period=9,
            ema_slow_period=21,
            rsi_entry_min=45,
            rsi_exit_max=45,
        )
    except ValueError as exc:
        assert "rsi_entry_min debe ser mayor" in str(exc)
    else:
        raise AssertionError("Se esperaba ValueError para umbral RSI de entrada no mayor al de salida")


def test_backtest_run_request_rejects_when_single_window_does_not_fit():
    try:
        BacktestRunRequest(
            symbol="BTCUSDT",
            timeframe="15m",
            candles_limit=170,
            training_window=120,
            testing_window=60,
        )
    except ValueError as exc:
        assert "training_window + testing_window no puede exceder candles_limit" in str(exc)
    else:
        raise AssertionError("Se esperaba ValueError cuando ni siquiera cabe una ventana de testing")


def test_backtest_run_request_requires_at_least_two_walk_forward_windows():
    try:
        BacktestRunRequest(
            symbol="BTCUSDT",
            timeframe="15m",
            candles_limit=180,
            training_window=120,
            testing_window=60,
        )
    except ValueError as exc:
        assert "al menos dos ventanas out-of-sample" in str(exc)
    else:
        raise AssertionError("Se esperaba ValueError para walk-forward degenerado de una sola ventana")


def test_backtest_run_request_rejects_symbols_outside_btc_eth_sol_scope():
    try:
        BacktestRunRequest(
            symbol="XRPUSDT",
            timeframe="15m",
            candles_limit=180,
            training_window=120,
            testing_window=30,
        )
    except ValueError as exc:
        assert "BTCUSDT, ETHUSDT, SOLUSDT" in str(exc)
    else:
        raise AssertionError("Se esperaba ValueError para símbolo fuera del scope permitido")


def test_is_better_result_uses_tolerance_before_drawdown_tiebreak():
    candidate = SimpleNamespace(
        metrics=BacktestMetrics(
            total_return_pct=10.0 + 1e-10,
            win_rate_pct=50.0,
            profit_factor=1.2,
            max_drawdown_pct=8.0,
            trades_count=4,
            ending_capital=1100.0,
        )
    )
    current = SimpleNamespace(
        metrics=BacktestMetrics(
            total_return_pct=10.0,
            win_rate_pct=50.0,
            profit_factor=1.2,
            max_drawdown_pct=9.0,
            trades_count=4,
            ending_capital=1100.0,
        )
    )

    assert BacktestingService._is_better_result(candidate, current) is True


def test_is_better_result_prefers_fewer_trades_when_return_and_drawdown_tie():
    candidate = SimpleNamespace(
        metrics=BacktestMetrics(
            total_return_pct=10.0,
            win_rate_pct=50.0,
            profit_factor=1.2,
            max_drawdown_pct=8.0,
            trades_count=3,
            ending_capital=1100.0,
        )
    )
    current = SimpleNamespace(
        metrics=BacktestMetrics(
            total_return_pct=10.0,
            win_rate_pct=50.0,
            profit_factor=1.2,
            max_drawdown_pct=8.0,
            trades_count=5,
            ending_capital=1100.0,
        )
    )

    assert BacktestingService._is_better_result(candidate, current) is True
