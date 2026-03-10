from dataclasses import asdict, dataclass

from trading_bot.engines.market_regime import MarketRegimeClassifier
from trading_bot.models.signals import MarketContext, SignalPack


@dataclass
class TradeBlueprint:
    symbol: str
    regime: str
    thesis: str
    allowed: bool


class PlanService:
    def __init__(self) -> None:
        self.regime_classifier = MarketRegimeClassifier()

    def build_plan(self, symbol: str, signals: SignalPack, context: MarketContext) -> dict:
        regime = self.regime_classifier.classify(context)
        score = round(signals.technical * 0.45 + signals.fundamental * 0.2 + signals.sentiment * 0.2 + signals.confidence * 0.15, 2)
        allowed = score >= 60 and regime != "alta_volatilidad"
        thesis = (
            "Setup habilitado: confluencia suficiente para evaluar entrada controlada"
            if allowed
            else "Setup bloqueado: score insuficiente o volatilidad no apta"
        )
        return asdict(TradeBlueprint(symbol=symbol, regime=regime, thesis=thesis, allowed=allowed))
