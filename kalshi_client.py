import base64
import os
import time
from pathlib import Path
from urllib.parse import urlencode, urlparse

import requests
from dotenv import load_dotenv
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

DEFAULT_BASE_URL = "https://external-api.kalshi.com/trade-api/v2"
DEMO_BASE_URL = "https://external-api.demo.kalshi.co/trade-api/v2"
DEMO_WS_URL = "wss://external-api-ws.demo.kalshi.co/trade-api/ws/v2"
PROD_WS_URL = "wss://external-api-ws.kalshi.com/trade-api/ws/v2"


def _resolve_path(path):
    expanded = Path(os.path.expanduser(os.path.expandvars(str(path).strip().strip('"'))))
    if expanded.is_absolute():
        return expanded
    return ROOT / expanded


def _kalshi_env():
    return os.getenv("KALSHI_ENV", "prod").strip().lower()


def _load_private_key():
    if _kalshi_env() == "demo":
        key_path = os.getenv("KALSHI_DEMO_PRIVATE_KEY_PATH") or os.getenv("KALSHI_PRIVATE_KEY_PATH")
    else:
        key_path = os.getenv("KALSHI_PRIVATE_KEY_PATH")
    if not key_path:
        raise RuntimeError("KALSHI_PRIVATE_KEY_PATH is not set")
    resolved = _resolve_path(key_path)
    if not resolved.exists():
        raise FileNotFoundError(f"Kalshi private key file not found: {resolved}")
    return serialization.load_pem_private_key(resolved.read_bytes(), password=None)


