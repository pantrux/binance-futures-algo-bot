from apps.worker.trading_bot.models.signals import MarketContext, SignalPack


class DemoSignalService:
    def build_signal_pack(self, symbol: str) -> tuple[SignalPack, MarketContext, str, dict[str, float]]:
        presets = {
            "BTCUSDT": {
                "signals": SignalPack(technical=82, fundamental=68, sentiment=77, confidence=80),
                "context": MarketContext(symbol="BTCUSDT", timeframe="15m", volatility_pct=2.7, trend_strength=74, liquidity_score=93),
                "thesis": "Breakout intradía con confirmación de tendencia y sentimiento favorable.",
                "levels": {"entry": 50000, "stop": 49750, "take_profit": 50650},
            },
            "ETHUSDT": {
                "signals": SignalPack(technical=76, fundamental=64, sentiment=71, confidence=74),
                "context": MarketContext(symbol="ETHUSDT", timeframe="15m", volatility_pct=2.3, trend_strength=69, liquidity_score=89),
                "thesis": "Continuación controlada con momentum positivo y volatilidad manejable.",
                "levels": {"entry": 3200, "stop": 3175, "take_profit": 3260},
            },
            "SOLUSDT": {
                "signals": SignalPack(technical=71, fundamental=58, sentiment=73, confidence=69),
                "context": MarketContext(symbol="SOLUSDT", timeframe="15m", volatility_pct=3.1, trend_strength=65, liquidity_score=86),
                "thesis": "Setup de continuación con mayor volatilidad, apto solo para tamaño controlado.",
                "levels": {"entry": 140, "stop": 137.5, "take_profit": 145.5},
            },
        }
        selected = presets.get(symbol, presets["BTCUSDT"])
        return selected["signals"], selected["context"], selected["thesis"], selected["levels"]
