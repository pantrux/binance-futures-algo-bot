from apps.worker.trading_bot.services.demo_signal_service import DemoSignalService


def test_demo_signal_service_sets_stable_last_candle_close_ms():
    service = DemoSignalService()

    for symbol in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
        _, context, _, _ = service.build_signal_pack(symbol)
        assert context.last_candle_close_ms == 0
