import pytest
from pydantic import ValidationError

from apps.worker.trading_bot.config.settings import WorkerSettings


def test_worker_settings_reject_invalid_poll_interval():
    with pytest.raises(ValidationError, match="poll_interval_seconds"):
        WorkerSettings(poll_interval_seconds=0)



def test_worker_settings_reject_negative_max_cycles():
    with pytest.raises(ValidationError, match="max_cycles"):
        WorkerSettings(max_cycles=-1)


def test_worker_settings_accepts_ema_rsi_strategy_and_symbol_list():
    settings = WorkerSettings(signal_strategy="ema_rsi_baseline", signal_strategy_symbols="ETHUSDT")
    assert settings.signal_strategy == "ema_rsi_baseline"
    assert settings.signal_strategy_symbols == ("ETHUSDT",)
