from dataclasses import dataclass

from apps.worker.trading_bot.services.api_client import TradingBotApiClient


@dataclass
class TestnetRouteDecision:
    allowed: bool
    reason: str | None = None


class BinanceTestnetRouter:
    def __init__(
        self,
        api_client: TradingBotApiClient,
        *,
        execution_enabled: bool,
        global_kill_switch: bool,
        kill_switch_symbols: tuple[str, ...],
    ) -> None:
        self.api_client = api_client
        self.execution_enabled = execution_enabled
        self.global_kill_switch = global_kill_switch
        self.kill_switch_symbols = {symbol.upper() for symbol in kill_switch_symbols}

    def preflight(self, *, symbol: str, trade_plan: dict) -> TestnetRouteDecision:
        if not self.execution_enabled:
            return TestnetRouteDecision(allowed=False, reason="testnet_execution_disabled")

        if self.global_kill_switch:
            return TestnetRouteDecision(allowed=False, reason="global_kill_switch_enabled")

        if symbol.upper() in self.kill_switch_symbols:
            return TestnetRouteDecision(allowed=False, reason="symbol_kill_switch_enabled")

        if trade_plan.get("status") != "approved":
            return TestnetRouteDecision(allowed=False, reason="trade_plan_not_approved")

        if not trade_plan.get("id"):
            return TestnetRouteDecision(allowed=False, reason="trade_plan_missing_id")

        return TestnetRouteDecision(allowed=True)

    async def execute_trade_plan(self, *, symbol: str, trade_plan: dict) -> dict:
        decision = self.preflight(symbol=symbol, trade_plan=trade_plan)
        if not decision.allowed:
            return {"executed": False, "reason": decision.reason}

        trade_plan_id = int(trade_plan["id"])
        return await self.api_client.execute_testnet_trade(trade_plan_id)
