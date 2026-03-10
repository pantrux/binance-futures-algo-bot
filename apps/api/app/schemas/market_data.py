from datetime import datetime
from pydantic import BaseModel


class MarketCandleRead(BaseModel):
    symbol: str
    timeframe: str
    open_time_ms: int
    close_time_ms: int
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    quote_volume: float
    trades_count: int


class MarketSnapshotRead(BaseModel):
    symbol: str
    last_price: float
    mark_price: float
    index_price: float
    open_interest: float
    funding_rate: float
    volume_24h: float
    captured_at: datetime


class MarketIngestionResponse(BaseModel):
    symbol: str
    timeframe: str
    candles_inserted: int
    snapshot_saved: bool
