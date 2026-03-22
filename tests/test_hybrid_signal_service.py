import asyncio

from apps.worker.trading_bot.services.demo_signal_service import DemoSignalService
from apps.worker.trading_bot.services.hybrid_signal_service import HybridSignalService


class FakeApiClient:
    def __init__(
        self,
        *,
        snapshot: dict | None = None,
        market: dict | None = None,
        market_regime: dict | None = None,
        error: Exception | None = None,
        regime_error: Exception | None = None,
        snapshot_after_ingest: dict | None = None,
        market_after_ingest: dict | None = None,
        market_regime_after_ingest: dict | None = None,
    ) -> None:
        self._snapshot = snapshot
        self._market = market
        self._market_regime = market_regime
        self._error = error
        self._regime_error = regime_error
        self._snapshot_after_ingest = snapshot_after_ingest
        self._market_after_ingest = market_after_ingest
        self._market_regime_after_ingest = market_regime_after_ingest
        self.ingest_calls = 0

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
        return None if self._market is None else dict(self._market)

    async def get_market_regime_snapshot(self, symbol: str, timeframe: str = "15m", limit: int = 200) -> dict | None:
        if self._regime_error:
            raise type(self._regime_error)(str(self._regime_error))
        self._raise_error()
        assert symbol
        assert timeframe
        assert limit >= 0
        return None if self._market_regime is None else dict(self._market_regime)

    async def ingest_market(self, symbol: str, timeframe: str = "15m", limit: int = 200) -> dict | None:
        assert symbol
        assert timeframe
        assert limit >= 0
        self.ingest_calls += 1
        if self._snapshot_after_ingest is not None:
            self._snapshot = dict(self._snapshot_after_ingest)
        if self._market_after_ingest is not None:
            self._market = dict(self._market_after_ingest)
        if self._market_regime_after_ingest is not None:
            self._market_regime = dict(self._market_regime_after_ingest)
        return {"ok": True}


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
    regime = {"regime": "tendencia_alcista", "regime_confidence": 78.4}
    service = HybridSignalService(api_client=FakeApiClient(snapshot=snapshot, market=market, market_regime=regime))

    signals, context, thesis, levels, meta = asyncio.run(service.build_signal_pack("BTCUSDT"))

    assert meta.source == "market"
    assert meta.side == "long"
    assert signals.technical > 60
    assert context.volatility_pct > 0
    assert context.market_regime == "tendencia_alcista"
    assert context.regime_confidence == 78.4
    assert levels["stop"] < levels["entry"] < levels["take_profit"]
    assert "market-driven" in thesis


def test_hybrid_ema_rsi_baseline_uses_market_snapshot_for_eth():
    snapshot = {
        "symbol": "ETHUSDT",
        "timeframe": "15m",
        "last_candle_close_ms": 123,
        "trend_bias": "bearish",
        "momentum_bias": "bearish",
        "volatility_regime": "medium",
        "ema_spread_pct": 0.12,
        "atr_pct": 1.0,
        "rsi_14": 55.0,
        "momentum_10": -2.0,
    }
    market = {"mark_price": 2500.0, "volume_24h": 1_000_000.0}
    service = HybridSignalService(
        api_client=FakeApiClient(snapshot=snapshot, market=market),
        strategy_mode="ema_rsi_baseline",
        strategy_symbols=("ETHUSDT",),
    )

    signals, _, thesis, _, meta = asyncio.run(service.build_signal_pack("ETHUSDT"))

    assert meta.source == "market"
    assert meta.side == "long"
    assert signals.technical == 78.0
    assert "Baseline EMA/RSI activo" in thesis


def test_hybrid_ema_rsi_baseline_applies_to_all_symbols_when_allowlist_is_empty():
    snapshot = {
        "symbol": "BTCUSDT",
        "timeframe": "15m",
        "last_candle_close_ms": 123,
        "trend_bias": "bullish",
        "momentum_bias": "bullish",
        "volatility_regime": "medium",
        "ema_spread_pct": 0.18,
        "atr_pct": 1.0,
        "rsi_14": 57.0,
        "momentum_10": 2.0,
    }
    market = {"mark_price": 50000.0, "volume_24h": 1_000_000.0}
    service = HybridSignalService(
        api_client=FakeApiClient(snapshot=snapshot, market=market),
        strategy_mode="ema_rsi_baseline",
        strategy_symbols=(),
    )

    signals, _, thesis, _, meta = asyncio.run(service.build_signal_pack("BTCUSDT"))

    assert meta.source == "market"
    assert meta.side == "long"
    assert signals.technical == 78.0
    assert "Baseline EMA/RSI activo" in thesis


