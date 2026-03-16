import hashlib
import hmac
import time
import traceback
from threading import Lock

from apps.api.app.schemas.live_pricing import DashboardLivePricingResponse
from apps.api.app.services.live_pricing_service import LivePricingService
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from apps.api.app.api.deps import get_db
from apps.api.app.core.settings import settings
from apps.api.app.observability.metrics import api_metrics
from apps.api.app.schemas.backtesting import BacktestRunRequest, BacktestRunResponse
from apps.api.app.schemas.dashboard import DashboardSummary
from apps.api.app.schemas.dashboard_command_center import DashboardCommandCenterResponse
from apps.api.app.schemas.execution_parity import ExecutionParityReport
from apps.api.app.schemas.execution_reconciliation import ReconciliationReport
from apps.api.app.schemas.production_reporting import AlertEvaluationResponse, DailyProductionSummary
from apps.api.app.schemas.shadow_run_reporting import ShadowRunSummary
from apps.api.app.schemas.indicators import IndicatorSnapshot
from apps.api.app.schemas.market_data import MarketCandleRead, MarketIngestionResponse, MarketSnapshotRead
from apps.api.app.schemas.market_regime import MarketRegimeSnapshot
from apps.api.app.schemas.paper_trading import PaperExecutionResponse
from apps.api.app.schemas.signals import SignalSnapshot
from apps.api.app.schemas.testnet_trading import TestnetExecutionResponse
from apps.api.app.schemas.trade_plan import TradePlanCreateRequest, TradePlanCreateResponse
from apps.api.app.schemas.trade_plan_read import TradePlanRead
from apps.api.app.schemas.trading import RiskDecision, TradePlanRequest
from apps.api.app.services.binance_client import BinanceFuturesClient
from apps.api.app.services.binance_market_data_service import BinanceMarketDataService
from apps.api.app.services.backtesting_service import BacktestingError, BacktestingService
from apps.api.app.services.dashboard_command_center_service import DashboardCommandCenterService
from apps.api.app.services.dashboard_service import DashboardService
from apps.api.app.services.execution_parity_service import ExecutionParityService
from apps.api.app.services.execution_state_machine_service import ExecutionStateMachineService
from apps.api.app.services.indicator_service import IndicatorService
from apps.api.app.services.market_regime_service import MarketRegimeService
from apps.api.app.services.paper_trading_service import PaperTradingService
from apps.api.app.services.production_reporting_service import ProductionReportingService
from apps.api.app.services.risk_engine import RiskEngine
from apps.api.app.services.shadow_run_reporting_service import ShadowRunReportingService
from apps.api.app.services.signal_service import SignalService
from apps.api.app.services.testnet_trading_service import BinanceTestnetTradingService
from apps.api.app.services.trade_plan_query_service import TradePlanQueryService
from apps.api.app.services.trade_plan_service import TradePlanService

router = APIRouter()
risk_engine = RiskEngine()
BACKTESTING_MIN_INTERVAL_SECONDS = 5.0
BACKTESTING_RATE_LIMIT_TTL_SECONDS = BACKTESTING_MIN_INTERVAL_SECONDS * 2
# Este throttle es deliberadamente process-local: protege el despliegue actual de
# un solo worker. Si el API escala a múltiples workers, debe migrarse a un backend
# compartido (por ejemplo Redis) para mantener una cuota global consistente.
_backtesting_rate_limit_lock = Lock()
_backtesting_last_request_by_key: dict[str, float] = {}


def require_metrics_auth(x_metrics_key: str | None = Header(default=None, alias="x-metrics-key")) -> None:
    configured_metrics_key = settings.metrics_api_key.get_secret_value()
    if configured_metrics_key and not hmac.compare_digest(x_metrics_key or "", configured_metrics_key):
        raise HTTPException(status_code=401, detail="No autorizado")


def require_backtesting_access(x_metrics_key: str | None = Header(default=None, alias="x-metrics-key")) -> None:
    require_metrics_auth(x_metrics_key)
    request_key_source = x_metrics_key or "metrics-authenticated"
    request_key = hashlib.sha256(request_key_source.encode("utf-8")).hexdigest()
    now = time.monotonic()
    with _backtesting_rate_limit_lock:
        expired_keys = [
            key
            for key, timestamp in _backtesting_last_request_by_key.items()
            if (now - timestamp) >= BACKTESTING_RATE_LIMIT_TTL_SECONDS
        ]
        for expired_key in expired_keys:
            _backtesting_last_request_by_key.pop(expired_key, None)

        previous_request_at = _backtesting_last_request_by_key.get(request_key)
        if previous_request_at is not None and (now - previous_request_at) < BACKTESTING_MIN_INTERVAL_SECONDS:
            raise HTTPException(
                status_code=429,
                detail="Backtesting rate-limited: espera unos segundos antes de reintentar",
            )
        _backtesting_last_request_by_key[request_key] = now


