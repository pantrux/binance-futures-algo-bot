from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.app.api.deps import get_db
from apps.api.app.schemas.trade_plan import TradePlanCreateRequest, TradePlanCreateResponse
from apps.api.app.schemas.trading import RiskDecision, TradePlanRequest
from apps.api.app.services.binance_client import BinanceFuturesClient
from apps.api.app.services.risk_engine import RiskEngine
from apps.api.app.services.trade_plan_service import TradePlanService

router = APIRouter()
risk_engine = RiskEngine()


@router.get("/health")
def healthcheck() -> dict:
    return {"status": "ok", "service": "api"}


@router.get("/integrations/binance/testnet/ping")
async def binance_ping() -> dict:
    return await BinanceFuturesClient().ping()


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