def test_hybrid_ema_rsi_baseline_falls_back_to_demo_when_ema_spread_is_missing():
    snapshot = {
        "symbol": "ETHUSDT",
        "timeframe": "15m",
        "last_candle_close_ms": 123,
        "trend_bias": "bullish",
        "momentum_bias": "bullish",
        "volatility_regime": "medium",
        "ema_spread_pct": "unknown",
        "atr_pct": 1.0,
        "rsi_14": 55.0,
        "momentum_10": 2.0,
    }
    market = {"mark_price": 2500.0, "volume_24h": 1_000_000.0}
    service = HybridSignalService(
        api_client=FakeApiClient(snapshot=snapshot, market=market),
        strategy_mode="ema_rsi_baseline",
        strategy_symbols=("ETHUSDT",),
    )

    _, _, _, _, meta = asyncio.run(service.build_signal_pack("ETHUSDT"))

    assert meta.source == "demo"
    assert meta.reason == "ema_spread_pct_missing"


def test_hybrid_tolerates_regime_endpoint_error_without_falling_to_demo():
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
    service = HybridSignalService(
        api_client=FakeApiClient(snapshot=snapshot, market=market, regime_error=RuntimeError("regime down"))
    )

    _, context, _, _, meta = asyncio.run(service.build_signal_pack("BTCUSDT"))

    assert meta.source == "market"
    assert context.market_regime is None
    assert context.regime_confidence is None


def test_hybrid_clamps_regime_confidence_to_valid_range():
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
    regime = {"regime": "tendencia_alcista", "regime_confidence": 150.0}
    service = HybridSignalService(api_client=FakeApiClient(snapshot=snapshot, market=market, market_regime=regime))

    _, context, _, _, meta = asyncio.run(service.build_signal_pack("BTCUSDT"))

    assert meta.source == "market"
    assert context.regime_confidence == 100.0


def test_hybrid_coerces_invalid_regime_type_to_none():
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
    regime = {"regime": 123, "regime_confidence": 60.0}
    service = HybridSignalService(api_client=FakeApiClient(snapshot=snapshot, market=market, market_regime=regime))

    _, context, _, _, meta = asyncio.run(service.build_signal_pack("BTCUSDT"))

    assert meta.source == "market"
    assert context.market_regime is None
    assert context.regime_confidence is None


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


def test_hybrid_retries_ingest_when_market_snapshot_missing():
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
    market = {"mark_price": 50000.0, "volume_24h": 1_000_000.0}
    api_client = FakeApiClient(snapshot=None, market=None, snapshot_after_ingest=snapshot, market_after_ingest=market)
    service = HybridSignalService(api_client=api_client, demo_service=DemoSignalService())

    _, _, _, _, meta = asyncio.run(service.build_signal_pack("BTCUSDT"))

    assert meta.source == "market"
    assert api_client.ingest_calls == 1


def test_hybrid_retries_ingest_when_snapshot_is_incomplete():
    bad_snapshot = {
        "symbol": "BTCUSDT",
        "timeframe": "15m",
        "last_candle_close_ms": 123,
        "trend_bias": "bullish",
        "momentum_bias": "bullish",
        "volatility_regime": "medium",
        "ema_spread_pct": 0.12,
        "atr_pct": "unknown",
        "rsi_14": 55.0,
        "momentum_10": 2.0,
    }
    good_snapshot = {
        **bad_snapshot,
        "atr_pct": 1.25,
    }
    market = {"mark_price": 50000.0, "volume_24h": 1_000_000.0}
    api_client = FakeApiClient(
        snapshot=bad_snapshot,
        market=market,
        snapshot_after_ingest=good_snapshot,
        market_after_ingest=market,
    )
    service = HybridSignalService(api_client=api_client, demo_service=DemoSignalService())

    _, _, _, _, meta = asyncio.run(service.build_signal_pack("BTCUSDT"))

    assert meta.source == "market"
    assert api_client.ingest_calls == 1


def test_hybrid_uses_market_when_optional_fields_are_unknown():
    snapshot = {
        "symbol": "BTCUSDT",
        "timeframe": "15m",
        "last_candle_close_ms": 123,
        "trend_bias": "bullish",
        "momentum_bias": "bullish",
        "volatility_regime": "medium",
        "ema_spread_pct": "unknown",
        "atr_pct": 1.0,
        "rsi_14": "unknown",
        "momentum_10": "unknown",
    }
    market = {"mark_price": 50000.0, "volume_24h": 1_000_000.0}
    service = HybridSignalService(api_client=FakeApiClient(snapshot=snapshot, market=market), demo_service=DemoSignalService())

    signals, context, thesis, levels, meta = asyncio.run(service.build_signal_pack("BTCUSDT"))

    assert meta.source == "market"
    assert context.trend_strength == 50.0
    assert levels["entry"] > 0
    assert signals.confidence >= 0
    assert thesis


def test_hybrid_falls_back_when_market_snapshot_has_no_price_keys():
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
    market = {"volume_24h": 1_000_000.0}
    service = HybridSignalService(api_client=FakeApiClient(snapshot=snapshot, market=market), demo_service=DemoSignalService())

    _, _, _, _, meta = asyncio.run(service.build_signal_pack("BTCUSDT"))

    assert meta.source == "demo"
    assert meta.reason == "market_snapshot_missing_price"


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
    assert settings.strict_symbol_failures is False
