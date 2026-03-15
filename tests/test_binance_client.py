import math

import pytest

from apps.api.app.services.binance_client import BinanceFuturesClient


def test_serialize_quantity_trims_float_artifacts_for_eth_like_size():
    assert BinanceFuturesClient._serialize_quantity(0.8100000000000001) == "0.81"


def test_serialize_quantity_trims_float_artifacts_for_sol_like_size():
    assert BinanceFuturesClient._serialize_quantity(18.030000000000001) == "18.03"


def test_serialize_quantity_preserves_reasonable_precision_without_trailing_zeros():
    assert BinanceFuturesClient._serialize_quantity(0.0015) == "0.0015"


def test_serialize_quantity_formats_exact_integer_without_decimal_suffix():
    assert BinanceFuturesClient._serialize_quantity(2.0) == "2"


def test_serialize_quantity_trims_trailing_zero_fraction():
    assert BinanceFuturesClient._serialize_quantity(0.100) == "0.1"


def test_serialize_quantity_rejects_zero():
    with pytest.raises(ValueError, match="número finito y mayor a cero"):
        BinanceFuturesClient._serialize_quantity(0.0)


def test_serialize_quantity_rejects_nan():
    with pytest.raises(ValueError, match="número finito y mayor a cero"):
        BinanceFuturesClient._serialize_quantity(math.nan)


def test_serialize_quantity_rejects_inf():
    with pytest.raises(ValueError, match="número finito y mayor a cero"):
        BinanceFuturesClient._serialize_quantity(math.inf)
