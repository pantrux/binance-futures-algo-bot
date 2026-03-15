from apps.api.app.services.binance_client import BinanceFuturesClient


def test_serialize_quantity_trims_float_artifacts_for_eth_like_size():
    assert BinanceFuturesClient._serialize_quantity(0.8100000000000001) == "0.81"


def test_serialize_quantity_trims_float_artifacts_for_sol_like_size():
    assert BinanceFuturesClient._serialize_quantity(18.030000000000001) == "18.03"


def test_serialize_quantity_preserves_reasonable_precision_without_trailing_zeros():
    assert BinanceFuturesClient._serialize_quantity(0.0015) == "0.0015"
