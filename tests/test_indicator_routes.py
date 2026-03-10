from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.api.deps import get_db
from apps.api.app.db.base import Base
from apps.api.app.db.models import MarketCandle
from apps.api.app.main import app


def test_indicator_endpoint_returns_400_when_candles_are_insufficient():
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

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

    client = TestClient(app)
    response = client.get('/indicators/ETHUSDT', params={'timeframe': '15m', 'limit': 22})

    assert response.status_code == 400
    assert 'Candles insuficientes' in response.json()['detail']

    app.dependency_overrides.clear()
