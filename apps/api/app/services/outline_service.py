from datetime import datetime, UTC
import httpx

from apps.api.app.core.settings import settings
from apps.api.app.schemas.trading import TradePlanRequest


class OutlineService:
    def __init__(self) -> None:
        self.base_url = settings.outline_api_url.rstrip("/")
        self.token = settings.outline_api_token

    async def create_trade_plan_document(self, request: TradePlanRequest, risk_summary: dict) -> dict:
        if not self.token:
            return {"status": "skipped", "reason": "Outline token no configurado"}

        title = f"Plan operativo {request.symbol} {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}"
        text = f"""
# {title}

## Resumen
- Símbolo: **{request.symbol}**
- Dirección: **{request.side.upper()}**
- Entrada: **{request.entry_price}**
- Stop Loss: **{request.stop_loss}**
- Take Profit: **{request.take_profit}**

## Señales
- Técnico: **{request.signals.technical}**
- Fundamental: **{request.signals.fundamental}**
- Sentimiento: **{request.signals.sentiment}**
- Confianza: **{request.signals.confidence}**

## Régimen y riesgo
- Régimen: **{risk_summary['market_regime']}**
- Score compuesto: **{risk_summary['score']}**
- Riesgo sugerido: **{risk_summary['suggested_risk_pct']}%**
- Notional máximo: **{risk_summary['max_position_notional']} USDT**
- Motivo: **{risk_summary['reason']}**
""".strip()

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                f"{self.base_url}/documents.create",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "title": title,
                    "text": text,
                    "publish": True,
                },
            )
            response.raise_for_status()
            return response.json()
