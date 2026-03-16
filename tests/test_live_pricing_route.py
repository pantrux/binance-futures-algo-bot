from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import pytest
from apps.api.app.main import app

client = TestClient(app)

@patch("apps.api.app.services.binance_client.BinanceFuturesClient.get_position_risk", new_callable=AsyncMock)
def test_dashboard_live_pricing(mock_get_position_risk):
    mock_get_position_risk.return_value = [
        {
            "symbol": "BTCUSDT",
            "positionAmt": "1.5",
            "markPrice": "95000.5",
            "unRealizedProfit": "120.5",
        },
        {
            "symbol": "ETHUSDT",
            "positionAmt": "0.0",  # should be filtered out
            "markPrice": "3000.0",
            "unRealizedProfit": "0.0",
        }
    ]
    response = client.get("/dashboard/live-pricing")
    assert response.status_code == 200
    data = response.json()
    assert "timestamp" in data
    assert "positions" in data
    assert len(data["positions"]) == 1
    assert data["positions"][0]["symbol"] == "BTCUSDT"
    assert data["positions"][0]["position_amt"] == 1.5
    assert data["positions"][0]["mark_price"] == 95000.5
    assert data["positions"][0]["unrealized_pnl"] == 120.5
