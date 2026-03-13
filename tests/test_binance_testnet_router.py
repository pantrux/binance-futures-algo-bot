import asyncio

from apps.worker.trading_bot.services.binance_testnet_router import BinanceTestnetRouter


class FakeApiClient:
    async def execute_testnet_trade(self, trade_plan_id: int) -> dict:
        return {
            "executed": True,
            "order_id": 11,
            "position_id": 22,
            "external_order_id": f"oid-{trade_plan_id}",
            "reason": None,
        }


class FailingApiClient:
    async def execute_testnet_trade(self, trade_plan_id: int) -> dict:
        raise RuntimeError(f"boom-{trade_plan_id}")


def test_testnet_router_blocks_on_global_kill_switch():
    router = BinanceTestnetRouter(
        api_client=FakeApiClient(),
        execution_enabled=True,
        global_kill_switch=True,
        kill_switch_symbols=(),
    )

    out = asyncio.run(router.execute_trade_plan(symbol="BTCUSDT", trade_plan={"id": 10, "status": "approved"}))

    assert out["executed"] is False
    assert out["reason"] == "global_kill_switch_enabled"


def test_testnet_router_blocks_on_symbol_kill_switch():
    router = BinanceTestnetRouter(
        api_client=FakeApiClient(),
        execution_enabled=True,
        global_kill_switch=False,
        kill_switch_symbols=("BTCUSDT",),
    )

    out = asyncio.run(router.execute_trade_plan(symbol="BTCUSDT", trade_plan={"id": 10, "status": "approved"}))

    assert out["executed"] is False
    assert out["reason"] == "symbol_kill_switch_enabled"


def test_testnet_router_executes_when_preflight_passes():
    router = BinanceTestnetRouter(
        api_client=FakeApiClient(),
        execution_enabled=True,
        global_kill_switch=False,
        kill_switch_symbols=(),
    )

    out = asyncio.run(router.execute_trade_plan(symbol="ETHUSDT", trade_plan={"id": 33, "status": "approved"}))

    assert out["executed"] is True
    assert out["external_order_id"] == "oid-33"


def test_testnet_router_returns_structured_error_when_api_client_raises():
    router = BinanceTestnetRouter(
        api_client=FailingApiClient(),
        execution_enabled=True,
        global_kill_switch=False,
        kill_switch_symbols=(),
    )

    out = asyncio.run(router.execute_trade_plan(symbol="ETHUSDT", trade_plan={"id": 33, "status": "approved"}))

    assert out["executed"] is False
    assert out["reason"] == "testnet_router_api_error"
    assert "boom-33" in out["error"]
