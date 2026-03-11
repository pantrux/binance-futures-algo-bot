import asyncio

from apps.worker.trading_bot.services.demo_signal_service import DemoSignalService
from apps.worker.trading_bot.services.hybrid_signal_service import HybridSignalService


class FakeApiClient:
    def __init__(self, *, snapshot: dict | None = None, market: dict | None = None, error: Exception | None = None) -> None:
        self._snapshot = snapshot
        self._market = market
        self._error = error

    def _raise_error(self) -> None:
        if self._error:
            raise type(self._error)(str(self._error))

    async def get_signal_snapshot(self, symbol: str, timeframe: str = "15m", limit: int = 200) -> dict | None:
        self._raise_error()
        assert symbol
        return None if self._snapshot is None else dict(self._snapshot)

    async def get_market_snapshot(self, symbol: str) -> dict | None:
        self._raise_error()
        assert symbol
        return self._market


def test_hybrid_uses_market_when_snapshot_is_usable():
    snapshot = {
        "symbol": "BTCUSDT",
        "timeframe": "15m",
        "last_candle_close_ms": 123,
        "trend_bias": "bullish",
        "momentum_bias": "bullish",
        "volatility_regime": "medium",
        "ema_spread_pct": 0.12,
        "atr_pct": 1.0,
        "rsi_14": 55.0,
        "momentum_10": 2.0,
    }
    market = {"mark_price": 50000.0, "volume_24h": 1_000_000.0}
    service = HybridSignalService(api_client=FakeApiClient(snapshot=snapshot, market=market))

    signals, context, thesis, levels, meta = asyncio.run(service.build_signal_pack("BTCUSDT"))

    assert meta.source == "market"
    assert meta.side == "long"
    assert signals.technical > 60
    assert context.volatility_pct > 0
    assert levels["stop"] < levels["entry"] < levels["take_profit"]
    assert "market-driven" in thesis


def test_hybrid_falls_back_to_demo_on_api_error():
    demo = DemoSignalService()
    demo_signals, demo_context, demo_thesis, demo_levels = demo.build_signal_pack("ETHUSDT")
    service = HybridSignalService(api_client=FakeApiClient(error=RuntimeError("boom")), demo_service=demo)

    signals, context, thesis, levels, meta = asyncio.run(service.build_signal_pack("ETHUSDT"))

    assert meta.source == "demo"
    assert "boom" in meta.reason
    assert signals == demo_signals
    assert context == demo_context
    assert thesis == demo_thesis
    assert levels == demo_levels


def test_hybrid_falls_back_when_market_snapshot_missing():
    snapshot = {
        "symbol": "BTCUSDT",
        "timeframe": "15m",
        "last_candle_close_ms": 123,
        "trend_bias": "bullish",
        "momentum_bias": "bullish",
        "volatility_regime": "medium",
        "ema_spread_pct": 0.12,
        "atr_pct": 2.0,
        "rsi_14": 55.0,
        "momentum_10": 2.0,
    }
    service = HybridSignalService(api_client=FakeApiClient(snapshot=snapshot, market=None), demo_service=DemoSignalService())

    _, _, _, _, meta = asyncio.run(service.build_signal_pack("BTCUSDT"))

    assert meta.source == "demo"
    assert meta.reason == "market_snapshot_missing"


def test_levels_from_atr_accepts_percentage_values():
    service = HybridSignalService(api_client=FakeApiClient(snapshot=None, market=None), demo_service=DemoSignalService())
    levels = service._levels_from_atr(100.0, 2.5)

    assert levels["stop"] > 0
    assert levels["stop"] < levels["entry"]
    assert levels["take_profit"] > 100.0


def test_hybrid_uses_short_side_and_inverted_levels_for_bearish_market():
    snapshot = {
        "symbol": "BTCUSDT",
        "timeframe": "15m",
        "last_candle_close_ms": 123,
        "trend_bias": "bearish",
        "momentum_bias": "bearish",
        "volatility_regime": "medium",
        "ema_spread_pct": -0.12,
        "atr_pct": 1.0,
        "rsi_14": 40.0,
        "momentum_10": -2.0,
    }
    market = {"mark_price": 50000.0, "volume_24h": 1_000_000.0}
    service = HybridSignalService(api_client=FakeApiClient(snapshot=snapshot, market=market))

    signals, context, thesis, levels, meta = asyncio.run(service.build_signal_pack("BTCUSDT"))

    assert meta.source == "market"
    assert meta.side == "short"
    assert levels["take_profit"] < levels["entry"] < levels["stop"]
    assert signals.technical < 60


def test_normalize_atr_fraction_accepts_sub_one_percent_values():
    service = HybridSignalService(api_client=FakeApiClient(snapshot=None, market=None), demo_service=DemoSignalService())
    assert abs(service._normalize_atr_fraction(0.8) - 0.008) < 1e-12
    assert abs(service._normalize_atr_fraction(0.01) - 0.0001) < 1e-12


def test_worker_settings_expose_signal_snapshot_config():
    from apps.worker.trading_bot.config.settings import WorkerSettings

    settings = WorkerSettings()
    assert settings.default_signal_timeframe == "15m"
    assert settings.signal_snapshot_limit == 200
