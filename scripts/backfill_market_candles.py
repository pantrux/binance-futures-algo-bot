#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.parse
import urllib.request


def positive_limit(value: str) -> int:
    parsed = int(value)
    if parsed <= 0 or parsed > 10000:
        raise argparse.ArgumentTypeError("--limit debe estar entre 1 y 10000")
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill market candles vía API del bot")
    parser.add_argument("--api-base-url", default="http://127.0.0.1:8000", help="Base URL del API")
    parser.add_argument("--symbols", default="BTCUSDT,ETHUSDT,SOLUSDT", help="CSV de símbolos")
    parser.add_argument("--timeframes", default="15m", help="CSV de timeframes")
    parser.add_argument("--limit", type=positive_limit, default=1000, help="Cantidad de candles a pedir por símbolo/timeframe")
    args = parser.parse_args()

    base_url = args.api_base_url.rstrip("/")
    parsed_base_url = urllib.parse.urlparse(base_url)
    if parsed_base_url.scheme not in {"http", "https"}:
        raise SystemExit("--api-base-url debe usar esquema http:// o https://")

    symbols = [item.strip().upper() for item in args.symbols.split(",") if item.strip()]
    timeframes = [item.strip() for item in args.timeframes.split(",") if item.strip()]

    results: list[dict] = []
    exit_code = 0
    for symbol in symbols:
        for timeframe in timeframes:
            query = urllib.parse.urlencode({"timeframe": timeframe, "limit": args.limit})
            url = f"{base_url}/market/ingest/{symbol}?{query}"
            req = urllib.request.Request(url, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=60) as response:
                    payload = json.loads(response.read().decode())
                    results.append({
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "status": response.status,
                        "candles_inserted": payload.get("candles_inserted", 0),
                        "snapshot_saved": payload.get("snapshot_saved", False),
                    })
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")
                results.append({
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "status": exc.code,
                    "error": body,
                })
                exit_code = 1
            except Exception as exc:  # noqa: BLE001
                results.append({
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "status": "error",
                    "error": repr(exc),
                })
                exit_code = 1

    print(json.dumps(results, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
