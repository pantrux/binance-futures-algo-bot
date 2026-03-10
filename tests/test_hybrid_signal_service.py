import asyncio

from apps.worker.trading_bot.services.hybrid_signal_service import HybridSignalService
from apps.worker.trading_bot.services.demo_signal_service import DemoSignalService


class FakeApiClient:
    def __init__(self, *, snapshot: dict | None = None, market: dict | None = None, error: Exception | None = None) -> None:
        self._snapshot = snapshot
        self._market = market
        self._error = error

    async def get_signal_snapshot(self, symbol: str, timeframe: str = "15m", limit: int = 200) -> dict:
        if self._error:
            raise self._error
        assert symbol
        return dict(self._snapshot or {})

    async def get_market_snapshot(self, symbol: str) -> dict | None:
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
        "atr_pct": 0.01,
        "rsi_14": 55.0,
        "momentum_10": 2.0,
    }
    market = {"mark_price": 50000.0, "volume_24h": 1_000_000.0}
    service = HybridSignalService(api_client=FakeApiClient(snapshot=snapshot, market=market))

    signals, context, thesis, levels, meta = asyncio.run(service.build_signal_pack("BTCUSDT"))

    assert meta.source == "market"
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
