from datetime import datetime, timezone

from apps.api.app.schemas.live_pricing import DashboardLivePricingResponse, LivePricingItem
from apps.api.app.services.binance_client import BinanceFuturesClient


class LivePricingService:
    def __init__(self):
        self.client = BinanceFuturesClient()

    async def get_live_pricing(self, symbols: list[str] | None = None) -> DashboardLivePricingResponse:
        normalized_symbols = sorted({symbol.strip().upper() for symbol in symbols or [] if symbol.strip()})

        positions_raw = await self.client.get_position_risk(symbol=None)
        if not positions_raw:
            positions_raw = []

        if isinstance(positions_raw, dict):
            positions_raw = [positions_raw]

        if normalized_symbols:
            allowed_symbols = set(normalized_symbols)
            positions_raw = [position for position in positions_raw if position.get("symbol") in allowed_symbols]

        items = []
        for position in positions_raw:
            amt = float(position.get("positionAmt", 0.0))
            if amt != 0:
                items.append(
                    LivePricingItem(
                        symbol=position.get("symbol", ""),
                        mark_price=float(position.get("markPrice", 0.0)),
                        unrealized_pnl=float(position.get("unRealizedProfit", 0.0)),
                        position_amt=amt,
                    )
                )

        return DashboardLivePricingResponse(
            timestamp=datetime.now(timezone.utc).isoformat(),
            positions=items,
        )
