import asyncio
import sys

from apps.worker.trading_bot.config.settings import WorkerSettings
from apps.worker.trading_bot.services.api_client import TradingBotApiClient
from apps.worker.trading_bot.services.hybrid_signal_service import HybridSignalService


def ensure_supported_python() -> None:
    if sys.version_info < (3, 11):
        raise RuntimeError(
            f"apps/worker requiere Python 3.11+ para usar asyncio.TaskGroup; versión actual: {sys.version.split()[0]}"
        )


async def main() -> None:
    ensure_supported_python()
    settings = WorkerSettings()
    api_client = TradingBotApiClient(settings.api_base_url)
    signal_service = HybridSignalService(
        api_client=api_client,
        timeframe=settings.default_signal_timeframe,
        limit=settings.signal_snapshot_limit,
    )

    for symbol in settings.symbols:
        signals, context, thesis, levels, meta = await signal_service.build_signal_pack(symbol)
        payload = {
            "symbol": symbol,
            "side": meta.side,
            "entry_price": levels["entry"],
            "stop_loss": levels["stop"],
            "take_profit": levels["take_profit"],
            "capital_usdt": settings.seed_capital_usdt,
            "existing_risk_pct": 0.0,
            "thesis": thesis,
            "signals": {
                "technical": signals.technical,
                "fundamental": signals.fundamental,
                "sentiment": signals.sentiment,
                "confidence": signals.confidence,
            },
            "market_state": {
                "symbol": context.symbol,
                "timeframe": context.timeframe,
                "volatility_pct": context.volatility_pct,
                "trend_strength": context.trend_strength,
                "liquidity_score": context.liquidity_score,
            },
        }
        created = await api_client.create_trade_plan(payload)
        print({"symbol": symbol, "source": meta.source, "reason": meta.reason, "trade_plan": created})
        if settings.paper_trading and created.get("status") == "approved":
            executed = await api_client.execute_paper_trade(created["id"])
            print({"symbol": symbol, "paper_execution": executed})


if __name__ == "__main__":
    asyncio.run(main())
