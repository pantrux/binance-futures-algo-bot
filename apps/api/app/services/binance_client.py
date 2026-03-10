import httpx

from apps.api.app.core.settings import settings


class BinanceFuturesClient:
    def __init__(self) -> None:
        self.base_url = settings.binance_futures_base_url.rstrip("/")

    async def ping(self) -> dict:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{self.base_url}/fapi/v1/ping")
            response.raise_for_status()
            return {"status": "ok", "base_url": self.base_url}