class KalshiClient:
    def __init__(self, *, base_url=None, api_key_id=None, private_key=None):
        env = _kalshi_env()
        default_base_url = DEMO_BASE_URL if env == "demo" else DEFAULT_BASE_URL
        env_base_url = os.getenv("KALSHI_DEMO_API_BASE_URL") if env == "demo" else os.getenv("KALSHI_API_BASE_URL")
        self.base_url = (base_url or env_base_url or default_base_url).rstrip("/")
        if env == "demo":
            self.api_key_id = api_key_id or os.getenv("KALSHI_DEMO_API_KEY_ID") or os.getenv("KALSHI_API_KEY_ID")
        else:
            self.api_key_id = api_key_id or os.getenv("KALSHI_API_KEY_ID")
        self.env = env
        self._private_key = private_key

    @property
    def websocket_url(self):
        configured = os.getenv("KALSHI_DEMO_WS_URL") if self.env == "demo" else os.getenv("KALSHI_WS_URL")
        return configured or (DEMO_WS_URL if self.env == "demo" else PROD_WS_URL)

    def _path_with_query(self, path, params=None):
        if not path.startswith("/"):
            path = f"/{path}"
        if params:
            return f"{path}?{urlencode(params)}"
        return path

    def _signature_headers(self, method, path):
        if not self.api_key_id:
            raise RuntimeError("KALSHI_API_KEY_ID is not set")
        if self._private_key is None:
            self._private_key = _load_private_key()

        timestamp = str(int(time.time() * 1000))
        sign_path = urlparse(self.base_url + path).path
        message = f"{timestamp}{method.upper()}{sign_path}".encode("utf-8")
        signature = self._private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH,
            ),
            hashes.SHA256(),
        )
        return {
            "KALSHI-ACCESS-KEY": self.api_key_id,
            "KALSHI-ACCESS-TIMESTAMP": timestamp,
            "KALSHI-ACCESS-SIGNATURE": base64.b64encode(signature).decode("utf-8"),
        }

    def request(self, method, path, *, params=None, json_body=None, auth=False, timeout=10):
        path_with_query = self._path_with_query(path, params)
        headers = {"Content-Type": "application/json"}
        if auth:
            headers.update(self._signature_headers(method, path_with_query))
        response = requests.request(
            method,
            f"{self.base_url}{path_with_query}",
            headers=headers,
            json=json_body,
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()

    def exchange_status(self):
        return self.request("GET", "/exchange/status")

    def markets(self, **params):
        return self.request("GET", "/markets", params={key: value for key, value in params.items() if value is not None})

    def orderbook(self, ticker, depth=20):
        return self.request("GET", f"/markets/{ticker}/orderbook", params={"depth": depth})

    def trades(self, ticker, limit=100):
        return self.request("GET", "/markets/trades", params={"ticker": ticker, "limit": limit})

    def balance(self):
        return self.request("GET", "/portfolio/balance", auth=True)


def _market_text(market):
    parts = [
        market.get("ticker"),
        market.get("event_ticker"),
        market.get("series_ticker"),
        market.get("title"),
        market.get("subtitle"),
        market.get("yes_sub_title"),
        market.get("no_sub_title"),
    ]
    return " ".join(str(part or "") for part in parts).lower()


def discover_btc_hourly_markets(client, *, limit=1000):
    data = client.markets(status="open", limit=limit, series_ticker=os.getenv("KALSHI_BTC_SERIES_TICKER", "KXBTCD"))
    markets = data.get("markets", [])
    matches = []
    for market in markets:
        text = _market_text(market)
        if ("btc" in text or "bitcoin" in text) and (
            "hour" in text or "hourly" in text or "up or down" in text
        ):
            matches.append(market)
    return sorted(matches, key=lambda item: str(item.get("close_time") or item.get("expiration_time") or ""))


def parse_strike(ticker):
    try:
        return float(str(ticker).rsplit("-T", 1)[1])
    except (IndexError, TypeError, ValueError):
        return None


def _normalize_price(raw):
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value > 1.0:
        value = value / 100.0
    return round(value, 4)


def _levels(orderbook, side):
    book = orderbook.get("orderbook") or orderbook.get("orderbook_fp") or orderbook
    candidates = [
        book.get(side),
        book.get(f"{side}_dollars"),
        book.get(f"{side}_cents"),
    ]
    for levels in candidates:
        if isinstance(levels, list):
            return levels
    return []


def best_bid(orderbook, side):
    levels = _levels(orderbook, side)
    if not levels:
        return {"price": None, "quantity": 0}
    best = levels[-1]
    if isinstance(best, dict):
        price = best.get("price") or best.get("price_dollars") or best.get("price_cents")
        quantity = best.get("quantity") or best.get("count") or best.get("contracts") or 0
    else:
        price = best[0] if len(best) > 0 else None
        quantity = best[1] if len(best) > 1 else 0
    return {"price": _normalize_price(price), "quantity": int(float(quantity or 0))}


def orderbook_summary(orderbook):
    yes_bid = best_bid(orderbook, "yes")
    no_bid = best_bid(orderbook, "no")
    yes_ask = round(1.0 - no_bid["price"], 4) if no_bid["price"] is not None else None
    no_ask = round(1.0 - yes_bid["price"], 4) if yes_bid["price"] is not None else None
    yes_levels = _levels(orderbook, "yes")
    no_levels = _levels(orderbook, "no")
    yes_spread = round(yes_ask - yes_bid["price"], 4) if yes_ask is not None and yes_bid["price"] is not None else None
    no_spread = round(no_ask - no_bid["price"], 4) if no_ask is not None and no_bid["price"] is not None else None
    return {
        "yes_bid": yes_bid,
        "yes_ask": yes_ask,
        "yes_spread": yes_spread,
        "yes_depth_levels": len(yes_levels),
        "no_bid": no_bid,
        "no_ask": no_ask,
        "no_spread": no_spread,
        "no_depth_levels": len(no_levels),
    }


if __name__ == "__main__":
    client = KalshiClient()
    print(client.exchange_status())
    markets = discover_btc_hourly_markets(client)
    print(f"BTC hourly markets found: {len(markets)}")
    for market in markets[:5]:
        print(market.get("ticker"), market.get("title") or market.get("subtitle"))
