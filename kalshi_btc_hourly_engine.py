import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from kalshi_client import KalshiClient, best_bid, discover_btc_hourly_markets


ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

JOURNAL_PATH = Path(os.getenv("KALSHI_PAPER_JOURNAL_PATH", ROOT / "kalshi_btc_hourly_journal.jsonl"))
POLL_SECONDS = float(os.getenv("KALSHI_POLL_SECONDS", "5"))
MAX_NOTIONAL = float(os.getenv("KALSHI_MAX_ORDER_NOTIONAL", "20"))
MIN_LARGE_TRADE_QTY = int(float(os.getenv("KALSHI_LARGE_TRADE_QTY", "100")))


def _trade_quantity(trade):
    for key in ("count", "quantity", "contracts", "yes_count", "no_count"):
        value = trade.get(key)
        if value is not None:
            try:
                return int(float(value))
            except (TypeError, ValueError):
                return 0
    return 0


def large_trade_context(trades):
    rows = trades.get("trades", []) if isinstance(trades, dict) else []
    large = [trade for trade in rows if _trade_quantity(trade) >= MIN_LARGE_TRADE_QTY]
    if not large:
        return {
            "large_trade_seen": False,
            "large_trade_count": 0,
            "largest_trade_quantity": 0,
            "large_trade_side": "none",
        }
    largest = max(large, key=_trade_quantity)
    return {
        "large_trade_seen": True,
        "large_trade_count": len(large),
        "largest_trade_quantity": _trade_quantity(largest),
        "large_trade_side": str(largest.get("side") or largest.get("taker_side") or "unknown").lower(),
    }


def expected_contracts(price):
    if not price or price <= 0:
        return 0
    return int(MAX_NOTIONAL // price)


def build_snapshot(client):
    markets = discover_btc_hourly_markets(client)
    if not markets:
        return {"status": "no_btc_hourly_market", "markets_found": 0}

    market = markets[0]
    ticker = market["ticker"]
    orderbook = client.orderbook(ticker, depth=20)
    trades = client.trades(ticker, limit=100)
    yes_bid = best_bid(orderbook, "yes")
    no_bid = best_bid(orderbook, "no")
    flow = large_trade_context(trades)
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ticker": ticker,
        "event_ticker": market.get("event_ticker"),
        "series_ticker": market.get("series_ticker"),
        "title": market.get("title") or market.get("subtitle"),
        "close_time": market.get("close_time") or market.get("expiration_time"),
        "yes_bid": yes_bid,
        "no_bid": no_bid,
        "max_notional": MAX_NOTIONAL,
        "paper_yes_contracts": expected_contracts(yes_bid["price"]),
        "paper_no_contracts": expected_contracts(no_bid["price"]),
        **flow,
    }


def write_snapshot(snapshot):
    JOURNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with JOURNAL_PATH.open("a", encoding="utf-8") as journal:
        journal.write(json.dumps(snapshot, sort_keys=True) + "\n")


def run():
    client = KalshiClient()
    status = client.exchange_status()
    print("[KALSHI] BTC hourly paper engine online")
    print(f"[KALSHI] Exchange active={status.get('exchange_active')} trading active={status.get('trading_active')}")
    print(f"[KALSHI] Journal: {JOURNAL_PATH}")
    print("[KALSHI] Real Kalshi data only. No real orders are submitted by this engine.")

    while True:
        try:
            snapshot = build_snapshot(client)
            if snapshot.get("status") != "ok":
                print(f"[KALSHI] {snapshot.get('status')} markets={snapshot.get('markets_found')}")
                time.sleep(POLL_SECONDS)
                continue
            write_snapshot(snapshot)
            print(
                f"[KALSHI] {snapshot['ticker']} YES bid={snapshot['yes_bid']['price']} "
                f"NO bid={snapshot['no_bid']['price']} large_trade={snapshot['large_trade_seen']} "
                f"side={snapshot['large_trade_side']}"
            )
        except Exception as exc:
            print(f"[KALSHI ERROR] {exc}")
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    run()
