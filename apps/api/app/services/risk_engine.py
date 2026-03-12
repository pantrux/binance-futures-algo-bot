import logging
from dataclasses import dataclass

from apps.api.app.schemas.trading import MarketState, RiskDecision, SignalSnapshot

logger = logging.getLogger(__name__)


@dataclass
class RiskPolicy:
    max_account_risk_pct: float = 5.0
    base_risk_per_trade_pct: float = 1.0
    max_single_trade_pct: float = 1.25
    min_score_to_trade: float = 60.0


class RiskEngine:
    def __init__(self, policy: RiskPolicy | None = None):
        self.policy = policy or RiskPolicy()

    @staticmethod
    def _normalize_regime_alias(raw_regime: str | None) -> str | None:
        if raw_regime is None:
            return None
        normalized = str(raw_regime).strip().lower()
        aliases = {
            "tendencia": "tendencia_alcista",
            "tendencia_fuerte": "tendencia_alcista",
            "rango": "rango_lateral",
        }
        normalized = aliases.get(normalized, normalized)
        allowed = {
            "tendencia_alcista",
            "tendencia_bajista",
            "rango_lateral",
            "transicion",
            "alta_volatilidad",
            "unknown",
        }
        if normalized in allowed:
            return normalized

        logger.warning(
            "_normalize_regime_alias: régimen no reconocido '%s'; se ignorará y se usará clasificación interna",
            raw_regime,
        )
        return None

    def classify_market_regime(self, market_state: MarketState) -> str:
        if market_state.volatility_pct >= 4.0:
            return "alta_volatilidad"
        if market_state.trend_strength >= 70:
            # Fallback sin dirección: `trend_strength` no distingue alcista/bajista por sí solo.
            # Si el caller conoce dirección real, debe proveer `market_regime` explícito.
            return "tendencia_alcista"
        if market_state.trend_strength <= 35:
            return "rango_lateral"
        return "transicion"

    def resolve_market_regime(self, market_state: MarketState) -> str:
        provided = self._normalize_regime_alias(market_state.market_regime)
        if provided is not None:
            return provided
        return self.classify_market_regime(market_state)

    def estimate_regime_confidence(self, *, market_state: MarketState, regime: str) -> float:
        if market_state.regime_confidence is not None:
            return max(0.0, min(100.0, float(market_state.regime_confidence)))

        volatility_score = max(0.0, min(100.0, market_state.volatility_pct * 18.0))
        inverse_volatility = 100.0 - volatility_score

        if regime == "alta_volatilidad":
            return round(volatility_score, 4)
        if regime in {"tendencia_alcista", "tendencia_bajista"}:
            return round(max(0.0, min(100.0, (market_state.trend_strength * 0.6) + (inverse_volatility * 0.4))), 4)
        if regime == "rango_lateral":
            return round(
                max(
                    0.0,
                    min(100.0, ((100.0 - market_state.trend_strength) * 0.6) + (inverse_volatility * 0.4)),
                ),
                4,
            )
        if regime == "transicion":
            trend_ambiguity = 100.0 - abs(market_state.trend_strength - 50.0) * 2.0
            return round(max(0.0, min(100.0, (trend_ambiguity * 0.55) + (inverse_volatility * 0.45))), 4)
        return 0.0

    def aggregate_score(self, signals: SignalSnapshot, market_state: MarketState) -> float:
        weights = {
            "technical": 0.40,
            "fundamental": 0.20,
            "sentiment": 0.20,
            "confidence": 0.15,
            "liquidity": 0.05,
        }
        return round(
            signals.technical * weights["technical"]
            + signals.fundamental * weights["fundamental"]
            + signals.sentiment * weights["sentiment"]
            + signals.confidence * weights["confidence"]
            + market_state.liquidity_score * weights["liquidity"],
            2,
        )

    @staticmethod
    def _score_multiplier(score: float, min_score_to_trade: float) -> float:
        if score < min_score_to_trade:
            return 0.0

        if score >= min_score_to_trade + 25:
            return 1.15
        if score >= min_score_to_trade + 15:
            return 1.0
        if score >= min_score_to_trade + 5:
            return 0.8
        return 0.65

    @staticmethod
    def _regime_multiplier(regime: str, regime_confidence: float) -> float:
        if regime == "unknown":
            return 0.0

        if regime == "alta_volatilidad":
            if regime_confidence >= 70:
                return 0.45
            if regime_confidence >= 50:
                return 0.6
            # Cerca del umbral de alta volatilidad (confidence más baja), degradamos menos agresivo.
            return 0.75

        if regime == "transicion":
            return 0.75 if regime_confidence >= 70 else 0.85

        if regime == "rango_lateral":
            return 0.8

        if regime in {"tendencia_alcista", "tendencia_bajista"}:
            if regime_confidence >= 75:
                return 1.05
            if regime_confidence < 45:
                return 0.95
            return 1.0

        # Fallback defensivo: solo alcanzable si se agrega un régimen nuevo sin actualizar esta función.
        logger.warning("_regime_multiplier: régimen no reconocido '%s'; aplicando multiplicador 0.9", regime)
        return 0.9

    @staticmethod
    def _volatility_multiplier(volatility_pct: float) -> float:
        if volatility_pct >= 5.0:
            return 0.45
        if volatility_pct >= 4.0:
            return 0.6
        if volatility_pct >= 3.0:
            return 0.75
        if volatility_pct >= 2.0:
            return 0.9
        return 1.0

    def suggest_risk_pct(self, *, score: float, regime: str, regime_confidence: float, volatility_pct: float) -> float:
        score_mult = self._score_multiplier(score, self.policy.min_score_to_trade)
        regime_mult = self._regime_multiplier(regime, regime_confidence)
        vol_mult = self._volatility_multiplier(volatility_pct)

        # Guardrail defensivo: si la volatilidad observada ya es alta, un régimen explícito
        # no puede habilitar un multiplicador más agresivo que el permitido para alta volatilidad.
        if volatility_pct >= 4.0:
            # El cap de alta volatilidad debe depender de la volatilidad observada,
            # no de la confianza del régimen explícito (que puede venir desfasada o faltar).
            vol_based_confidence = max(0.0, min(100.0, volatility_pct * 18.0))
            high_vol_cap = self._regime_multiplier("alta_volatilidad", vol_based_confidence)
            regime_mult = min(regime_mult, high_vol_cap)

        if score_mult <= 0 or regime_mult <= 0:
            return 0.0

        suggested = self.policy.base_risk_per_trade_pct * score_mult * regime_mult * vol_mult
        return round(min(suggested, self.policy.max_single_trade_pct), 4)

    def evaluate(
        self,
        *,
        capital_usdt: float,
        existing_risk_pct: float,
        signals: SignalSnapshot,
        market_state: MarketState,
        entry_price: float,
        stop_loss: float,
    ) -> RiskDecision:
        regime = self.resolve_market_regime(market_state)
        regime_confidence = self.estimate_regime_confidence(market_state=market_state, regime=regime)
        score = self.aggregate_score(signals, market_state)
        suggested_risk_pct = self.suggest_risk_pct(
            score=score,
            regime=regime,
            regime_confidence=regime_confidence,
            volatility_pct=market_state.volatility_pct,
        )

        if suggested_risk_pct == 0:
            return RiskDecision(
                approved=False,
                max_position_notional=0,
                suggested_risk_pct=0,
                reason="Score/régimen insuficiente para abrir operación",
                market_regime=regime,
                score=score,
                regime_confidence=regime_confidence,
            )

        available_risk_pct = max(self.policy.max_account_risk_pct - existing_risk_pct, 0)
        applied_risk_pct = min(suggested_risk_pct, available_risk_pct)

        if applied_risk_pct <= 0:
            return RiskDecision(
                approved=False,
                max_position_notional=0,
                suggested_risk_pct=0,
                reason="Sin margen de riesgo disponible dentro del límite global del 5%",
                market_regime=regime,
                score=score,
                regime_confidence=regime_confidence,
            )

        stop_distance = abs(entry_price - stop_loss)
        if stop_distance <= 0:
            return RiskDecision(
                approved=False,
                max_position_notional=0,
                suggested_risk_pct=0,
                reason="Stop loss inválido: distancia cero",
                market_regime=regime,
                score=score,
                regime_confidence=regime_confidence,
            )

        capital_at_risk = capital_usdt * (applied_risk_pct / 100)
        quantity = capital_at_risk / stop_distance
        notional = round(quantity * entry_price, 2)

        return RiskDecision(
            approved=True,
            max_position_notional=notional,
            suggested_risk_pct=applied_risk_pct,
            reason="Operación aprobada por el motor de riesgo",
            market_regime=regime,
            score=score,
            regime_confidence=regime_confidence,
        )
