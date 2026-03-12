from sqlalchemy.orm import Session

from apps.api.app.schemas.indicators import IndicatorSnapshot
from apps.api.app.schemas.market_regime import MarketRegimeSnapshot
from apps.api.app.schemas.signals import SignalSnapshot
from apps.api.app.services.indicator_service import IndicatorService
from apps.api.app.services.signal_service import SignalService


class MarketRegimeService:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _trend_strength(ema_spread_pct: float | None) -> float:
        if ema_spread_pct is None:
            return 50.0
        return max(0.0, min(100.0, abs(float(ema_spread_pct)) * 40.0))

    @staticmethod
    def _volatility_score(atr_pct: float | None) -> float:
        if atr_pct is None:
            return 50.0
        # atr_pct llega como porcentaje real (ej: 2.5 = 2.5%)
        return max(0.0, min(100.0, float(atr_pct) * 18.0))

    @staticmethod
    def _momentum_score(rsi_14: float | None, momentum_10_pct: float | None) -> float:
        if rsi_14 is None and momentum_10_pct is None:
            return 50.0

        rsi_component = 50.0 if rsi_14 is None else max(0.0, min(100.0, 50.0 + ((float(rsi_14) - 50.0) * 1.4)))
        # Normalizamos momentum a % para que la escala sea comparable entre activos (BTC vs altcoins).
        # momentum_10_pct es porcentaje real (ej: 0.8 = +0.8%).
        mom_component = (
            50.0
            if momentum_10_pct is None
            else max(0.0, min(100.0, 50.0 + (float(momentum_10_pct) * 12.0)))
        )
        return round((rsi_component * 0.65) + (mom_component * 0.35), 4)

    @staticmethod
    def _classify_regime(
        *,
        trend_bias: str,
        momentum_bias: str,
        volatility_regime: str,
        trend_strength: float,
        volatility_score: float,
        momentum_score: float,
    ) -> str:
        # Guardrail: si el contexto base viene incompleto, preferimos un régimen "unknown"
        # antes de inferir direccionalidad. Esto evita decisiones erróneas en consumidores futuros
        # (por ejemplo RiskEngine) cuando falten señales/indicadores.
        if trend_bias == "unknown" or momentum_bias == "unknown" or volatility_regime == "unknown":
            return "unknown"

        if volatility_regime == "high":
            return "alta_volatilidad"

        if trend_bias == "bullish" and momentum_bias == "bullish" and trend_strength >= 58.0 and momentum_score >= 58.0:
            return "tendencia_alcista"

        if trend_bias == "bearish" and momentum_bias == "bearish" and trend_strength >= 58.0 and momentum_score <= 42.0:
            return "tendencia_bajista"

        if trend_strength <= 35.0 and volatility_score <= 55.0:
            return "rango_lateral"

        return "transicion"

    @staticmethod
    def _regime_confidence(*, regime: str, trend_strength: float, volatility_score: float, momentum_score: float) -> float:
        if regime == "unknown":
            return 0.0

        inverse_volatility = 100.0 - volatility_score

        if regime == "alta_volatilidad":
            return round(max(0.0, min(100.0, (volatility_score * 0.7) + (trend_strength * 0.3))), 4)

        if regime == "tendencia_alcista":
            return round(
                max(0.0, min(100.0, (trend_strength * 0.45) + (momentum_score * 0.35) + (inverse_volatility * 0.2))),
                4,
            )

        if regime == "tendencia_bajista":
            # `momentum_score` está centrado en 50: valores bajos significan momentum bajista más fuerte.
            # Para confianza bajista, invertimos el componente de momentum.
            bearish_momentum = 100.0 - momentum_score
            return round(
                max(0.0, min(100.0, (trend_strength * 0.45) + (bearish_momentum * 0.35) + (inverse_volatility * 0.2))),
                4,
            )

        if regime == "rango_lateral":
            return round(max(0.0, min(100.0, ((100.0 - trend_strength) * 0.5) + (inverse_volatility * 0.5))), 4)

        # "transicion" debería tener más confianza cuando el momentum es más neutral (cerca de 50)
        # y cuando la volatilidad no es excesiva.
        momentum_neutrality = max(0.0, min(100.0, 100.0 - (abs(momentum_score - 50.0) * 2.0)))
        return round(
            max(0.0, min(100.0, (trend_strength * 0.35) + (momentum_neutrality * 0.3) + (inverse_volatility * 0.35))),
            4,
        )

    def snapshot(
        self,
        symbol: str,
        timeframe: str = "15m",
        limit: int = 200,
        indicator_snapshot: IndicatorSnapshot | None = None,
        signal_snapshot: SignalSnapshot | None = None,
    ) -> MarketRegimeSnapshot:
        indicator_snapshot = indicator_snapshot or IndicatorService(self.db).snapshot(symbol=symbol, timeframe=timeframe, limit=limit)
        signal_snapshot = signal_snapshot or SignalService(self.db).snapshot(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            indicator_snapshot=indicator_snapshot,
        )

        trend_strength = self._trend_strength(signal_snapshot.ema_spread_pct)
        volatility_score = self._volatility_score(signal_snapshot.atr_pct)
        momentum_10_pct = None
        if signal_snapshot.momentum_10 is not None and indicator_snapshot.ema_21 not in (None, 0):
            momentum_10_pct = round((float(signal_snapshot.momentum_10) / float(indicator_snapshot.ema_21)) * 100.0, 6)

        momentum_score = self._momentum_score(signal_snapshot.rsi_14, momentum_10_pct)

        regime = self._classify_regime(
            trend_bias=signal_snapshot.trend_bias,
            momentum_bias=signal_snapshot.momentum_bias,
            volatility_regime=signal_snapshot.volatility_regime,
            trend_strength=trend_strength,
            volatility_score=volatility_score,
            momentum_score=momentum_score,
        )

        return MarketRegimeSnapshot(
            symbol=symbol,
            timeframe=timeframe,
            last_candle_close_ms=signal_snapshot.last_candle_close_ms,
            regime=regime,
            trend_bias=signal_snapshot.trend_bias,
            momentum_bias=signal_snapshot.momentum_bias,
            volatility_regime=signal_snapshot.volatility_regime,
            trend_strength=round(trend_strength, 4),
            volatility_score=round(volatility_score, 4),
            momentum_score=round(momentum_score, 4),
            regime_confidence=self._regime_confidence(
                regime=regime,
                trend_strength=trend_strength,
                volatility_score=volatility_score,
                momentum_score=momentum_score,
            ),
            ema_spread_pct=signal_snapshot.ema_spread_pct,
            atr_pct=signal_snapshot.atr_pct,
            rsi_14=signal_snapshot.rsi_14,
            momentum_10=signal_snapshot.momentum_10,
        )
