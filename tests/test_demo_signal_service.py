from apps.worker.trading_bot.services.demo_signal_service import DemoSignalService


def test_demo_signal_service_sets_stable_last_candle_close_ms():
    _, context, _, _ = DemoSignalService().build_signal_pack("BTCUSDT")

    assert context.last_candle_close_ms == 0
