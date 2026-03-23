from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from apps.api.app.main import app

client = TestClient(app)


@patch("apps.api.app.services.binance_client.BinanceFuturesClient.get_premium_index", new_callable=AsyncMock)
@patch("apps.api.app.services.binance_client.BinanceFuturesClient.get_position_risk", new_callable=AsyncMock)
def test_dashboard_live_pricing(mock_get_position_risk, mock_get_premium_index):
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
    mock_get_premium_index.return_value = {
        "symbol": "BTCUSDT",
        "markPrice": "95001.0",
    }

    response = client.get("/dashboard/live-pricing")
    assert response.status_code == 200
    data = response.json()
    assert "timestamp" in data
    assert "positions" in data
    assert "quotes" in data
    assert len(data["positions"]) == 1
    assert data["positions"][0]["symbol"] == "BTCUSDT"
    assert data["positions"][0]["position_amt"] == 1.5
    assert data["positions"][0]["mark_price"] == 95000.5
    assert data["positions"][0]["unrealized_pnl"] == 120.5
    assert data["quotes"] == [{"symbol": "BTCUSDT", "mark_price": 95001.0}]
    mock_get_position_risk.assert_awaited_once_with(symbol=None)
    mock_get_premium_index.assert_awaited_once_with("BTCUSDT")


@patch("apps.api.app.services.binance_client.BinanceFuturesClient.get_premium_index", new_callable=AsyncMock)
@patch("apps.api.app.services.binance_client.BinanceFuturesClient.get_position_risk", new_callable=AsyncMock)
def test_dashboard_live_pricing_filters_requested_symbols(mock_get_position_risk, mock_get_premium_index):
    mock_get_position_risk.return_value = [
        {
            "symbol": "BTCUSDT",
            "positionAmt": "1.5",
            "markPrice": "95000.5",
            "unRealizedProfit": "120.5",
        },
        {
            "symbol": "SOLUSDT",
            "positionAmt": "2.0",
            "markPrice": "180.2",
            "unRealizedProfit": "42.0",
        },
    ]
    mock_get_premium_index.side_effect = [
        {"symbol": "BTCUSDT", "markPrice": "95001.0"},
        {"symbol": "SOLUSDT", "markPrice": "180.4"},
    ]

    response = client.get("/dashboard/live-pricing", params=[("symbols", "solusdt"), ("symbols", "solusdt"), ("symbols", "BTCUSDT")])

    assert response.status_code == 200
    data = response.json()
    assert [position["symbol"] for position in data["positions"]] == ["BTCUSDT", "SOLUSDT"]
    assert data["quotes"] == [
        {"symbol": "BTCUSDT", "mark_price": 95001.0},
        {"symbol": "SOLUSDT", "mark_price": 180.4},
    ]
    mock_get_position_risk.assert_awaited_once_with(symbol=None)
    assert mock_get_premium_index.await_args_list[0].args == ("BTCUSDT",)
    assert mock_get_premium_index.await_args_list[1].args == ("SOLUSDT",)


@patch("apps.api.app.services.binance_client.BinanceFuturesClient.get_premium_index", new_callable=AsyncMock)
@patch("apps.api.app.services.binance_client.BinanceFuturesClient.get_position_risk", new_callable=AsyncMock)
def test_dashboard_live_pricing_preserves_multiple_rows_for_same_symbol(mock_get_position_risk, mock_get_premium_index):
    mock_get_position_risk.return_value = [
        {
            "symbol": "BTCUSDT",
            "positionAmt": "1.5",
            "markPrice": "95000.5",
            "unRealizedProfit": "120.5",
        },
        {
            "symbol": "BTCUSDT",
            "positionAmt": "-0.5",
            "markPrice": "94990.0",
            "unRealizedProfit": "-12.0",
        },
        {
            "symbol": "ETHUSDT",
            "positionAmt": "2.0",
            "markPrice": "3000.0",
            "unRealizedProfit": "40.0",
        },
    ]
    mock_get_premium_index.return_value = {"symbol": "BTCUSDT", "markPrice": "95002.0"}

    response = client.get("/dashboard/live-pricing", params={"symbols": "btcusdt"})

    assert response.status_code == 200
    data = response.json()
    assert [position["symbol"] for position in data["positions"]] == ["BTCUSDT", "BTCUSDT"]
    assert data["quotes"] == [{"symbol": "BTCUSDT", "mark_price": 95002.0}]
    mock_get_position_risk.assert_awaited_once_with(symbol=None)
    mock_get_premium_index.assert_awaited_once_with("BTCUSDT")


@patch("apps.api.app.services.binance_client.BinanceFuturesClient.get_premium_index", new_callable=AsyncMock)
@patch("apps.api.app.services.binance_client.BinanceFuturesClient.get_position_risk", new_callable=AsyncMock)
def test_dashboard_live_pricing_keeps_partial_quotes_when_one_symbol_fails(mock_get_position_risk, mock_get_premium_index):
    mock_get_position_risk.return_value = []
    mock_get_premium_index.side_effect = [
        {"symbol": "BTCUSDT", "markPrice": "95001.0"},
        RuntimeError("binance timeout"),
    ]

    response = client.get("/dashboard/live-pricing", params=[("symbols", "BTCUSDT"), ("symbols", "ETHUSDT")])

    assert response.status_code == 200
    data = response.json()
    assert data["positions"] == []
    assert data["quotes"] == [{"symbol": "BTCUSDT", "mark_price": 95001.0}]
    mock_get_position_risk.assert_awaited_once_with(symbol=None)
    assert mock_get_premium_index.await_count == 2
