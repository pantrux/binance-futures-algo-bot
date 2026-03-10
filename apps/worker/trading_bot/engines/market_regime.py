from trading_bot.models.signals import MarketContext


class MarketRegimeClassifier:
    def classify(self, context: MarketContext) -> str:
        if context.volatility_pct >= 4:
            return "alta_volatilidad"
        if context.trend_strength >= 70:
            return "tendencia"
        if context.trend_strength <= 35:
            return "rango"
        return "transicion"
