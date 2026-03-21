import asyncio
import json
import logging
import sys
from dataclasses import dataclass

from apps.worker.trading_bot.config.settings import WorkerSettings
from apps.worker.trading_bot.services.api_client import TradingBotApiClient
from apps.worker.trading_bot.services.binance_testnet_router import BinanceTestnetRouter
from apps.worker.trading_bot.services.hybrid_signal_service import HybridSignalService

logger = logging.getLogger("apps.worker.observability")


@dataclass
class SymbolRunResult:
    symbol: str
    timeframe: str
    success: bool
    last_candle_close_ms: int | None = None
    skipped_duplicate: bool = False


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


def build_signal_services(settings: WorkerSettings, api_client: TradingBotApiClient) -> dict[str, HybridSignalService]:
    if settings.runtime_mode == "oneshot":
        timeframes = (settings.default_signal_timeframe,)
    else:
        timeframes = settings.timeframes or (settings.default_signal_timeframe,)
    return {
        timeframe: HybridSignalService(
            api_client=api_client,
            timeframe=timeframe,
            limit=settings.signal_snapshot_limit,
        )
        for timeframe in timeframes
    }


async def process_symbol_cycle(
    *,
    symbol: str,
    timeframe: str,
    settings: WorkerSettings,
    signal_service: HybridSignalService,
    api_client: TradingBotApiClient,
    testnet_router: BinanceTestnetRouter,
    processed_candles: dict[tuple[str, str], int] | None = None,
) -> SymbolRunResult:
    signals, context, thesis, levels, meta = await signal_service.build_signal_pack(symbol)
    if context.timeframe != timeframe:
        raise ValueError(f"timeframe_mismatch requested={timeframe} received={context.timeframe}")
    last_candle_close_ms = context.last_candle_close_ms
    dedupe_key = (symbol, timeframe)

    if processed_candles is not None and last_candle_close_ms is not None:
        last_processed = processed_candles.get(dedupe_key)
        if last_processed == last_candle_close_ms:
            log_event(
                "trade_cycle_skipped_duplicate_candle",
                symbol=symbol,
                timeframe=context.timeframe,
                last_candle_close_ms=last_candle_close_ms,
            )
            return SymbolRunResult(
                symbol=symbol,
                timeframe=context.timeframe,
                success=True,
                last_candle_close_ms=last_candle_close_ms,
                skipped_duplicate=True,
            )

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
    previous_processed = None
    should_track_candle = processed_candles is not None and last_candle_close_ms is not None
    if should_track_candle:
        previous_processed = processed_candles.get(dedupe_key)
        processed_candles[dedupe_key] = last_candle_close_ms
    try:
        created = await api_client.create_trade_plan(payload)
    except Exception:
        if should_track_candle:
            if previous_processed is None:
                processed_candles.pop(dedupe_key, None)
            else:
                processed_candles[dedupe_key] = previous_processed
        raise
    log_event(
        "trade_plan_created",
        symbol=symbol,
        timeframe=context.timeframe,
        source=meta.source,
        reason=meta.reason,
        last_candle_close_ms=last_candle_close_ms,
        trade_plan=created,
    )
    if created.get("status") != "approved":
        log_event(
            "trade_execution_skipped_not_approved",
            symbol=symbol,
            timeframe=context.timeframe,
            status=created.get("status"),
            trade_plan_id=created.get("id"),
        )
        return SymbolRunResult(symbol=symbol, timeframe=context.timeframe, success=True, last_candle_close_ms=last_candle_close_ms)

    trade_plan_id = created.get("id")
    if not trade_plan_id:
        log_event("trade_execution_skip_missing_id", symbol=symbol, timeframe=context.timeframe, trade_plan=created)
        return SymbolRunResult(symbol=symbol, timeframe=context.timeframe, success=False, last_candle_close_ms=last_candle_close_ms)

    if settings.paper_trading:
        executed = await api_client.execute_paper_trade(trade_plan_id)
        log_event("paper_trade_executed", symbol=symbol, timeframe=context.timeframe, source=meta.source, execution=executed)
        return SymbolRunResult(symbol=symbol, timeframe=context.timeframe, success=True, last_candle_close_ms=last_candle_close_ms)

    if meta.source != "market":
        log_event(
            "testnet_trade_execution_blocked_non_market_source",
            symbol=symbol,
            timeframe=context.timeframe,
            trade_plan_id=trade_plan_id,
            source=meta.source,
            reason=meta.reason,
        )
        if settings.testnet_fallback_to_paper:
            executed = await api_client.execute_paper_trade(trade_plan_id)
            log_event(
                "paper_trade_fallback_executed_non_market_source",
                symbol=symbol,
                timeframe=context.timeframe,
                source=meta.source,
                reason=meta.reason,
                execution=executed,
            )
        return SymbolRunResult(symbol=symbol, timeframe=context.timeframe, success=True, last_candle_close_ms=last_candle_close_ms)

    testnet_execution = await testnet_router.execute_trade_plan(symbol=symbol, trade_plan=created)
    log_event("testnet_trade_execution_result", symbol=symbol, timeframe=context.timeframe, execution=testnet_execution)

    if testnet_execution.get("executed"):
        return SymbolRunResult(symbol=symbol, timeframe=context.timeframe, success=True, last_candle_close_ms=last_candle_close_ms)

    if settings.testnet_fallback_to_paper:
        executed = await api_client.execute_paper_trade(trade_plan_id)
        log_event(
            "paper_trade_fallback_executed",
            symbol=symbol,
            timeframe=context.timeframe,
            reason=testnet_execution.get("reason"),
            execution=executed,
        )
        return SymbolRunResult(symbol=symbol, timeframe=context.timeframe, success=True, last_candle_close_ms=last_candle_close_ms)

    log_event(
        "testnet_trade_execution_failed",
        symbol=symbol,
        timeframe=context.timeframe,
        reason=testnet_execution.get("reason"),
        trade_plan_id=trade_plan_id,
    )

    success = testnet_execution.get("reason") in {
        "testnet_execution_disabled",
        "global_kill_switch_enabled",
        "symbol_kill_switch_enabled",
        "trade_plan_not_approved",
        "trade_plan_missing_id",
    }
    return SymbolRunResult(symbol=symbol, timeframe=context.timeframe, success=success, last_candle_close_ms=last_candle_close_ms)


