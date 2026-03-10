from trading_bot.models.signals import SignalPack


class SignalAggregator:
    def aggregate(self, technical: float, fundamental: float, sentiment: float, confidence: float) -> SignalPack:
        return SignalPack(
            technical=max(0, min(technical, 100)),
            fundamental=max(0, min(fundamental, 100)),
            sentiment=max(0, min(sentiment, 100)),
            confidence=max(0, min(confidence, 100)),
        )