@router.get("/health")
def healthcheck() -> dict:
    return {"status": "ok", "service": "api"}


@router.get("/metrics")
def metrics_snapshot(_: None = Depends(require_metrics_auth)) -> dict:
    return api_metrics.snapshot()


@router.get("/integrations/binance/testnet/ping")
async def binance_ping() -> dict:
    return await BinanceFuturesClient().ping()


@router.post("/market/ingest/{symbol}", response_model=MarketIngestionResponse)
async def ingest_market(symbol: str, timeframe: str = '15m', limit: int = 50, db: Session = Depends(get_db)) -> MarketIngestionResponse:
    return await BinanceMarketDataService(db).ingest_symbol(symbol=symbol, timeframe=timeframe, limit=limit)


@router.get("/market/candles/{symbol}", response_model=list[MarketCandleRead])
def list_market_candles(symbol: str, timeframe: str = '15m', limit: int = 50, db: Session = Depends(get_db)) -> list[MarketCandleRead]:
    return BinanceMarketDataService(db).list_candles(symbol=symbol, timeframe=timeframe, limit=limit)


@router.get("/market/snapshot/{symbol}", response_model=MarketSnapshotRead | None)
def latest_market_snapshot(symbol: str, db: Session = Depends(get_db)) -> MarketSnapshotRead | None:
    return BinanceMarketDataService(db).latest_snapshot(symbol=symbol)


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)) -> DashboardSummary:
    return DashboardService(db).summary()


@router.get("/dashboard/command-center", response_model=DashboardCommandCenterResponse)
def dashboard_command_center(db: Session = Depends(get_db)) -> DashboardCommandCenterResponse:
    return DashboardCommandCenterService(db).build()


@router.post("/backtesting/run", response_model=BacktestRunResponse)
def run_backtesting(
    payload: BacktestRunRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_backtesting_access),
) -> BacktestRunResponse:
    try:
        return BacktestingService(db).run(payload)
    except BacktestingError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("/indicators/{symbol}", response_model=IndicatorSnapshot)
def indicator_snapshot(symbol: str, timeframe: str = '15m', limit: int = Query(default=200, ge=22, le=1000), db: Session = Depends(get_db)) -> IndicatorSnapshot:
    snapshot = IndicatorService(db).snapshot(symbol=symbol, timeframe=timeframe, limit=limit)
    if snapshot.candles_used == 0:
        raise HTTPException(status_code=404, detail=f"No hay candles para {symbol} en timeframe {timeframe}")
    if any(value is None for value in (snapshot.ema_9, snapshot.ema_21, snapshot.rsi_14, snapshot.atr_14, snapshot.momentum_10)):
        raise HTTPException(status_code=400, detail=f"Candles insuficientes para calcular indicadores de {symbol} en timeframe {timeframe}")
    return snapshot


@router.get("/signals/{symbol}", response_model=SignalSnapshot)
def signal_snapshot(symbol: str, timeframe: str = '15m', limit: int = Query(default=200, ge=22, le=1000), db: Session = Depends(get_db)) -> SignalSnapshot:
    indicator_snapshot = IndicatorService(db).snapshot(symbol=symbol, timeframe=timeframe, limit=limit)
    if indicator_snapshot.candles_used == 0:
        raise HTTPException(status_code=404, detail=f"No hay candles para {symbol} en timeframe {timeframe}")
    if any(value is None for value in (indicator_snapshot.ema_9, indicator_snapshot.ema_21, indicator_snapshot.rsi_14, indicator_snapshot.atr_14, indicator_snapshot.momentum_10)):
        raise HTTPException(status_code=400, detail=f"Candles insuficientes para calcular señales de {symbol} en timeframe {timeframe}")
    return SignalService(db).snapshot(symbol=symbol, timeframe=timeframe, limit=limit, indicator_snapshot=indicator_snapshot)


