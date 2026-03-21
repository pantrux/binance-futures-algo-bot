import pytest
from pydantic import ValidationError

from apps.worker.trading_bot.config.settings import WorkerSettings


def test_worker_settings_reject_invalid_poll_interval():
    with pytest.raises(ValidationError, match="poll_interval_seconds"):
        WorkerSettings(poll_interval_seconds=0)



def test_worker_settings_reject_negative_max_cycles():
    with pytest.raises(ValidationError, match="max_cycles"):
        WorkerSettings(max_cycles=-1)
