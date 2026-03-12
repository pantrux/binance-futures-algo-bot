import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from apps.api.app.api.deps import get_db
from apps.api.app.core.settings import settings
from apps.api.app.schemas.dashboard import DashboardSummary
from apps.api.app.schemas.indicators import IndicatorSnapshot
from apps.api.app.schemas.market_data import MarketCandleRead, MarketIngestionResponse, MarketSnapshotRead
from apps.api.app.schemas.market_regime import MarketRegimeSnapshot
from apps.api.app.services.binance_market_data_service import BinanceMarketDataService
from apps.api.app.schemas.paper_trading import PaperExecutionResponse
from apps.api.app.schemas.signals import SignalSnapshot
from apps.api.app.schemas.trade_plan import TradePlanCreateRequest, TradePlanCreateResponse
from apps.api.app.schemas.trade_plan_read import TradePlanRead
from apps.api.app.schemas.trading import RiskDecision, TradePlanRequest
from apps.api.app.observability.metrics import api_metrics
from apps.api.app.services.binance_client import BinanceFuturesClient
from apps.api.app.services.dashboard_service import DashboardService
from apps.api.app.services.indicator_service import IndicatorService
from apps.api.app.services.market_regime_service import MarketRegimeService
from apps.api.app.services.paper_trading_service import PaperTradingService
from apps.api.app.services.risk_engine import RiskEngine
from apps.api.app.services.signal_service import SignalService
from apps.api.app.services.trade_plan_query_service import TradePlanQueryService
from apps.api.app.services.trade_plan_service import TradePlanService

router = APIRouter()
risk_engine = RiskEngine()


def require_metrics_auth(x_metrics_key: str | None = Header(default=None, alias="x-metrics-key")) -> None:
    configured_metrics_key = settings.metrics_api_key.get_secret_value()
    if configured_metrics_key and not hmac.compare_digest(x_metrics_key or "", configured_metrics_key):
        raise HTTPException(status_code=401, detail="No autorizado")


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

    return MarketRegimeService(db).snapshot(symbol=symbol, timeframe=timeframe, limit=limit, indicator_snapshot=indicator_snapshot)


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
