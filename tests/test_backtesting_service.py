from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.db.base import Base
from apps.api.app.db.models import MarketCandle
from apps.api.app.schemas.backtesting import BacktestRunRequest
from apps.api.app.services.backtesting_service import BacktestingService


def _seed_walk_forward_candles(db, symbol: str = "BTCUSDT", timeframe: str = "15m", candles: int = 320) -> None:
    close = 100.0
    phases = [1.4] * 18 + [-1.1] * 12 + [1.8] * 20 + [-1.5] * 14 + [1.0] * 16 + [-0.9] * 10
    for index in range(candles):
        step = phases[index % len(phases)]
        previous_close = close
        close = max(10.0, close + step)
        db.add(MarketCandle(
            symbol=symbol,
            timeframe=timeframe,
            open_time_ms=index * 60_000,
            close_time_ms=(index + 1) * 60_000,
            open_price=previous_close,
            high_price=max(previous_close, close) + 0.8,
            low_price=min(previous_close, close) - 0.8,
            close_price=close,
            volume=100 + index,
            quote_volume=1000 + index,
            trades_count=10 + index,
            source="binance",
        ))
    db.commit()


def test_backtesting_service_returns_metrics_and_walk_forward_windows():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    _seed_walk_forward_candles(db)

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
    assert response.full_period_benchmark.trades_count == 1
    assert response.walk_forward.windows_count >= 2
    assert len(response.walk_forward.windows) == response.walk_forward.windows_count
    assert response.walk_forward.out_of_sample_strategy.trades_count > 0
    assert response.walk_forward.out_of_sample_benchmark.ending_capital > 0
    first_window = response.walk_forward.windows[0]
    assert first_window.training_start_ms < first_window.training_end_ms
    assert first_window.testing_start_ms < first_window.testing_end_ms
    assert first_window.selected_parameters.ema_fast_period < first_window.selected_parameters.ema_slow_period


def test_backtesting_service_raises_when_walk_forward_windows_do_not_fit():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    _seed_walk_forward_candles(db, candles=65)

    try:
        BacktestingService(db).run(
            BacktestRunRequest(
                symbol="BTCUSDT",
                timeframe="15m",
                candles_limit=80,
                training_window=50,
                testing_window=20,
            )
        )
    except ValueError as exc:
        assert "Candles insuficientes" in str(exc)
    else:
        raise AssertionError("Se esperaba ValueError por ventanas incompatibles")
