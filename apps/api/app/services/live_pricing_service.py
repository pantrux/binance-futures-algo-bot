from datetime import datetime, timezone
from apps.api.app.services.binance_client import BinanceFuturesClient
from apps.api.app.schemas.live_pricing import DashboardLivePricingResponse, LivePricingItem

class LivePricingService:
    def __init__(self):
        self.client = BinanceFuturesClient()

    async def get_live_pricing(self) -> DashboardLivePricingResponse:
        positions_raw = await self.client.get_position_risk(symbol=None)
        if not positions_raw:
            positions_raw = []

        items = []
        for p in positions_raw:
            amt = float(p.get("positionAmt", 0.0))
            if amt != 0:
                items.append(
                    LivePricingItem(
                        symbol=p.get("symbol", ""),
                        mark_price=float(p.get("markPrice", 0.0)),
                        unrealized_pnl=float(p.get("unRealizedProfit", 0.0)),
                        position_amt=amt,
                    )
                )

        return DashboardLivePricingResponse(
            timestamp=datetime.now(timezone.utc).isoformat(),
            positions=items
        )
