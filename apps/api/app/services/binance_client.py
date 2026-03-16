import hashlib
import hmac
import math
import time
from urllib.parse import urlencode

import httpx

from apps.api.app.core.settings import settings


class BinanceFuturesClient:
    def __init__(self) -> None:
        self.base_url = settings.binance_futures_base_url.rstrip("/")
        self.api_key = settings.binance_api_key.get_secret_value()
        self.api_secret = settings.binance_api_secret.get_secret_value()
        self._exchange_info_cache: dict | None = None

    def has_credentials(self) -> bool:
        return bool(self.api_key and self.api_secret)

    def ensure_credentials(self) -> None:
        if not self.has_credentials():
            raise RuntimeError("binance_credentials_missing")

    async def ping(self) -> dict:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{self.base_url}/fapi/v1/ping")
            response.raise_for_status()
            return {"status": "ok", "base_url": self.base_url}

    async def exchange_info(self) -> dict:
        if self._exchange_info_cache is not None:
            return self._exchange_info_cache

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(f"{self.base_url}/fapi/v1/exchangeInfo")
            response.raise_for_status()
            payload = response.json()
            self._exchange_info_cache = payload
            return payload

    async def get_symbol_step_size(self, symbol: str) -> float:
        payload = await self.exchange_info()
        symbols = payload.get("symbols", [])
        for item in symbols:
            if item.get("symbol") != symbol:
                continue
            for filt in item.get("filters", []):
                if filt.get("filterType") == "LOT_SIZE":
                    try:
                        step = float(filt.get("stepSize", 0.0))
                        if step > 0:
                            return step
                    except (TypeError, ValueError):
                        break
        raise RuntimeError(f"symbol_step_size_not_found:{symbol}")

    async def get_position_risk(self, symbol: str | None = None, recv_window: int = 5000) -> list[dict] | dict | None:
        self.ensure_credentials()

        params: dict[str, str] = {
            "recvWindow": str(recv_window),
            "timestamp": str(int(time.time() * 1000)),
        }
        params["signature"] = self._sign(params)

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                f"{self.base_url}/fapi/v2/positionRisk",
                params=params,
                headers=self._auth_headers(),
            )
            response.raise_for_status()
            positions = response.json()

        if symbol is None:
            return positions

        for position in positions:
            if position.get("symbol") == symbol:
                return position
        return None

    async def get_symbol_leverage(self, symbol: str, recv_window: int = 5000) -> int:
        position = await self.get_position_risk(symbol, recv_window=recv_window)
        if not position:
            return 1
        try:
            leverage = int(position.get("leverage", 1))
            return leverage if leverage > 0 else 1
        except (TypeError, ValueError):
            return 1

    def _sign(self, params: dict[str, str]) -> str:
        self.ensure_credentials()
        query = urlencode(params)
        return hmac.new(self.api_secret.encode("utf-8"), query.encode("utf-8"), hashlib.sha256).hexdigest()

    def _auth_headers(self) -> dict[str, str]:
        self.ensure_credentials()
        return {"X-MBX-APIKEY": self.api_key}


    async def get_order(
        self,
        *,
        symbol: str,
        order_id: int | None = None,
        client_order_id: str | None = None,
        recv_window: int = 5000,
    ) -> dict:
        self.ensure_credentials()

        params: dict[str, str | int] = {
            "symbol": symbol.upper(),
            "recvWindow": str(recv_window),
            "timestamp": str(int(time.time() * 1000)),
        }
        if order_id is not None:
            params["orderId"] = order_id
        if client_order_id:
            params["origClientOrderId"] = client_order_id
        if "orderId" not in params and "origClientOrderId" not in params:
            raise ValueError("get_order requiere al menos 'order_id' o 'client_order_id'")
        params["signature"] = self._sign({k: str(v) for k, v in params.items()})

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                f"{self.base_url}/fapi/v1/order",
                params=params,
                headers=self._auth_headers(),
            )
            response.raise_for_status()
            return response.json()

    async def get_order_trades(
        self,
        *,
        symbol: str,
        order_id: int,
        recv_window: int = 5000,
    ) -> list[dict]:
        self.ensure_credentials()

        params: dict[str, str | int] = {
            "symbol": symbol.upper(),
            "orderId": order_id,
            "recvWindow": str(recv_window),
            "timestamp": str(int(time.time() * 1000)),
        }
        params["signature"] = self._sign({k: str(v) for k, v in params.items()})

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                f"{self.base_url}/fapi/v1/userTrades",
                params=params,
                headers=self._auth_headers(),
            )
            response.raise_for_status()
            payload = response.json()
        return payload if isinstance(payload, list) else []

    @staticmethod
    def _serialize_quantity(quantity: float) -> str:
        if not math.isfinite(quantity) or quantity <= 0:
            raise ValueError("quantity debe ser un número finito y mayor a cero para serialización")
        quantity_str = f"{quantity:.12f}".rstrip("0").rstrip(".")
        if not quantity_str or quantity_str == "0":
            raise ValueError("quantity inválida para serialización")
        return quantity_str

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

        quantity_str = self._serialize_quantity(quantity)

        params: dict[str, str] = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": quantity_str,
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
