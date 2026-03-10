import asyncio

import httpx
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from apps.api.app.core.settings import settings
from apps.api.app.db.models import MarketCandle, MarketSnapshot
from apps.api.app.schemas.market_data import MarketCandleRead, MarketIngestionResponse, MarketSnapshotRead


class BinanceMarketDataService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.base_url = settings.binance_futures_base_url.rstrip('/')

    async def ingest_symbol(self, symbol: str, timeframe: str = '15m', limit: int = 50) -> MarketIngestionResponse:
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                results = await asyncio.gather(
                    client.get(f'{self.base_url}/fapi/v1/klines', params={'symbol': symbol, 'interval': timeframe, 'limit': limit}),
                    client.get(f'{self.base_url}/fapi/v1/ticker/24hr', params={'symbol': symbol}),
                    client.get(f'{self.base_url}/fapi/v1/premiumIndex', params={'symbol': symbol}),
                    client.get(f'{self.base_url}/fapi/v1/openInterest', params={'symbol': symbol}),
                    return_exceptions=True,
                )
                errors = [result for result in results if isinstance(result, BaseException)]
                if errors:
                    if len(errors) == 1:
                        raise errors[0]
                    raise BaseExceptionGroup('fallos en gather de Binance', errors)
                klines_resp, ticker_resp, premium_resp, oi_resp = results
                klines_resp.raise_for_status()
                ticker_resp.raise_for_status()
                premium_resp.raise_for_status()
                oi_resp.raise_for_status()

            klines = klines_resp.json()
            ticker = ticker_resp.json()
            premium = premium_resp.json()
            open_interest = oi_resp.json()

            candles_inserted = 0
            existing_open_times = set(self.db.scalars(select(MarketCandle.open_time_ms).where(MarketCandle.symbol == symbol, MarketCandle.timeframe == timeframe)).all())
            for row in klines:
                open_time = int(row[0])
                if open_time in existing_open_times:
                    continue
                candle = MarketCandle(
                    symbol=symbol,
                    timeframe=timeframe,
                    open_time_ms=open_time,
                    close_time_ms=int(row[6]),
                    open_price=float(row[1]),
                    high_price=float(row[2]),
                    low_price=float(row[3]),
                    close_price=float(row[4]),
                    volume=float(row[5]),
                    quote_volume=float(row[7]),
                    trades_count=int(row[8]),
                    source='binance',
                )
                self.db.add(candle)
                candles_inserted += 1

            snapshot = MarketSnapshot(
                symbol=symbol,
                last_price=float(ticker['lastPrice']),
                mark_price=float(premium['markPrice']),
                index_price=float(premium['indexPrice']),
                open_interest=float(open_interest['openInterest']),
                funding_rate=float(premium.get('lastFundingRate', 0) or 0),
                volume_24h=float(ticker['quoteVolume']),
                source='binance',
            )
            self.db.add(snapshot)
            self.db.commit()
            return MarketIngestionResponse(symbol=symbol, timeframe=timeframe, candles_inserted=candles_inserted, snapshot_saved=True)
        except Exception:
            self.db.rollback()
            raise

    def list_candles(self, symbol: str, timeframe: str = '15m', limit: int = 50) -> list[MarketCandleRead]:
        rows = self.db.scalars(select(MarketCandle).where(MarketCandle.symbol == symbol, MarketCandle.timeframe == timeframe).order_by(MarketCandle.open_time_ms.desc()).limit(limit)).all()
        return [MarketCandleRead(
            symbol=r.symbol, timeframe=r.timeframe, open_time_ms=r.open_time_ms, close_time_ms=r.close_time_ms,
            open_price=r.open_price, high_price=r.high_price, low_price=r.low_price, close_price=r.close_price,
            volume=r.volume, quote_volume=r.quote_volume, trades_count=r.trades_count
        ) for r in rows]

    def latest_snapshot(self, symbol: str) -> MarketSnapshotRead | None:
        row = self.db.scalar(select(MarketSnapshot).where(MarketSnapshot.symbol == symbol).order_by(MarketSnapshot.captured_at.desc()).limit(1))
        if not row:
            return None
        return MarketSnapshotRead(
            symbol=row.symbol,
            last_price=row.last_price,
            mark_price=row.mark_price,
            index_price=row.index_price,
            open_interest=row.open_interest,
            funding_rate=row.funding_rate,
            volume_24h=row.volume_24h,
            captured_at=row.captured_at,
        )
