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


async def process_symbol(
    symbol: str,
    settings: WorkerSettings,
    signal_service: HybridSignalService,
    api_client: TradingBotApiClient,
) -> bool:
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
        trade_plan_id = created.get("id")
        if not trade_plan_id:
            print({"symbol": symbol, "error": "approved_plan_missing_id", "trade_plan": created})
            return False
        executed = await api_client.execute_paper_trade(trade_plan_id)
        print({"symbol": symbol, "paper_execution": executed})
    return True


async def main() -> None:
    ensure_supported_python()
    settings = WorkerSettings()
    api_client = TradingBotApiClient(settings.api_base_url)
    signal_service = HybridSignalService(
        api_client=api_client,
        timeframe=settings.default_signal_timeframe,
        limit=settings.signal_snapshot_limit,
    )

    results = await asyncio.gather(
        *(process_symbol(symbol, settings, signal_service, api_client) for symbol in settings.symbols),
        return_exceptions=True,
    )

    successes = 0
    for symbol, result in zip(settings.symbols, results):
        if isinstance(result, BaseException):
            print({"symbol": symbol, "error": str(result)})
            continue
        if result is True:
            successes += 1
        else:
            print({"symbol": symbol, "error": "symbol_failed_without_exception"})

    if settings.symbols and successes == 0:
        raise RuntimeError("all_symbols_failed")


if __name__ == "__main__":
    asyncio.run(main())
