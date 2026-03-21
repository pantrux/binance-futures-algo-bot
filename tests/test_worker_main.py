import asyncio
from types import SimpleNamespace

from apps.worker.main import process_symbol, process_symbol_cycle, run_worker_cycle
from apps.worker.trading_bot.services.hybrid_signal_service import HybridSignalResult


class FakeSignalService:
    def __init__(self, *, source: str, reason: str = "ok", timeframe: str = "15m", last_candle_close_ms: int = 123) -> None:
        self.source = source
        self.reason = reason
        self.timeframe = timeframe
        self.last_candle_close_ms = last_candle_close_ms

    async def build_signal_pack(self, symbol: str):
        signals = SimpleNamespace(technical=80, fundamental=60, sentiment=70, confidence=75)
        context = SimpleNamespace(
            symbol=symbol,
            timeframe=self.timeframe,
            volatility_pct=2.0,
            trend_strength=70,
            liquidity_score=90,
            last_candle_close_ms=self.last_candle_close_ms,
            market_regime="tendencia_alcista",
            regime_confidence=68,
        )
        thesis = "setup test"
        levels = {"entry": 100.0, "stop": 95.0, "take_profit": 110.0}
        meta = HybridSignalResult(source=self.source, reason=self.reason, side="long")
        return signals, context, thesis, levels, meta


class FakeApiClient:
    def __init__(self) -> None:
        self.paper_trade_calls: list[int] = []
        self.created_payloads: list[dict] = []

    async def create_trade_plan(self, payload: dict) -> dict:
        self.created_payloads.append(payload)
        return {"id": 123, "status": "approved"}

    async def execute_paper_trade(self, trade_plan_id: int) -> dict:
        self.paper_trade_calls.append(trade_plan_id)
        return {"executed": True, "trade_plan_id": trade_plan_id}


class FakeTestnetRouter:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    async def execute_trade_plan(self, *, symbol: str, trade_plan: dict) -> dict:
        self.calls.append((symbol, trade_plan))
        return {"executed": True, "trade_plan_id": trade_plan.get("id")}


def build_settings(*, paper_trading: bool, testnet_fallback_to_paper: bool = True):
    return SimpleNamespace(
        seed_capital_usdt=1000.0,
        paper_trading=paper_trading,
        testnet_fallback_to_paper=testnet_fallback_to_paper,
        strict_symbol_failures=False,
        symbols=("BTCUSDT", "ETHUSDT", "SOLUSDT"),
    )


def test_process_symbol_blocks_testnet_execution_for_demo_source_and_falls_back_to_paper():
    settings = build_settings(paper_trading=False, testnet_fallback_to_paper=True)
    signal_service = FakeSignalService(source="demo", reason="snapshot_incompleto")
    api_client = FakeApiClient()
    router = FakeTestnetRouter()

    result = asyncio.run(
        process_symbol(
            symbol="BTCUSDT",
            settings=settings,
            signal_service=signal_service,
            api_client=api_client,
            testnet_router=router,
        )
    )

    assert result is True
    assert router.calls == []
    assert api_client.paper_trade_calls == [123]


def test_process_symbol_allows_testnet_execution_for_market_source():
    settings = build_settings(paper_trading=False, testnet_fallback_to_paper=True)
    signal_service = FakeSignalService(source="market", reason="ok")
    api_client = FakeApiClient()
    router = FakeTestnetRouter()

    result = asyncio.run(
        process_symbol(
            symbol="BTCUSDT",
            settings=settings,
            signal_service=signal_service,
            api_client=api_client,
            testnet_router=router,
        )
    )

    assert result is True
    assert len(router.calls) == 1
    assert api_client.paper_trade_calls == []


def test_process_symbol_skips_non_market_testnet_without_paper_fallback():
    settings = build_settings(paper_trading=False, testnet_fallback_to_paper=False)
    signal_service = FakeSignalService(source="demo", reason="snapshot_incompleto")
    api_client = FakeApiClient()
    router = FakeTestnetRouter()

    result = asyncio.run(
        process_symbol(
            symbol="ETHUSDT",
            settings=settings,
            signal_service=signal_service,
            api_client=api_client,
            testnet_router=router,
        )
    )

    assert result is True
    assert router.calls == []
    assert api_client.paper_trade_calls == []


def test_process_symbol_cycle_skips_duplicate_candle_for_same_symbol_and_timeframe():
    settings = build_settings(paper_trading=True)
    signal_service = FakeSignalService(source="market", timeframe="15m", last_candle_close_ms=123)
    api_client = FakeApiClient()
    router = FakeTestnetRouter()
    processed_candles = {("BTCUSDT", "15m"): 123}

    result = asyncio.run(
        process_symbol_cycle(
            symbol="BTCUSDT",
            timeframe="15m",
            settings=settings,
            signal_service=signal_service,
            api_client=api_client,
            testnet_router=router,
            processed_candles=processed_candles,
        )
    )

    assert result.success is True
    assert result.skipped_duplicate is True
    assert api_client.created_payloads == []
    assert api_client.paper_trade_calls == []


def test_run_worker_cycle_processes_distinct_timeframes_independently():
    settings = build_settings(paper_trading=True)
    settings.symbols = ("BTCUSDT",)
    signal_services = {
        "15m": FakeSignalService(source="market", timeframe="15m", last_candle_close_ms=123),
        "1h": FakeSignalService(source="market", timeframe="1h", last_candle_close_ms=123),
    }
    api_client = FakeApiClient()
    router = FakeTestnetRouter()

    successes, failures, duplicates = asyncio.run(
        run_worker_cycle(
            settings=settings,
            signal_services=signal_services,
            api_client=api_client,
            testnet_router=router,
            processed_candles={},
        )
    )

    assert (successes, failures, duplicates) == (2, 0, 0)
    assert len(api_client.created_payloads) == 2
    assert api_client.created_payloads[0]["market_state"]["timeframe"] != api_client.created_payloads[1]["market_state"]["timeframe"]
