import asyncio
import logging
import math
from dataclasses import dataclass
from typing import overload

from apps.worker.trading_bot.models.signals import MarketContext, SignalPack
from apps.worker.trading_bot.services.demo_signal_service import DemoSignalService


@dataclass(frozen=True)
class HybridSignalResult:
    source: str
    reason: str
    side: str

logger = logging.getLogger(__name__)


class HybridSignalService:
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
            async with asyncio.TaskGroup() as task_group:
                snapshot_task = task_group.create_task(
                    self.api_client.get_signal_snapshot(symbol, timeframe=self.timeframe, limit=self.limit)
                )
                market_task = task_group.create_task(self.api_client.get_market_snapshot(symbol))
                # `regime_task` siempre completa sin excepción porque `_safe_get_market_regime_snapshot`
                # absorbe cualquier error y retorna `None`; así no puede tumbar este TaskGroup.
                regime_task = task_group.create_task(self._safe_get_market_regime_snapshot(symbol))

            snapshot = snapshot_task.result()
            market = market_task.result()
            market_regime_snapshot = regime_task.result()
            if not self._is_snapshot_usable(snapshot):
                raise ValueError("snapshot_incompleto")
            if market is None:
                raise ValueError("market_snapshot_missing")

            pack, context, thesis, levels, side = self._build_from_market(
                symbol=symbol,
                snapshot=snapshot,
                market=market,
                market_regime_snapshot=market_regime_snapshot,
            )
            return pack, context, thesis, levels, HybridSignalResult(source="market", reason="ok", side=side)
        except Exception as exc:  # noqa: BLE001
            pack, context, thesis, levels = self.demo_service.build_signal_pack(symbol)
            # Los presets demo actuales solo representan escenarios alcistas, por diseño.
            side = "long"
            return pack, context, thesis, levels, HybridSignalResult(
                source="demo", reason=self._exception_reason(exc), side=side
            )


    @staticmethod
    def _exception_reason(exc: Exception) -> str:
        if isinstance(exc, BaseExceptionGroup) and exc.exceptions:
            first = exc.exceptions[0]
            return str(first)
        return str(exc)

    async def _safe_get_market_regime_snapshot(self, symbol: str) -> dict | None:
        try:
            return await self.api_client.get_market_regime_snapshot(
                symbol,
                timeframe=self.timeframe,
                limit=self.limit,
            )
        except Exception:  # noqa: BLE001
            logger.warning("market_regime_snapshot_unavailable; fallback sin régimen para %s", symbol)
            return None

    @staticmethod
    def _is_snapshot_usable(snapshot: dict | None) -> bool:
        if not snapshot:
            return False
        required_fields = ["trend_bias", "momentum_bias", "volatility_regime"]
        if any(snapshot.get(field) in (None, "unknown") for field in required_fields):
            return False
        if snapshot.get("last_candle_close_ms") in (None, "unknown"):
            return False

        atr_pct = snapshot.get("atr_pct")
        if atr_pct in (None, "unknown"):
            return False
        try:
            float(atr_pct)
        except (TypeError, ValueError):
            return False
        return True

    def _build_from_market(
        self,
        symbol: str,
        snapshot: dict,
        market: dict,
        market_regime_snapshot: dict | None,
    ) -> tuple[SignalPack, MarketContext, str, dict[str, float], str]:
        trend_bias = snapshot.get("trend_bias", "unknown")
        momentum_bias = snapshot.get("momentum_bias", "unknown")
        vol_regime = snapshot.get("volatility_regime", "unknown")
        ema_spread_pct = self._coerce_optional_number(snapshot.get("ema_spread_pct"), default=None)
        atr_pct = float(snapshot["atr_pct"])
        rsi_14 = self._coerce_optional_number(snapshot.get("rsi_14"), default=None)
        momentum_10 = self._coerce_optional_number(snapshot.get("momentum_10"), default=0.0)

        technical = self._technical_score(trend_bias, momentum_bias, rsi_14=rsi_14, momentum_10=momentum_10)
        fundamental = 50.0
        sentiment = 50.0
        confidence = self._confidence_score(vol_regime, atr_pct)

        volatility_pct = max(0.0, atr_pct)
        trend_strength = self._trend_strength(ema_spread_pct)
        liquidity_score = self._liquidity_score(market)

        regime = None
        regime_confidence = None
        if isinstance(market_regime_snapshot, dict):
            raw_regime = market_regime_snapshot.get("regime")
            regime = raw_regime if isinstance(raw_regime, str) else None
            regime_confidence = self._coerce_optional_number(market_regime_snapshot.get("regime_confidence"), default=None)
            if regime_confidence is not None:
                regime_confidence = max(0.0, min(100.0, regime_confidence))

        context = MarketContext(
            symbol=symbol,
            timeframe=snapshot.get("timeframe") or self.timeframe,
            volatility_pct=volatility_pct,
            trend_strength=trend_strength,
            liquidity_score=liquidity_score,
            market_regime=regime,
            regime_confidence=regime_confidence,
        )

        entry = self._entry_price(market)
        side = "short" if trend_bias == "bearish" and momentum_bias == "bearish" else "long"
        levels = self._levels_from_atr(entry, atr_pct, side)

        thesis = self._thesis(trend_bias, momentum_bias, vol_regime)
        pack = SignalPack(technical=technical, fundamental=fundamental, sentiment=sentiment, confidence=confidence)
        return pack, context, thesis, levels, side

    @staticmethod
    def _entry_price(market: dict | None) -> float:
        if not market:
            raise ValueError("market_snapshot_missing")
        for key in ("mark_price", "last_price", "index_price"):
            value = market.get(key)
            if value is not None:
                return float(value)
        logger.warning("market snapshot sin precio reconocible; claves disponibles: %s", sorted(market.keys()))
        raise ValueError("market_snapshot_missing_price")

    @staticmethod
    @overload
    def _coerce_optional_number(value: object, *, default: None) -> float | None: ...

    @staticmethod
    @overload
    def _coerce_optional_number(value: object, *, default: float) -> float: ...

    @staticmethod
    def _coerce_optional_number(value: object, *, default: float | None) -> float | None:
        if value in (None, "unknown"):
            return default
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _normalize_atr_fraction(atr_pct: float) -> float:
        """Convierte `atr_pct` del API a fracción decimal.

        Contrato actual del endpoint `/signals/{symbol}`:
        - `atr_pct` se publica como porcentaje real (`ATR / EMA * 100`)
        - ejemplos: `2.5` = 2.5%, `0.8` = 0.8%, `0.01` = 0.01%

        Por lo tanto, en el worker siempre lo normalizamos dividiendo por 100 antes
        de derivar niveles, volatilidad y penalizaciones.
        """
        return max(0.0, float(atr_pct)) / 100.0

    def _levels_from_atr(self, entry: float, atr_pct: float, side: str = "long") -> dict[str, float]:
        atr_fraction = self._normalize_atr_fraction(atr_pct)
        stop_dist = max(0.002, atr_fraction * 1.2)
        tp_dist = max(0.004, atr_fraction * 2.0)
        if side == "short":
            stop = entry * (1.0 + stop_dist)
            take_profit = entry * (1.0 - tp_dist)
        else:
            stop = entry * (1.0 - stop_dist)
            take_profit = entry * (1.0 + tp_dist)
        return {"entry": round(entry, 4), "stop": round(stop, 4), "take_profit": round(take_profit, 4)}

    @staticmethod
    def _bias_score(bias: str) -> float:
        return {"bullish": 80.0, "neutral": 55.0, "bearish": 30.0}.get(bias, 50.0)

    def _technical_score(self, trend_bias: str, momentum_bias: str, rsi_14: float | None, momentum_10: float) -> float:
        base = 0.6 * self._bias_score(trend_bias) + 0.4 * self._bias_score(momentum_bias)
        # Ajuste deliberadamente simétrico: penaliza extremos de RSI sin asumir dirección adicional del trade.
        # Escalado para ocupar efectivamente el rango objetivo [-8, +8].
        if rsi_14 is not None:
            base += max(-8.0, min(8.0, (50.0 - abs(rsi_14 - 50.0)) / 3.0 - 8.0))
        base += max(-6.0, min(6.0, momentum_10 / 2.0))
        return max(0.0, min(100.0, base))

    def _confidence_score(self, vol_regime: str, atr_pct: float) -> float:
        vol_penalty = {"low": 0.0, "medium": 6.0, "high": 12.0}.get(vol_regime, 8.0)
        atr_penalty = max(0.0, min(20.0, self._normalize_atr_fraction(atr_pct) * 200.0))
        return max(0.0, min(100.0, 75.0 - vol_penalty - atr_penalty))

    @staticmethod
    def _trend_strength(ema_spread_pct: float | None) -> float:
        # `ema_spread_pct` llega desde `/signals/{symbol}` en porcentaje real
        # (ej. 0.12 = 0.12%), no en fracción decimal.
        if ema_spread_pct is None:
            return 50.0
        return max(0.0, min(100.0, abs(float(ema_spread_pct)) * 40.0))

    @staticmethod
    def _liquidity_score(market: dict | None) -> float:
        if not market:
            return 50.0
        vol = market.get("volume_24h")
        if vol is None:
            return 50.0
        # Escala más gradual para diferenciar volúmenes reales de crypto sin saturar demasiado rápido.
        score = (math.log10(float(vol) + 1.0) - 3.0) * 12.5
        return max(0.0, min(100.0, score))

    @staticmethod
    def _thesis(trend_bias: str, momentum_bias: str, vol_regime: str) -> str:
        return (
            f"Setup market-driven ({trend_bias}/{momentum_bias}) con régimen de volatilidad {vol_regime}. "
            "Plan generado desde snapshot de señales y niveles basados en ATR."
        )
