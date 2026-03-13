import hashlib
import hmac
import time
from urllib.parse import urlencode

import httpx

from apps.api.app.core.settings import settings


class BinanceFuturesClient:
    def __init__(self) -> None:
        self.base_url = settings.binance_futures_base_url.rstrip("/")
        self.api_key = settings.binance_api_key.get_secret_value()
        self.api_secret = settings.binance_api_secret.get_secret_value()

    async def ping(self) -> dict:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{self.base_url}/fapi/v1/ping")
            response.raise_for_status()
            return {"status": "ok", "base_url": self.base_url}

    def _sign(self, params: dict[str, str]) -> str:
        if not self.api_secret:
            raise RuntimeError("binance_api_secret no configurado")
        query = urlencode(params)
        return hmac.new(self.api_secret.encode("utf-8"), query.encode("utf-8"), hashlib.sha256).hexdigest()

    def _auth_headers(self) -> dict[str, str]:
        if not self.api_key:
            raise RuntimeError("binance_api_key no configurado")
        return {"X-MBX-APIKEY": self.api_key}

    async def place_market_order(
        self,
        *,
        symbol: str,
        side: str,
        quantity: float,
        client_order_id: str,
        recv_window: int = 5000,
    ) -> dict:
        if quantity <= 0:
            raise ValueError("quantity debe ser mayor a cero")

        params: dict[str, str] = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": f"{quantity:.6f}",
            "newClientOrderId": client_order_id,
            "recvWindow": str(recv_window),
            "timestamp": str(int(time.time() * 1000)),
        }
        params["signature"] = self._sign(params)

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                f"{self.base_url}/fapi/v1/order",
                params=params,
                headers=self._auth_headers(),
            )
            response.raise_for_status()
            return response.json()
