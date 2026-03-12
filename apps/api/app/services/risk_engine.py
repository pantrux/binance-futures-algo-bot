import logging
from dataclasses import dataclass

from apps.api.app.schemas.trading import MarketState, PortfolioState, PositionExposure, RiskDecision, RiskEventDetail, SignalSnapshot

logger = logging.getLogger(__name__)


@dataclass
class RiskPolicy:
    max_account_risk_pct: float = 5.0
    base_risk_per_trade_pct: float = 1.0
    max_single_trade_pct: float = 1.25
    min_score_to_trade: float = 60.0
    default_max_cluster_risk_pct: float = 2.5
    default_max_symbol_risk_pct: float = 1.5
    high_volatility_threshold_pct: float = 4.0


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
        if market_state.volatility_pct >= self.policy.high_volatility_threshold_pct:
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

    @staticmethod
    def _symbol_cluster(symbol: str) -> str:
        token = symbol.upper().removesuffix("USDT")
        if token.startswith("BTC"):
            return "BTC_CORE"
        if token.startswith("ETH"):
            return "ETH_CORE"
        if token in {"BNB", "SOL", "XRP", "ADA", "DOGE", "LINK", "AVAX"}:
            return "LARGE_ALT"
        return "ALTS"

    @classmethod
    def _correlation_coefficient(cls, lhs_cluster: str, rhs_cluster: str) -> float:
        if lhs_cluster == rhs_cluster:
            return 0.95

        pair = frozenset({lhs_cluster, rhs_cluster})
        table = {
            frozenset({"BTC_CORE", "ETH_CORE"}): 0.75,
            frozenset({"BTC_CORE", "LARGE_ALT"}): 0.6,
            frozenset({"ETH_CORE", "LARGE_ALT"}): 0.65,
            frozenset({"BTC_CORE", "ALTS"}): 0.5,
            frozenset({"ETH_CORE", "ALTS"}): 0.55,
            frozenset({"LARGE_ALT", "ALTS"}): 0.7,
        }
        return table.get(pair, 0.45)

    @classmethod
    def _correlation_multiplier(cls, *, symbol: str, positions: list[PositionExposure]) -> tuple[float, float]:
        if not positions:
            return 1.0, 0.0

        target_cluster = cls._symbol_cluster(symbol)
        aggregated_pressure = 0.0
        for position in positions:
            source_cluster = cls._symbol_cluster(position.symbol)
            coeff = cls._correlation_coefficient(target_cluster, source_cluster)
            weighted = coeff * max(0.0, min(1.0, position.risk_pct / 5.0))
            aggregated_pressure += weighted

        normalized_pressure = min(1.0, aggregated_pressure)

        if normalized_pressure >= 0.8:
            return 0.72, normalized_pressure
        if normalized_pressure >= 0.6:
            return 0.84, normalized_pressure
        if normalized_pressure >= 0.45:
            return 0.92, normalized_pressure
        return 1.0, normalized_pressure

    @classmethod
    def _portfolio_metrics(
        cls,
        *,
        symbol: str,
        existing_risk_pct: float,
        positions: list[PositionExposure],
    ) -> dict[str, float | str]:
        symbol_upper = symbol.upper()
        cluster_key = cls._symbol_cluster(symbol_upper)

        sum_positions_risk = round(sum(position.risk_pct for position in positions), 4)
        portfolio_before = round(max(existing_risk_pct, sum_positions_risk), 4)

        symbol_before = round(
            sum(position.risk_pct for position in positions if position.symbol.upper() == symbol_upper),
            4,
        )
        cluster_before = round(
            sum(position.risk_pct for position in positions if cls._symbol_cluster(position.symbol) == cluster_key),
            4,
        )

        return {
            "cluster_key": cluster_key,
            "portfolio_before": portfolio_before,
            "symbol_before": symbol_before,
            "cluster_before": cluster_before,
        }

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
        if regime == "unknown":
            return 0.0

        # Fallback defensivo: solo alcanzable si se agrega un régimen nuevo sin actualizar esta función.
        logger.warning(
            "estimate_regime_confidence: régimen no reconocido '%s'; retornando confianza neutral 50.0",
            regime,
        )
        return 50.0

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
        if volatility_pct >= self.policy.high_volatility_threshold_pct:
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
        symbol: str | None = None,
        side: str | None = None,
        portfolio_state: PortfolioState | None = None,
    ) -> RiskDecision:
        regime = self.resolve_market_regime(market_state)
        regime_confidence = self.estimate_regime_confidence(market_state=market_state, regime=regime)
        score = self.aggregate_score(signals, market_state)

        normalized_symbol = (symbol or market_state.symbol).upper()
        normalized_side = (side or "long").lower()
        _ = normalized_side  # reservado para futuras reglas side-aware

        portfolio_state = portfolio_state or PortfolioState(
            max_portfolio_risk_pct=self.policy.max_account_risk_pct,
            max_cluster_risk_pct=self.policy.default_max_cluster_risk_pct,
            max_symbol_risk_pct=self.policy.default_max_symbol_risk_pct,
        )
        positions = portfolio_state.positions
        portfolio_metrics = self._portfolio_metrics(
            symbol=normalized_symbol,
            existing_risk_pct=existing_risk_pct,
            positions=positions,
        )
        cluster_key = str(portfolio_metrics["cluster_key"])
        portfolio_before = float(portfolio_metrics["portfolio_before"])
        symbol_before = float(portfolio_metrics["symbol_before"])
        cluster_before = float(portfolio_metrics["cluster_before"])

        risk_events: list[RiskEventDetail] = []
        correlation_multiplier = 1.0

        suggested_risk_pct = self.suggest_risk_pct(
            score=score,
            regime=regime,
            regime_confidence=regime_confidence,
            volatility_pct=market_state.volatility_pct,
        )

        if portfolio_state.correlation_guard_enabled:
            correlation_multiplier, correlation_pressure = self._correlation_multiplier(
                symbol=normalized_symbol,
                positions=positions,
            )
            if correlation_multiplier < 1.0 and suggested_risk_pct > 0:
                suggested_risk_pct = round(suggested_risk_pct * correlation_multiplier, 4)
                risk_events.append(
                    RiskEventDetail(
                        event_type="correlation_pressure",
                        severity="warning",
                        message="Sizing degradado por presión de correlación en portafolio",
                        context={
                            "symbol": normalized_symbol,
                            "cluster_key": cluster_key,
                            "correlation_pressure": round(correlation_pressure, 4),
                            "correlation_multiplier": correlation_multiplier,
                        },
                    )
                )

        max_portfolio_risk_pct = min(self.policy.max_account_risk_pct, portfolio_state.max_portfolio_risk_pct)
        max_cluster_risk_pct = min(max_portfolio_risk_pct, portfolio_state.max_cluster_risk_pct)
        max_symbol_risk_pct = min(max_portfolio_risk_pct, portfolio_state.max_symbol_risk_pct)

        available_policy = max(self.policy.max_account_risk_pct - existing_risk_pct, 0.0)
        available_portfolio = max(max_portfolio_risk_pct - portfolio_before, 0.0)
        available_symbol = max(max_symbol_risk_pct - symbol_before, 0.0)
        available_cluster = max(max_cluster_risk_pct - cluster_before, 0.0)

        available_risk_pct = min(available_policy, available_portfolio, available_symbol, available_cluster)

        if suggested_risk_pct == 0:
            risk_events.append(
                RiskEventDetail(
                    event_type="risk_gate_score_or_regime",
                    severity="critical",
                    message="Score/régimen insuficiente para abrir operación",
                    context={"score": score, "market_regime": regime, "regime_confidence": regime_confidence},
                )
            )
            return RiskDecision(
                approved=False,
                max_position_notional=0,
                suggested_risk_pct=0,
                reason="Score/régimen insuficiente para abrir operación",
                market_regime=regime,
                score=score,
                regime_confidence=regime_confidence,
                portfolio_risk_pct_before=portfolio_before,
                portfolio_risk_pct_after=portfolio_before,
                cluster_key=cluster_key,
                cluster_risk_pct_before=cluster_before,
                cluster_risk_pct_after=cluster_before,
                symbol_risk_pct_before=symbol_before,
                symbol_risk_pct_after=symbol_before,
                correlation_multiplier=correlation_multiplier,
                risk_events=risk_events,
            )

        if available_risk_pct <= 0:
            if available_symbol <= 0:
                reason = "Bloqueado por límite de riesgo por símbolo"
                event_type = "symbol_risk_limit_breached"
                context = {"symbol": normalized_symbol, "symbol_risk_before": symbol_before, "max_symbol_risk_pct": max_symbol_risk_pct}
            elif available_cluster <= 0:
                reason = "Bloqueado por límite de riesgo por clúster correlacionado"
                event_type = "cluster_risk_limit_breached"
                context = {
                    "symbol": normalized_symbol,
                    "cluster_key": cluster_key,
                    "cluster_risk_before": cluster_before,
                    "max_cluster_risk_pct": max_cluster_risk_pct,
                }
            else:
                reason = "Sin margen de riesgo disponible dentro del límite global de portafolio"
                event_type = "portfolio_risk_limit_breached"
                context = {
                    "portfolio_risk_before": portfolio_before,
                    "max_portfolio_risk_pct": max_portfolio_risk_pct,
                    "available_policy_risk_pct": round(available_policy, 4),
                }

            risk_events.append(RiskEventDetail(event_type=event_type, severity="critical", message=reason, context=context))
            return RiskDecision(
                approved=False,
                max_position_notional=0,
                suggested_risk_pct=0,
                reason=reason,
                market_regime=regime,
                score=score,
                regime_confidence=regime_confidence,
                portfolio_risk_pct_before=portfolio_before,
                portfolio_risk_pct_after=portfolio_before,
                cluster_key=cluster_key,
                cluster_risk_pct_before=cluster_before,
                cluster_risk_pct_after=cluster_before,
                symbol_risk_pct_before=symbol_before,
                symbol_risk_pct_after=symbol_before,
                correlation_multiplier=correlation_multiplier,
                risk_events=risk_events,
            )

        applied_risk_pct = min(suggested_risk_pct, available_risk_pct)

        portfolio_after = round(portfolio_before + applied_risk_pct, 4)
        symbol_after = round(symbol_before + applied_risk_pct, 4)
        cluster_after = round(cluster_before + applied_risk_pct, 4)

        if applied_risk_pct < suggested_risk_pct:
            risk_events.append(
                RiskEventDetail(
                    event_type="risk_pct_capped_by_portfolio",
                    severity="warning",
                    message="Sizing recortado por límites agregados de portafolio/correlación",
                    context={
                        "suggested_risk_pct": suggested_risk_pct,
                        "applied_risk_pct": applied_risk_pct,
                        "cluster_key": cluster_key,
                    },
                )
            )

        stop_distance = abs(entry_price - stop_loss)
        if stop_distance <= 0:
            risk_events.append(
                RiskEventDetail(
                    event_type="invalid_stop_distance",
                    severity="critical",
                    message="Stop loss inválido: distancia cero",
                    context={"entry_price": entry_price, "stop_loss": stop_loss},
                )
            )
            return RiskDecision(
                approved=False,
                max_position_notional=0,
                suggested_risk_pct=0,
                reason="Stop loss inválido: distancia cero",
                market_regime=regime,
                score=score,
                regime_confidence=regime_confidence,
                portfolio_risk_pct_before=portfolio_before,
                portfolio_risk_pct_after=portfolio_before,
                cluster_key=cluster_key,
                cluster_risk_pct_before=cluster_before,
                cluster_risk_pct_after=cluster_before,
                symbol_risk_pct_before=symbol_before,
                symbol_risk_pct_after=symbol_before,
                correlation_multiplier=correlation_multiplier,
                risk_events=risk_events,
            )

        capital_at_risk = capital_usdt * (applied_risk_pct / 100)
        quantity = capital_at_risk / stop_distance
        notional = round(quantity * entry_price, 2)

        risk_events.append(
            RiskEventDetail(
                event_type="portfolio_risk_approved",
                severity="info",
                message="Operación aprobada respetando límites de riesgo de portafolio",
                context={
                    "cluster_key": cluster_key,
                    "portfolio_risk_after": portfolio_after,
                    "cluster_risk_after": cluster_after,
                    "symbol_risk_after": symbol_after,
                },
            )
        )

        return RiskDecision(
            approved=True,
            max_position_notional=notional,
            suggested_risk_pct=applied_risk_pct,
            reason="Operación aprobada por el motor de riesgo",
            market_regime=regime,
            score=score,
            regime_confidence=regime_confidence,
            portfolio_risk_pct_before=portfolio_before,
            portfolio_risk_pct_after=portfolio_after,
            cluster_key=cluster_key,
            cluster_risk_pct_before=cluster_before,
            cluster_risk_pct_after=cluster_after,
            symbol_risk_pct_before=symbol_before,
            symbol_risk_pct_after=symbol_after,
            correlation_multiplier=correlation_multiplier,
            risk_events=risk_events,
        )
