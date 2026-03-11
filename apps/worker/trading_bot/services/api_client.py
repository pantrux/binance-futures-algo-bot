import httpx


class TradingBotApiClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def create_trade_plan(self, payload: dict) -> dict:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(f"{self.base_url}/trade-plans", json=payload)
            response.raise_for_status()
            return response.json()

    async def execute_paper_trade(self, trade_plan_id: int) -> dict:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(f"{self.base_url}/paper-trading/execute/{trade_plan_id}")
            response.raise_for_status()
            return response.json()

    async def get_signal_snapshot(self, symbol: str, timeframe: str = "15m", limit: int = 200) -> dict | None:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                f"{self.base_url}/signals/{symbol}",
                params={"timeframe": timeframe, "limit": limit},
            )
            if response.status_code in (400, 404):
                return None
            response.raise_for_status()
            return response.json()

    async def get_market_snapshot(self, symbol: str) -> dict | None:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(f"{self.base_url}/market/snapshot/{symbol}")
            if response.status_code in (400, 404):
                return None
            response.raise_for_status()
            return response.json()
