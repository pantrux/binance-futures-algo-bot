from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.api.deps import get_db
from apps.api.app.db.base import Base
from apps.api.app.db.models import MarketCandle
from apps.api.app.main import app


def _make_test_db():
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return TestingSessionLocal


def _override_db(testing_session_local):
    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    return override_get_db


def test_indicator_endpoint_returns_400_when_candles_are_insufficient():
    TestingSessionLocal = _make_test_db()
    app.dependency_overrides[get_db] = _override_db(TestingSessionLocal)

    db = TestingSessionLocal()
    try:
        for i in range(1, 22):
            close = 100.0 + i
            db.add(MarketCandle(
                symbol='ETHUSDT',
                timeframe='15m',
                open_time_ms=i,
                close_time_ms=i + 1,
                open_price=close - 0.3,
                high_price=close + 0.7,
                low_price=close - 0.9,
                close_price=close,
                volume=50 + i,
                quote_volume=500 + i,
                trades_count=5 + i,
                source='binance',
            ))
        db.commit()
    finally:
        db.close()

    try:
        client = TestClient(app)
        response = client.get('/indicators/ETHUSDT', params={'timeframe': '15m', 'limit': 22})

        assert response.status_code == 400
        assert 'Candles insuficientes' in response.json()['detail']
    finally:
        app.dependency_overrides.clear()


def test_indicator_endpoint_returns_snapshot_when_candles_are_sufficient():
    TestingSessionLocal = _make_test_db()
    app.dependency_overrides[get_db] = _override_db(TestingSessionLocal)

    db = TestingSessionLocal()
    try:
        pattern = [1.8, -1.1, 2.2, -0.9, 1.4, -1.6, 2.0, -0.7]
        close = 100.0
        for i in range(1, 70):
            step = pattern[i % len(pattern)]
            close = max(5.0, close + step)
            db.add(MarketCandle(
                symbol='BTCUSDT',
                timeframe='15m',
                open_time_ms=i,
                close_time_ms=i + 1,
                open_price=close - 0.5,
                high_price=close + 0.8,
                low_price=close - 1.2,
                close_price=close,
                volume=100 + i,
                quote_volume=1000 + i,
                trades_count=10 + i,
                source='binance',
            ))
        db.commit()
    finally:
        db.close()

    try:
        client = TestClient(app)
        response = client.get('/indicators/BTCUSDT', params={'timeframe': '15m', 'limit': 69})

        assert response.status_code == 200
        payload = response.json()
        assert payload['symbol'] == 'BTCUSDT'
        assert payload['timeframe'] == '15m'
        assert payload['candles_used'] == 69
        assert payload['last_candle_close_ms'] == 70
        assert payload['ema_9'] is not None
        assert payload['ema_21'] is not None
        assert payload['rsi_14'] is not None
        assert payload['atr_14'] is not None
        assert payload['momentum_10'] is not None
    finally:
        app.dependency_overrides.clear()
