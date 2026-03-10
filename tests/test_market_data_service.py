import asyncio
from unittest.mock import AsyncMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.db.base import Base
from apps.api.app.services.binance_market_data_service import BinanceMarketDataService


class MockResponse:
    def __init__(self, payload):
        self._payload = payload
    def raise_for_status(self):
        return None
    def json(self):
        return self._payload


async def _run_ingest():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    service = BinanceMarketDataService(db)

    async def fake_get(url, params=None):
        if 'klines' in url:
            return MockResponse([[1, '100', '110', '90', '105', '12', 2, '1200', 44, 0, 0, 0]])
        if 'ticker/24hr' in url:
            return MockResponse({'lastPrice': '105', 'quoteVolume': '9999'})
        if 'premiumIndex' in url:
            return MockResponse({'markPrice': '104.8', 'indexPrice': '104.5', 'lastFundingRate': '0.0001'})
        if 'openInterest' in url:
            return MockResponse({'openInterest': '12345'})
        raise AssertionError(url)

    with patch('httpx.AsyncClient.get', new=AsyncMock(side_effect=fake_get)):
        result = await service.ingest_symbol('BTCUSDT', '15m', 1)
        candles = service.list_candles('BTCUSDT', '15m', 10)
        snapshot = service.latest_snapshot('BTCUSDT')
        return result, candles, snapshot


def test_market_ingestion_persists_candles_and_snapshot():
    result, candles, snapshot = asyncio.run(_run_ingest())
    assert result.candles_inserted == 1
    assert result.snapshot_saved is True
    assert len(candles) == 1
    assert snapshot is not None
    assert snapshot.symbol == 'BTCUSDT'


async def _run_ingest_http_error():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    service = BinanceMarketDataService(db)

    async def fake_get(url, params=None):
        raise Exception('boom')

    with patch('httpx.AsyncClient.get', new=AsyncMock(side_effect=fake_get)):
        try:
            await service.ingest_symbol('BTCUSDT', '15m', 1)
        except Exception:
            pass
        return db


def test_market_ingestion_rolls_back_session_on_error():
    db = asyncio.run(_run_ingest_http_error())
    assert db.in_transaction() is False
