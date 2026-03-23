import asyncio
from datetime import datetime, timezone

from apps.api.app.schemas.live_pricing import DashboardLivePricingResponse, LivePricingItem, LiveQuoteItem
from apps.api.app.services.binance_client import BinanceFuturesClient


class LivePricingService:
    def __init__(self):
        self.client = BinanceFuturesClient()

    async def get_live_pricing(self, symbols: list[str] | None = None) -> DashboardLivePricingResponse:
        normalized_symbols = sorted({symbol.strip().upper() for symbol in symbols or [] if symbol.strip()})

        positions_raw = await self.client.get_position_risk(symbol=None)
        if not positions_raw:
            positions_raw = []

        filtered_positions = positions_raw
        if normalized_symbols:
            allowed_symbols = set(normalized_symbols)
            filtered_positions = [position for position in positions_raw if position.get("symbol") in allowed_symbols]

        items = []
        active_position_symbols: set[str] = set()
        for position in filtered_positions:
            amt = float(position.get("positionAmt", 0.0))
            if amt != 0:
                symbol = position.get("symbol", "")
                active_position_symbols.add(symbol)
                items.append(
                    LivePricingItem(
                        symbol=symbol,
                        mark_price=float(position.get("markPrice", 0.0)),
                        unrealized_pnl=float(position.get("unRealizedProfit", 0.0)),
                        position_amt=amt,
                    )
                )

        quote_symbols = normalized_symbols or sorted(active_position_symbols)
        quotes: list[LiveQuoteItem] = []
        if quote_symbols:
            premium_indexes = await asyncio.gather(
                *(self.client.get_premium_index(symbol) for symbol in quote_symbols),
            )
            quotes = [
                LiveQuoteItem(
                    symbol=str(quote.get("symbol", "")).upper(),
                    mark_price=float(quote.get("markPrice", 0.0)),
                )
                for quote in premium_indexes
            ]

        return DashboardLivePricingResponse(
            timestamp=datetime.now(timezone.utc).isoformat(),
            positions=items,
            quotes=quotes,
        )
