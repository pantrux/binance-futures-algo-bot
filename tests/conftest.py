import sys
from pathlib import Path

# pytest en modo importlib no garantiza que el root del repo quede en sys.path.
# Se mantiene explícito para que imports tipo `apps.api...` sigan siendo reproducibles.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.api.app.db.models import MarketCandle


def seed_walk_forward_candles(db, symbol: str = "BTCUSDT", timeframe: str = "15m", candles: int = 320) -> None:
    close = 100.0
    phases = [1.4] * 18 + [-1.1] * 12 + [1.8] * 20 + [-1.5] * 14 + [1.0] * 16 + [-0.9] * 10
    for index in range(candles):
        step = phases[index % len(phases)]
        previous_close = close
        close = max(10.0, close + step)
        db.add(MarketCandle(
            symbol=symbol,
            timeframe=timeframe,
            open_time_ms=index * 60_000,
            close_time_ms=(index + 1) * 60_000,
            open_price=previous_close,
            high_price=max(previous_close, close) + 0.8,
            low_price=min(previous_close, close) - 0.8,
            close_price=close,
            volume=100 + index,
            quote_volume=1000 + index,
            trades_count=10 + index,
            source="binance",
        ))
    db.commit()
