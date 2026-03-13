from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.api.routes import run_backtesting
from apps.api.app.db.base import Base
from apps.api.app.schemas.backtesting import BacktestRunRequest
from tests.conftest import seed_walk_forward_candles


def _make_db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return TestingSessionLocal()


def test_backtesting_route_returns_backtest_with_walk_forward_summary():
    db = _make_db()
    try:
        seed_walk_forward_candles(db)
        response = run_backtesting(
            BacktestRunRequest(
                symbol="BTCUSDT",
                timeframe="15m",
                candles_limit=300,
                training_window=120,
                testing_window=60,
                initial_capital=1000,
                fee_rate=0.0004,
            ),
            db,
        )

        assert response.symbol == "BTCUSDT"
        assert response.strategy_name == "ema_rsi_baseline"
        assert response.benchmark_name == "buy_and_hold"
        assert response.full_period_strategy.trades_count > 0
        assert response.full_period_benchmark.trades_count == 1
        assert response.walk_forward.windows_count >= 2
        assert len(response.walk_forward.windows) == response.walk_forward.windows_count
    finally:
        db.close()


def test_backtesting_route_returns_404_when_symbol_has_no_candles():
    db = _make_db()
    try:
        try:
            run_backtesting(
                BacktestRunRequest(
                    symbol="ETHUSDT",
                    timeframe="15m",
                    candles_limit=200,
                    training_window=120,
                    testing_window=60,
                ),
                db,
            )
        except HTTPException as exc:
            assert exc.status_code == 404
            assert "No hay candles" in exc.detail
        else:
            raise AssertionError("Se esperaba HTTPException para símbolo sin candles")
    finally:
        db.close()


def test_backtesting_route_returns_400_when_windows_do_not_fit_available_candles():
    db = _make_db()
    try:
        seed_walk_forward_candles(db, candles=65)
        try:
            run_backtesting(
                BacktestRunRequest(
                    symbol="BTCUSDT",
                    timeframe="15m",
                    candles_limit=80,
                    training_window=50,
                    testing_window=20,
                ),
                db,
            )
        except HTTPException as exc:
            assert exc.status_code == 400
            assert "Candles insuficientes" in exc.detail
        else:
            raise AssertionError("Se esperaba HTTPException 400 por candles insuficientes")
    finally:
        db.close()
