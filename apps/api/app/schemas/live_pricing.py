from pydantic import BaseModel
from typing import List


class LivePricingItem(BaseModel):
    symbol: str
    mark_price: float
    unrealized_pnl: float
    position_amt: float


class LiveQuoteItem(BaseModel):
    symbol: str
    mark_price: float


class DashboardLivePricingResponse(BaseModel):
    timestamp: str
    positions: List[LivePricingItem]
    quotes: List[LiveQuoteItem]
