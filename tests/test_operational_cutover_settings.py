from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from apps.api.app.core.settings import Settings


def test_operational_cutover_requires_timezone():
    with pytest.raises(ValidationError, match="operational_cutover_at"):
        Settings(operational_cutover_at=datetime(2026, 3, 21, 0, 0, 0))



def test_operational_cutover_is_normalized_to_utc():
    value = datetime(2026, 3, 21, 3, 0, 0, tzinfo=timezone.utc)
    settings = Settings(operational_cutover_at=value)

    assert settings.operational_cutover_at == value
    assert settings.operational_cutover_at.tzinfo == timezone.utc