async def process_symbol(
    symbol: str,
    settings: WorkerSettings,
    signal_service: HybridSignalService,
    api_client: TradingBotApiClient,
    testnet_router: BinanceTestnetRouter,
) -> bool:
    result = await process_symbol_cycle(
        symbol=symbol,
        timeframe=signal_service.timeframe,
        settings=settings,
        signal_service=signal_service,
        api_client=api_client,
        testnet_router=testnet_router,
    )
    return result.success


async def run_worker_cycle(
    settings: WorkerSettings,
    signal_services: dict[str, HybridSignalService],
    api_client: TradingBotApiClient,
    testnet_router: BinanceTestnetRouter,
    processed_candles: dict[tuple[str, str], int] | None = None,
) -> tuple[int, int, int]:
    if not settings.paper_trading:
        try:
            sync_result = await api_client.sync_open_testnet_exits()
            log_event("testnet_open_exits_sync_result", sync=sync_result)
        except Exception as exc:  # noqa: BLE001
            log_event("testnet_open_exits_sync_failed", error=str(exc), error_type=type(exc).__name__)

    tasks = [
        process_symbol_cycle(
            symbol=symbol,
            timeframe=timeframe,
            settings=settings,
            signal_service=signal_service,
            api_client=api_client,
            testnet_router=testnet_router,
            processed_candles=processed_candles,
        )
        for timeframe, signal_service in signal_services.items()
        for symbol in settings.symbols
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    successes = 0
    failures = 0
    duplicates = 0
    ordered_targets = [(symbol, timeframe) for timeframe in signal_services for symbol in settings.symbols]
    for (symbol, timeframe), result in zip(ordered_targets, results):
        if isinstance(result, BaseException):
            failures += 1
            log_event("symbol_failed_exception", symbol=symbol, timeframe=timeframe, error=str(result))
            continue
        if result.skipped_duplicate:
            duplicates += 1
        if result.success:
            successes += 1
        else:
            failures += 1
            log_event("symbol_failed_without_exception", symbol=symbol, timeframe=timeframe)

    if failures > 0:
        log_event("symbol_failures_detected", failures=failures, successes=successes, duplicates=duplicates)

    if settings.symbols and (successes == 0 or (settings.strict_symbol_failures and failures > 0)):
        raise RuntimeError(f"symbol_failures={failures};symbol_successes={successes};duplicates={duplicates}")

    return successes, failures, duplicates


async def main() -> None:
    ensure_logging_configured()
    ensure_supported_python()
    settings = WorkerSettings()
    api_client = TradingBotApiClient(settings.api_base_url)
    signal_services = build_signal_services(settings, api_client)
    testnet_router = BinanceTestnetRouter(
        api_client=api_client,
        execution_enabled=settings.testnet_execution_enabled,
        global_kill_switch=settings.testnet_global_kill_switch,
        kill_switch_symbols=settings.testnet_kill_switch_symbols,
    )

    if settings.runtime_mode == "oneshot":
        await run_worker_cycle(settings, signal_services, api_client, testnet_router)
        return

    processed_candles: dict[tuple[str, str], int] = {}
    cycle = 0
    while True:
        cycle += 1
        try:
            successes, failures, duplicates = await run_worker_cycle(
                settings,
                signal_services,
                api_client,
                testnet_router,
                processed_candles=processed_candles,
            )
        except RuntimeError as exc:
            log_event(
                "worker_cycle_error",
                cycle=cycle,
                runtime_mode=settings.runtime_mode,
                error=str(exc),
                tracked_candles=len(processed_candles),
            )
            if settings.max_cycles > 0 and cycle >= settings.max_cycles:
                raise
            await asyncio.sleep(settings.poll_interval_seconds)
            continue

        log_event(
            "worker_cycle_completed",
            cycle=cycle,
            runtime_mode=settings.runtime_mode,
            successes=successes,
            failures=failures,
            duplicates=duplicates,
            tracked_candles=len(processed_candles),
        )
        if settings.max_cycles > 0 and cycle >= settings.max_cycles:
            break
        await asyncio.sleep(settings.poll_interval_seconds)


if __name__ == "__main__":
    asyncio.run(main())
