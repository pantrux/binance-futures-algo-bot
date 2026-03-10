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
