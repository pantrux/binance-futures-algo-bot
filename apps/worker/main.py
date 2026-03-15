import asyncio
import json
import logging
import sys

from apps.worker.trading_bot.config.settings import WorkerSettings
from apps.worker.trading_bot.services.api_client import TradingBotApiClient
from apps.worker.trading_bot.services.binance_testnet_router import BinanceTestnetRouter
from apps.worker.trading_bot.services.hybrid_signal_service import HybridSignalService

logger = logging.getLogger("apps.worker.observability")


def ensure_logging_configured() -> None:
    worker_logger = logging.getLogger("apps.worker")
    if worker_logger.handlers:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    worker_logger.addHandler(handler)
    worker_logger.setLevel(logging.INFO)
    worker_logger.propagate = False


def log_event(event: str, **payload: object) -> None:
    logger.info(json.dumps({"event": event, **payload}, ensure_ascii=False, default=str))


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
    testnet_router: BinanceTestnetRouter,
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
            "market_regime": context.market_regime,
            "regime_confidence": context.regime_confidence,
        },
    }
    created = await api_client.create_trade_plan(payload)
    log_event("trade_plan_created", symbol=symbol, source=meta.source, reason=meta.reason, trade_plan=created)
    if created.get("status") != "approved":
        log_event(
            "trade_execution_skipped_not_approved",
            symbol=symbol,
            status=created.get("status"),
            trade_plan_id=created.get("id"),
        )
        return True

    trade_plan_id = created.get("id")
    if not trade_plan_id:
        log_event("trade_execution_skip_missing_id", symbol=symbol, trade_plan=created)
        return False

    if settings.paper_trading:
        executed = await api_client.execute_paper_trade(trade_plan_id)
        log_event("paper_trade_executed", symbol=symbol, source=meta.source, execution=executed)
        return True

    if meta.source != "market":
        log_event(
            "testnet_trade_execution_blocked_non_market_source",
            symbol=symbol,
            trade_plan_id=trade_plan_id,
            source=meta.source,
            reason=meta.reason,
        )
        if settings.testnet_fallback_to_paper:
            executed = await api_client.execute_paper_trade(trade_plan_id)
            log_event(
                "paper_trade_fallback_executed_non_market_source",
                symbol=symbol,
                source=meta.source,
                reason=meta.reason,
                execution=executed,
            )
        return True

    testnet_execution = await testnet_router.execute_trade_plan(symbol=symbol, trade_plan=created)
    log_event("testnet_trade_execution_result", symbol=symbol, execution=testnet_execution)

    if testnet_execution.get("executed"):
        return True

    if settings.testnet_fallback_to_paper:
        executed = await api_client.execute_paper_trade(trade_plan_id)
        log_event(
            "paper_trade_fallback_executed",
            symbol=symbol,
            reason=testnet_execution.get("reason"),
            execution=executed,
        )
        return True

    log_event(
        "testnet_trade_execution_failed",
        symbol=symbol,
        reason=testnet_execution.get("reason"),
        trade_plan_id=trade_plan_id,
    )

    return testnet_execution.get("reason") in {
        "testnet_execution_disabled",
        "global_kill_switch_enabled",
        "symbol_kill_switch_enabled",
        "trade_plan_not_approved",
        "trade_plan_missing_id",
    }


async def main() -> None:
    ensure_logging_configured()
    ensure_supported_python()
    settings = WorkerSettings()
    api_client = TradingBotApiClient(settings.api_base_url)
    signal_service = HybridSignalService(
        api_client=api_client,
        timeframe=settings.default_signal_timeframe,
        limit=settings.signal_snapshot_limit,
    )
    testnet_router = BinanceTestnetRouter(
        api_client=api_client,
        execution_enabled=settings.testnet_execution_enabled,
        global_kill_switch=settings.testnet_global_kill_switch,
        kill_switch_symbols=settings.testnet_kill_switch_symbols,
    )

    results = await asyncio.gather(
        *(process_symbol(symbol, settings, signal_service, api_client, testnet_router) for symbol in settings.symbols),
        return_exceptions=True,
    )

    successes = 0
    failures = 0
    for symbol, result in zip(settings.symbols, results):
        if isinstance(result, BaseException):
            failures += 1
            log_event("symbol_failed_exception", symbol=symbol, error=str(result))
            continue
        if result is True:
            successes += 1
        else:
            failures += 1
            log_event("symbol_failed_without_exception", symbol=symbol)

    if failures > 0:
        log_event("symbol_failures_detected", failures=failures, successes=successes)

    if settings.symbols and (successes == 0 or (settings.strict_symbol_failures and failures > 0)):
        raise RuntimeError(f"symbol_failures={failures};symbol_successes={successes}")


if __name__ == "__main__":
    asyncio.run(main())
