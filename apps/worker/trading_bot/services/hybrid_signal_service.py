import math
from dataclasses import dataclass

from apps.worker.trading_bot.models.signals import MarketContext, SignalPack
from apps.worker.trading_bot.services.demo_signal_service import DemoSignalService


@dataclass(frozen=True)
class HybridSignalResult:
    source: str  # 'market' | 'demo'
    reason: str


class HybridSignalService:
    """Construye un paquete de señales usando datos reales (API) cuando hay suficiente información.

    Estrategia:
    1) Intentar GET /signals/{symbol} (y /market/snapshot/{symbol})
    2) Si falta data o falla la API, fallback controlado a DemoSignalService

    Nota: este worker genera los campos requeridos por /trade-plans (SignalPack + MarketContext + niveles)
    a partir de un snapshot de señales (bias/regime/features). Es una aproximación deliberadamente simple
    para el corte mínimo del PR-7.
    """

    def __init__(
        self,
        api_client,
        demo_service: DemoSignalService | None = None,
        timeframe: str = "15m",
        limit: int = 200,
    ) -> None:
        self.api_client = api_client
        self.demo_service = demo_service or DemoSignalService()
        self.timeframe = timeframe
        self.limit = limit

    async def build_signal_pack(
        self, symbol: str
    ) -> tuple[SignalPack, MarketContext, str, dict[str, float], HybridSignalResult]:
        try:
            snapshot = await self.api_client.get_signal_snapshot(symbol, timeframe=self.timeframe, limit=self.limit)
            market = await self.api_client.get_market_snapshot(symbol)
            if not self._is_snapshot_usable(snapshot):
                raise ValueError("snapshot incompleto (candles/indicadores insuficientes)")

            pack, context, thesis, levels = self._build_from_market(symbol=symbol, snapshot=snapshot, market=market)
            return pack, context, thesis, levels, HybridSignalResult(source="market", reason="ok")
        except Exception as exc:  # noqa: BLE001 (fallback intentionally broad)
            pack, context, thesis, levels = self.demo_service.build_signal_pack(symbol)
            return pack, context, thesis, levels, HybridSignalResult(source="demo", reason=str(exc))

    @staticmethod
    def _is_snapshot_usable(snapshot: dict) -> bool:
        # El endpoint /signals/{symbol} ya valida candles/indicadores; pero si llega 200 con None, lo tratamos como insuficiente.
        required_any = ["trend_bias", "momentum_bias", "volatility_regime"]
        if any(snapshot.get(k) in (None, "unknown") for k in required_any):
            return False
        # Necesitamos al menos last_candle_close_ms y atr_pct para niveles/volatilidad.
        if snapshot.get("last_candle_close_ms") is None:
            return False
        if snapshot.get("atr_pct") is None:
            return False
        return True

    def _build_from_market(self, symbol: str, snapshot: dict, market: dict | None) -> tuple[SignalPack, MarketContext, str, dict[str, float]]:
        trend_bias = snapshot.get("trend_bias", "unknown")
        momentum_bias = snapshot.get("momentum_bias", "unknown")
        vol_regime = snapshot.get("volatility_regime", "unknown")
        ema_spread_pct = snapshot.get("ema_spread_pct")
        atr_pct = float(snapshot.get("atr_pct") or 0.0)
        rsi_14 = snapshot.get("rsi_14")
        momentum_10 = snapshot.get("momentum_10")

        technical = self._technical_score(trend_bias, momentum_bias, rsi_14=rsi_14, momentum_10=momentum_10)
        fundamental = 50.0
        sentiment = 50.0
        confidence = self._confidence_score(vol_regime, atr_pct)

        volatility_pct = max(0.0, atr_pct * 100.0)
        trend_strength = self._trend_strength(ema_spread_pct)
        liquidity_score = self._liquidity_score(market)

        context = MarketContext(
            symbol=symbol,
            timeframe=snapshot.get("timeframe") or self.timeframe,
            volatility_pct=volatility_pct,
            trend_strength=trend_strength,
            liquidity_score=liquidity_score,
        )

        entry = self._entry_price(market)
        levels = self._levels_from_atr(entry, atr_pct)

        thesis = self._thesis(trend_bias, momentum_bias, vol_regime)
        pack = SignalPack(technical=technical, fundamental=fundamental, sentiment=sentiment, confidence=confidence)
        return pack, context, thesis, levels

    @staticmethod
    def _entry_price(market: dict | None) -> float:
        if not market:
            # fallback seguro si no hay snapshot de mercado: entry dummy para no crashear; el risk-engine debería filtrar
            return 1.0
        for key in ("mark_price", "last_price", "index_price"):
            value = market.get(key)
            if value is not None:
                return float(value)
        return 1.0

    @staticmethod
    def _levels_from_atr(entry: float, atr_pct: float) -> dict[str, float]:
        # Default long (corte mínimo).
        # Stop y TP protegidos contra atr_pct ridículo.
        stop_dist = max(0.002, atr_pct * 1.2)
        tp_dist = max(0.004, atr_pct * 2.0)
        stop = entry * (1.0 - stop_dist)
        take_profit = entry * (1.0 + tp_dist)
        return {"entry": entry, "stop": stop, "take_profit": take_profit}

    @staticmethod
    def _bias_score(bias: str) -> float:
        return {
            "bullish": 80.0,
            "neutral": 55.0,
            "bearish": 30.0,
        }.get(bias, 50.0)

    def _technical_score(self, trend_bias: str, momentum_bias: str, rsi_14: float | None, momentum_10: float | None) -> float:
        base = 0.6 * self._bias_score(trend_bias) + 0.4 * self._bias_score(momentum_bias)
        # Ajustes suaves
        if rsi_14 is not None:
            # RSI centrado en 50, penaliza extremos
            base += max(-8.0, min(8.0, (50.0 - abs(rsi_14 - 50.0)) / 6.0 - 4.0))
        if momentum_10 is not None:
            base += max(-6.0, min(6.0, float(momentum_10) / 2.0))
        return max(0.0, min(100.0, base))

    @staticmethod
    def _confidence_score(vol_regime: str, atr_pct: float) -> float:
        # Volatilidad alta => menos confianza.
        vol_penalty = {"low": 0.0, "medium": 6.0, "high": 12.0}.get(vol_regime, 8.0)
        atr_penalty = max(0.0, min(20.0, atr_pct * 200.0))  # 0.10 atr => 20 penalty
        return max(0.0, min(100.0, 75.0 - vol_penalty - atr_penalty))

    @staticmethod
    def _trend_strength(ema_spread_pct: float | None) -> float:
        if ema_spread_pct is None:
            return 50.0
        # ema_spread_pct ya es porcentaje; escalamos a 0..100
        strength = abs(float(ema_spread_pct)) * 1200.0
        return max(0.0, min(100.0, strength))

    @staticmethod
    def _liquidity_score(market: dict | None) -> float:
        if not market:
            return 50.0
        vol = market.get("volume_24h")
        if vol is None:
            return 50.0
        # Escala logarítmica: 10^3 => 60, 10^4 => 80, 10^5 => 100 cap
        score = math.log10(float(vol) + 1.0) * 20.0
        return max(0.0, min(100.0, score))

    @staticmethod
    def _thesis(trend_bias: str, momentum_bias: str, vol_regime: str) -> str:
        return (
            f"Setup market-driven ({trend_bias}/{momentum_bias}) con régimen de volatilidad {vol_regime}. "
            "Plan generado desde snapshot de señales y niveles basados en ATR."
        )