@router.get("/market/regime/{symbol}", response_model=MarketRegimeSnapshot)
def market_regime_snapshot(symbol: str, timeframe: str = '15m', limit: int = Query(default=200, ge=22, le=1000), db: Session = Depends(get_db)) -> MarketRegimeSnapshot:
    indicator_snapshot = IndicatorService(db).snapshot(symbol=symbol, timeframe=timeframe, limit=limit)
    if indicator_snapshot.candles_used == 0:
        raise HTTPException(status_code=404, detail=f"No hay candles para {symbol} en timeframe {timeframe}")
    if any(value is None for value in (indicator_snapshot.ema_9, indicator_snapshot.ema_21, indicator_snapshot.rsi_14, indicator_snapshot.atr_14, indicator_snapshot.momentum_10)):
        raise HTTPException(status_code=400, detail=f"Candles insuficientes para calcular régimen de mercado de {symbol} en timeframe {timeframe}")

    regime_signal_snapshot = SignalService(db).snapshot(
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
        indicator_snapshot=indicator_snapshot,
    )
    if any(value is None for value in (regime_signal_snapshot.ema_spread_pct, regime_signal_snapshot.atr_pct)):
        raise HTTPException(status_code=400, detail=f"Candles insuficientes para calcular régimen de mercado de {symbol} en timeframe {timeframe}")

    return MarketRegimeService(db).snapshot(
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
        indicator_snapshot=indicator_snapshot,
        signal_snapshot=regime_signal_snapshot,
    )


@router.get("/trade-plans", response_model=list[TradePlanRead])
def list_trade_plans(limit: int = 20, db: Session = Depends(get_db)) -> list[TradePlanRead]:
    return TradePlanQueryService(db).list_trade_plans(limit=limit)


@router.post("/risk/evaluate", response_model=RiskDecision)
def evaluate_risk(payload: TradePlanRequest) -> RiskDecision:
    return risk_engine.evaluate(
        capital_usdt=payload.capital_usdt,
        existing_risk_pct=payload.existing_risk_pct,
        signals=payload.signals,
        market_state=payload.market_state,
        entry_price=payload.entry_price,
        stop_loss=payload.stop_loss,
    )


@router.post("/trade-plans", response_model=TradePlanCreateResponse)
async def create_trade_plan(payload: TradePlanCreateRequest, db: Session = Depends(get_db)) -> TradePlanCreateResponse:
    service = TradePlanService(db=db)
    return await service.create_trade_plan(payload)


@router.post("/paper-trading/execute/{trade_plan_id}", response_model=PaperExecutionResponse)
def paper_execute(trade_plan_id: int, db: Session = Depends(get_db)) -> PaperExecutionResponse:
    try:
        result = PaperTradingService(db).execute_trade_plan(trade_plan_id)
        return PaperExecutionResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/testnet-trading/execute/{trade_plan_id}", response_model=TestnetExecutionResponse)
async def testnet_execute(trade_plan_id: int, db: Session = Depends(get_db)) -> TestnetExecutionResponse:
    try:
        result = await BinanceTestnetTradingService(
            db=db,
            execution_enabled=settings.testnet_execution_enabled,
        ).execute_trade_plan(trade_plan_id)
        return TestnetExecutionResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/execution/reconcile/{trade_plan_id}", response_model=ReconciliationReport)
def reconcile_execution(trade_plan_id: int, db: Session = Depends(get_db)) -> ReconciliationReport:
    try:
        return ExecutionStateMachineService(db).reconcile_trade_plan(trade_plan_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/execution/parity/{symbol}", response_model=ExecutionParityReport)
def execution_parity(
    symbol: str,
    timeframe: str | None = Query(default=None, min_length=1),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> ExecutionParityReport:
    return ExecutionParityService(db).build_report(symbol=symbol.upper(), timeframe=timeframe, limit=limit)


@router.get("/reporting/daily-summary", response_model=DailyProductionSummary)
def reporting_daily_summary(_: None = Depends(require_metrics_auth), db: Session = Depends(get_db)) -> DailyProductionSummary:
    return ProductionReportingService(db).daily_summary()


@router.get("/alerts/evaluate", response_model=AlertEvaluationResponse)
def alerts_evaluate(_: None = Depends(require_metrics_auth), db: Session = Depends(get_db)) -> AlertEvaluationResponse:
    return ProductionReportingService(db).evaluate_alerts()


@router.get("/reporting/shadow-run-summary", response_model=ShadowRunSummary)
def reporting_shadow_run_summary(
    window_days: int = Query(default=30, ge=1, le=365),
    timeframe: str | None = Query(default=None, min_length=1),
    _: None = Depends(require_metrics_auth),
    db: Session = Depends(get_db),
) -> ShadowRunSummary:
    return ShadowRunReportingService(db).build_summary(window_days=window_days, timeframe=timeframe)


@router.get("/dashboard/live-pricing", response_model=DashboardLivePricingResponse)
async def dashboard_live_pricing() -> DashboardLivePricingResponse:
    try:
        service = LivePricingService()
        return await service.get_live_pricing()
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to fetch live pricing") from exc
