import json
import math
import os
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

import btc_diviner as rh
from kalshi_client import KalshiClient, orderbook_summary, parse_strike


ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

SERIES_TICKER = os.getenv("KALSHI_BTC_SERIES_TICKER", "KXBTCD")
JOURNAL_PATH = Path(os.getenv("KALSHI_GAMMA_JOURNAL_PATH", ROOT / "kalshi_gamma_sandbox_journal.jsonl"))
POLL_SECONDS = float(os.getenv("KALSHI_GAMMA_POLL_SECONDS", "2.0"))
MAX_ORDER_NOTIONAL = float(os.getenv("KALSHI_GAMMA_MAX_ORDER_NOTIONAL", "10"))
MAX_DRAWDOWN = float(os.getenv("KALSHI_GAMMA_MAX_DRAWDOWN", "25"))
MAX_TRADES_PER_HOUR = int(float(os.getenv("KALSHI_GAMMA_MAX_TRADES_PER_HOUR", "30")))
MAX_SPREAD = float(os.getenv("KALSHI_GAMMA_MAX_SPREAD", "0.04"))
MIN_DEPTH = int(float(os.getenv("KALSHI_GAMMA_MIN_DEPTH", "25")))
TARGET_GAIN = float(os.getenv("KALSHI_GAMMA_TARGET_GAIN", "0.08"))
STOP_LOSS = float(os.getenv("KALSHI_GAMMA_STOP_LOSS", "0.05"))
MIN_HOLD_SECONDS = float(os.getenv("KALSHI_GAMMA_MIN_HOLD_SECONDS", "60"))
EXIT_CONFIRM_TICKS = int(float(os.getenv("KALSHI_GAMMA_EXIT_CONFIRM_TICKS", "3")))
SPOT_WINDOW_SECONDS = float(os.getenv("KALSHI_GAMMA_SPOT_WINDOW_SECONDS", "600"))
MIN_10M_DELTA = float(os.getenv("KALSHI_GAMMA_MIN_10M_DELTA", "0"))
REVERSION_DISTANCE = float(os.getenv("KALSHI_GAMMA_REVERSION_DISTANCE", "80"))
REVERSION_MIN_WINDOW_SECONDS = float(os.getenv("KALSHI_GAMMA_REVERSION_MIN_WINDOW_SECONDS", "120"))
REVERSE_SIGNAL = os.getenv("KALSHI_GAMMA_REVERSE_SIGNAL", "false").strip().lower() in {"1", "true", "yes", "on"}
TELEMETRY_MAXLEN = int(float(os.getenv(
    "KALSHI_GAMMA_TELEMETRY_MAXLEN",
    str(max(600, int(SPOT_WINDOW_SECONDS / max(POLL_SECONDS, 0.1)) + 10)),
)))
MARKET_REFRESH_SECONDS = float(os.getenv("KALSHI_GAMMA_MARKET_REFRESH_SECONDS", "60"))
USE_COLOR = os.getenv("USE_COLOR", "true").strip().lower() not in {"0", "false", "no", "off"}


COLORS = {
    "green": "\033[92m",
    "red": "\033[91m",
    "yellow": "\033[93m",
    "cyan": "\033[96m",
    "gray": "\033[90m",
    "reset": "\033[0m",
}


def color(text, name):
    if not USE_COLOR:
        return str(text)
    return f"{COLORS.get(name, '')}{text}{COLORS['reset']}"


def bias_color(value):
    if value in {"breakout_up", "rising"}:
        return "green"
    if value in {"breakout_down", "falling"}:
        return "red"
    if value in {"warming_up", "liquidity_thinning"}:
        return "yellow"
    return "gray"


def mean(values):
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def fetch_spot():
    try:
        _, spot = rh.fetch_live_robinhood_spot()
        return float(spot)
    except Exception:
        return 0.0


class TelemetryState:
    def __init__(self, maxlen=TELEMETRY_MAXLEN):
        self.spot = deque(maxlen=maxlen)
        self.spot_window = deque(maxlen=maxlen)
        self.yes_mid = deque(maxlen=maxlen)
        self.no_mid = deque(maxlen=maxlen)
        self.liquidity = deque(maxlen=maxlen)

    def update(self, *, timestamp, spot, yes_mid, no_mid, liquidity):
        if spot:
            self.spot.append(float(spot))
            self.spot_window.append((float(timestamp), float(spot)))
            while self.spot_window and (float(timestamp) - self.spot_window[0][0]) > SPOT_WINDOW_SECONDS:
                self.spot_window.popleft()
        if yes_mid is not None:
            self.yes_mid.append(float(yes_mid))
        if no_mid is not None:
            self.no_mid.append(float(no_mid))
        if liquidity is not None:
            self.liquidity.append(float(liquidity))

    def fourier_pred(self):
        values = list(self.spot)[-60:]
        if len(values) < 16:
            return {"fourier_pred": "warming_up", "fourier_slope": 0.0}
        centered = [value - mean(values) for value in values]
        n = len(centered)
        best = {"period": 0, "amplitude": 0.0, "re": 0.0, "im": 0.0}
        for period in (6, 8, 10, 12, 15, 20, 30, 45):
            if period >= n:
                continue
            re = 0.0
            im = 0.0
            for idx, value in enumerate(centered):
                angle = 2.0 * math.pi * idx / period
                re += value * math.cos(angle)
                im += value * math.sin(angle)
            amplitude = (2.0 / n) * math.sqrt((re * re) + (im * im))
            if amplitude > best["amplitude"]:
                best = {"period": period, "amplitude": amplitude, "re": re, "im": im}
        if not best["period"]:
            return {"fourier_pred": "flat", "fourier_slope": 0.0}
        phase = math.atan2(best["im"], best["re"])
        now_angle = 2.0 * math.pi * (n - 1) / best["period"]
        prev_angle = 2.0 * math.pi * (n - 2) / best["period"]
        slope = best["amplitude"] * math.cos(now_angle - phase) - best["amplitude"] * math.cos(prev_angle - phase)
        trend_delta = values[-1] - values[-6] if len(values) >= 6 else values[-1] - values[0]
        if trend_delta > 2.0:
            pred = "rising"
        elif trend_delta < -2.0:
            pred = "falling"
        else:
            pred = "rising" if slope > 0.25 else "falling" if slope < -0.25 else "flat"
        return {"fourier_pred": pred, "fourier_slope": round(float(slope), 4)}

    def laplace_drift(self):
        # Practical impulse/decay filter: fast response minus slow response for spot and liquidity.
        spots = list(self.spot)
        liquidity = list(self.liquidity)
        if len(spots) < 8:
            return {"laplace_drift": "warming_up", "laplace_score": 0.0, "liquidity_decay": 0.0}
        deltas = [spots[idx] - spots[idx - 1] for idx in range(1, len(spots))]
        fast = mean(deltas[-4:])
        slow = mean(deltas[-18:] if len(deltas) >= 18 else deltas)
        score = fast - slow
        liquidity_decay = 0.0
        if len(liquidity) >= 8:
            liquidity_decay = mean(liquidity[-4:]) - mean(liquidity[-18:] if len(liquidity) >= 18 else liquidity)
        if score > 0.2:
            drift = "breakout_up"
        elif score < -0.2:
            drift = "breakout_down"
        elif liquidity_decay < -50:
            drift = "liquidity_thinning"
        else:
            drift = "mean_reverting"
        return {
            "laplace_drift": drift,
            "laplace_score": round(float(score), 4),
            "liquidity_decay": round(float(liquidity_decay), 4),
        }

    def ten_min_impulse(self):
        samples = list(self.spot_window)
        if len(samples) < 2:
            return {
                "spot_10m_delta": 0.0,
                "spot_10m_direction": "warming_up",
                "spot_10m_impulse_ok": False,
                "spot_10m_window_seconds": 0,
            }
        window_seconds = samples[-1][0] - samples[0][0]
        delta = samples[-1][1] - samples[0][1]
        if window_seconds < SPOT_WINDOW_SECONDS:
            direction = "warming_up"
            impulse_ok = False
        elif delta > MIN_10M_DELTA:
            direction = "up"
            impulse_ok = True
        elif delta < -MIN_10M_DELTA:
            direction = "down"
            impulse_ok = True
        else:
            direction = "flat"
            impulse_ok = False
        return {
            "spot_10m_delta": round(float(delta), 4),
            "spot_10m_direction": direction,
            "spot_10m_impulse_ok": impulse_ok,
            "spot_10m_window_seconds": int(window_seconds),
        }


def market_score(market, spot):
    strike = parse_strike(market.get("ticker"))
    if strike is None or spot <= 0:
        return float("inf")
    close_time = str(market.get("close_time") or market.get("expiration_time") or "")
    return abs(strike - spot) + (0 if close_time else 100000)


def select_market(client, spot):
    data = client.markets(status="open", limit=1000, series_ticker=SERIES_TICKER)
    markets = data.get("markets", [])
    candidates = [market for market in markets if parse_strike(market.get("ticker")) is not None]
    if not candidates:
        return None, None
    fallback = sorted(candidates, key=lambda market: market_score(market, spot))[0]
    quoted_fallback = None
    for market in sorted(candidates, key=lambda market: market_score(market, spot))[:80]:
        summary = orderbook_summary(client.orderbook(market["ticker"], depth=100))
        if summary["yes_bid"]["price"] is not None and summary["no_bid"]["price"] is not None:
            if quoted_fallback is None:
                quoted_fallback = (market, summary)
            spread_ok = (
                summary["yes_spread"] is not None
                and summary["yes_spread"] <= MAX_SPREAD
                and summary["no_spread"] is not None
                and summary["no_spread"] <= MAX_SPREAD
            )
            depth_ok = summary["yes_bid"]["quantity"] >= MIN_DEPTH and summary["no_bid"]["quantity"] >= MIN_DEPTH
            if spread_ok and depth_ok:
                return market, summary
    if quoted_fallback is not None:
        return quoted_fallback
    return fallback, orderbook_summary(client.orderbook(fallback["ticker"], depth=100))


def midpoint(bid, ask):
    if bid is None or ask is None:
        return None
    return round((bid + ask) / 2.0, 4)


def side_price(summary, side):
    return summary["yes_ask"] if side == "YES" else summary["no_ask"]


def close_price(summary, side):
    return summary["yes_bid"]["price"] if side == "YES" else summary["no_bid"]["price"]


def spread_ok(summary):
    return (
        summary["yes_spread"] is not None
        and summary["yes_spread"] <= MAX_SPREAD
        and summary["no_spread"] is not None
        and summary["no_spread"] <= MAX_SPREAD
    )


def depth_ok(summary):
    return summary["yes_bid"]["quantity"] >= MIN_DEPTH and summary["no_bid"]["quantity"] >= MIN_DEPTH


def side_book_ok(summary, side):
    return side_price(summary, side) is not None and close_price(summary, side) is not None


def impulse_matches_side(impulse, side):
    if not impulse["spot_10m_impulse_ok"]:
        return False
    if REVERSE_SIGNAL:
        if side == "YES":
            return impulse["spot_10m_direction"] == "down"
        return impulse["spot_10m_direction"] == "up"
    if side == "YES":
        return impulse["spot_10m_direction"] == "up"
    return impulse["spot_10m_direction"] == "down"


def opposing_laplace_confirmed(laplace, side):
    if side == "YES":
        expected = "breakout_down" if REVERSE_SIGNAL else "breakout_up"
    else:
        expected = "breakout_up" if REVERSE_SIGNAL else "breakout_down"
    if expected == "breakout_up":
        return laplace["laplace_drift"] == "breakout_down"
    return laplace["laplace_drift"] == "breakout_up"


def strike_reversion_context(spot, strike, impulse, laplace, fourier):
    if not spot or strike is None:
        return {
            "strike_distance": None,
            "strike_reversion_side": "none",
            "strike_reversion_confidence": 0.0,
            "strike_reversion_ready": False,
            "falling_knife_risk": False,
            "setup_mode": "unknown",
        }

    distance = float(spot) - float(strike)
    abs_distance = abs(distance)
    window_ready = impulse["spot_10m_window_seconds"] >= REVERSION_MIN_WINDOW_SECONDS
    extended = abs_distance >= REVERSION_DISTANCE
    ten_min_delta = impulse["spot_10m_delta"]

    above_strike = distance > 0
    below_strike = distance < 0
    still_accelerating_up = (
        above_strike
        and laplace["laplace_drift"] == "breakout_up"
        and fourier["fourier_pred"] == "rising"
    )
    still_accelerating_down = (
        below_strike
        and laplace["laplace_drift"] == "breakout_down"
        and fourier["fourier_pred"] == "falling"
    )
    reversion_signal = (
        (above_strike and (laplace["laplace_drift"] != "breakout_up" or fourier["fourier_pred"] in {"falling", "flat"}))
        or (below_strike and (laplace["laplace_drift"] != "breakout_down" or fourier["fourier_pred"] in {"rising", "flat"}))
    )

    falling_knife_risk = (
        (below_strike and still_accelerating_down and ten_min_delta < -REVERSION_DISTANCE)
        or (above_strike and still_accelerating_up and ten_min_delta > REVERSION_DISTANCE)
    )
    side = "NO" if above_strike else "YES" if below_strike else "none"
    confidence = 0.0
    if window_ready and extended:
        confidence += min(0.55, abs_distance / max(REVERSION_DISTANCE * 3.0, 1.0))
        if reversion_signal:
            confidence += 0.35
        if fourier["fourier_pred"] == ("falling" if above_strike else "rising"):
            confidence += 0.1
    confidence = round(min(1.0, confidence), 4)
    ready = window_ready and extended and reversion_signal and not falling_knife_risk
    if ready:
        setup_mode = "strike_reversion"
    elif falling_knife_risk:
        setup_mode = "falling_knife_wait"
    else:
        setup_mode = "breakout_or_observe"

    return {
        "strike_distance": round(distance, 4),
        "strike_reversion_side": side,
        "strike_reversion_confidence": confidence,
        "strike_reversion_ready": ready,
        "falling_knife_risk": falling_knife_risk,
        "setup_mode": setup_mode,
    }


def signal_side(laplace, fourier):
    if laplace["laplace_drift"] == "breakout_up" and fourier["fourier_pred"] in {"rising", "flat"}:
        return "NO" if REVERSE_SIGNAL else "YES"
    if laplace["laplace_drift"] == "breakout_down" and fourier["fourier_pred"] in {"falling", "flat"}:
        return "YES" if REVERSE_SIGNAL else "NO"
    return None


def write_event(event):
    JOURNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with JOURNAL_PATH.open("a", encoding="utf-8") as journal:
        journal.write(json.dumps(event, sort_keys=True) + "\n")


def run():
    client = KalshiClient()
    telemetry = TelemetryState()
    active = None
    realized_pnl = 0.0
    trade_times = deque(maxlen=MAX_TRADES_PER_HOUR)
    selected_market = None
    selected_at = 0.0

    print("[KALSHI-GAMMA] sandbox/paper engine online", flush=True)
    print(f"[KALSHI-GAMMA] env={client.env} rest={client.base_url}", flush=True)
    print(f"[KALSHI-GAMMA] ws={client.websocket_url}", flush=True)
    print(f"[KALSHI-GAMMA] journal={JOURNAL_PATH}", flush=True)
    print("[KALSHI-GAMMA] no live orders submitted", flush=True)

    while True:
        now = datetime.now(timezone.utc)
        try:
            if realized_pnl <= -abs(MAX_DRAWDOWN):
                print(f"[KALSHI-GAMMA] circuit breaker: drawdown {realized_pnl:.2f}", flush=True)
                time.sleep(POLL_SECONDS)
                continue

            spot = fetch_spot()
            refresh_market = selected_market is None or (time.time() - selected_at) >= MARKET_REFRESH_SECONDS
            if refresh_market:
                market, summary = select_market(client, spot)
                selected_market = market
                selected_at = time.time()
            else:
                market = selected_market
                summary = orderbook_summary(client.orderbook(market["ticker"], depth=100))
            if not market:
                print("[KALSHI-GAMMA] no market selected", flush=True)
                time.sleep(POLL_SECONDS)
                continue

            ticker = market["ticker"]
            yes_mid = midpoint(summary["yes_bid"]["price"], summary["yes_ask"])
            no_mid = midpoint(summary["no_bid"]["price"], summary["no_ask"])
            liquidity = (
                summary["yes_bid"]["quantity"]
                + summary["no_bid"]["quantity"]
            )
            telemetry.update(timestamp=time.time(), spot=spot, yes_mid=yes_mid, no_mid=no_mid, liquidity=liquidity)
            fourier = telemetry.fourier_pred()
            laplace = telemetry.laplace_drift()
            impulse = telemetry.ten_min_impulse()
            strike = parse_strike(ticker)
            reversion = strike_reversion_context(spot, strike, impulse, laplace, fourier)

            event = {
                "timestamp": now.isoformat(),
                "mode": "kalshi_sandbox_paper",
                "ticker": ticker,
                "event_ticker": market.get("event_ticker"),
                "title": market.get("title") or market.get("subtitle"),
                "spot": spot,
                "strike": strike,
                "target_vs_spot": round((strike or 0) - spot, 4) if strike and spot else None,
                "yes_bid": summary["yes_bid"],
                "yes_ask": summary["yes_ask"],
                "yes_spread": summary["yes_spread"],
                "no_bid": summary["no_bid"],
                "no_ask": summary["no_ask"],
                "no_spread": summary["no_spread"],
                "liquidity": liquidity,
                **fourier,
                **laplace,
                **impulse,
                **reversion,
            }

            if active:
                active_ticker = active["entry_ticker"]
                active_summary = summary if active_ticker == ticker else orderbook_summary(client.orderbook(active_ticker, depth=100))
                exit_px = close_price(active_summary, active["side"])
                pnl = (exit_px - active["entry_price"]) * active["quantity"] if exit_px is not None else 0.0
                held_seconds = time.time() - active["entry_epoch"]
                active_market_sane = spread_ok(active_summary) and side_book_ok(active_summary, active["side"])
                reversion_still_valid = (
                    active.get("entry_setup_mode") == "strike_reversion"
                    and reversion["strike_reversion_ready"]
                    and reversion["strike_reversion_side"] == active["side"]
                )
                impulse_still_valid = impulse_matches_side(impulse, active["side"]) or reversion_still_valid
                opposing_signal = opposing_laplace_confirmed(laplace, active["side"])
                if opposing_signal:
                    active["exit_confirm_ticks"] = active.get("exit_confirm_ticks", 0) + 1
                else:
                    active["exit_confirm_ticks"] = 0
                exit_reason = None
                if not side_book_ok(active_summary, active["side"]):
                    exit_reason = "broken_book"
                    exit_px = exit_px if exit_px is not None else 0.0
                    pnl = (exit_px - active["entry_price"]) * active["quantity"]
                elif pnl >= active["target_pnl"]:
                    exit_reason = "target_pnl"
                elif pnl <= -active["stop_pnl"]:
                    exit_reason = "stop_pnl"
                elif held_seconds >= MIN_HOLD_SECONDS and active_market_sane and not impulse_still_valid:
                    if active["exit_confirm_ticks"] >= EXIT_CONFIRM_TICKS:
                        exit_reason = "impulse_failed"
                should_exit = exit_reason is not None
                event.update({
                    "action": "HOLD",
                    "active_position": active,
                    "active_ticker": active_ticker,
                    "active_yes_bid": active_summary["yes_bid"],
                    "active_yes_ask": active_summary["yes_ask"],
                    "active_yes_spread": active_summary["yes_spread"],
                    "active_no_bid": active_summary["no_bid"],
                    "active_no_ask": active_summary["no_ask"],
                    "active_no_spread": active_summary["no_spread"],
                    "active_held_seconds": round(held_seconds, 2),
                    "active_market_sane": active_market_sane,
                    "active_impulse_still_valid": impulse_still_valid,
                    "exit_confirm_ticks": active["exit_confirm_ticks"],
                    "unrealized_pnl": round(pnl, 4),
                })
                if should_exit:
                    realized_pnl += pnl
                    event.update({
                        "action": "SELL",
                        "side": active["side"],
                        "exit_reason": exit_reason,
                        "exit_price": exit_px,
                        "quantity": active["quantity"],
                        "realized_pnl": round(pnl, 4),
                        "total_realized_pnl": round(realized_pnl, 4),
                    })
                    pnl_color = "green" if pnl >= 0 else "red"
                    print(
                        color(
                            f"[KALSHI-GAMMA] SELL {active['side']} {active_ticker} @ {exit_px} "
                            f"pnl={pnl:.2f} reason={exit_reason}",
                            pnl_color,
                        ),
                        flush=True,
                    )
                    active = None
            else:
                recent_trades = [ts for ts in trade_times if (now - ts).total_seconds() < 3600]
                trade_times = deque(recent_trades, maxlen=MAX_TRADES_PER_HOUR)
                can_trade = len(trade_times) < MAX_TRADES_PER_HOUR
                spread_is_ok = spread_ok(summary)
                depth_is_ok = depth_ok(summary)
                side = None
                if can_trade and spread_is_ok and depth_is_ok:
                    candidate_side = reversion["strike_reversion_side"] if reversion["strike_reversion_ready"] else signal_side(laplace, fourier)
                    if (
                        candidate_side
                        and side_book_ok(summary, candidate_side)
                        and (
                            reversion["strike_reversion_ready"]
                            or (
                                impulse_matches_side(impulse, candidate_side)
                                and not reversion["falling_knife_risk"]
                            )
                        )
                    ):
                        side = candidate_side

                if side:
                    entry_price = side_price(summary, side)
                    quantity = int(MAX_ORDER_NOTIONAL // entry_price) if entry_price else 0
                    if quantity > 0:
                        trigger_ts = time.time()
                        time.sleep(float(os.getenv("KALSHI_GAMMA_EXECUTION_DELAY_SECONDS", "1.0")))
                        execution_delay_ms = int((time.time() - trigger_ts) * 1000)
                        active = {
                            "side": side,
                            "entry_price": entry_price,
                            "quantity": quantity,
                            "target_pnl": round(quantity * TARGET_GAIN, 4),
                            "stop_pnl": round(quantity * STOP_LOSS, 4),
                            "entry_timestamp": now.isoformat(),
                            "entry_epoch": time.time(),
                            "entry_ticker": ticker,
                            "entry_spot_10m_delta": impulse["spot_10m_delta"],
                            "entry_spot_10m_direction": impulse["spot_10m_direction"],
                            "entry_setup_mode": reversion["setup_mode"],
                            "entry_strike_distance": reversion["strike_distance"],
                            "entry_reversion_confidence": reversion["strike_reversion_confidence"],
                            "exit_confirm_ticks": 0,
                        }
                        trade_times.append(now)
                        event.update({
                            "action": "BUY",
                            "side": side,
                            "entry_price": entry_price,
                            "quantity": quantity,
                            "execution_delay_ms": execution_delay_ms,
                        })
                        buy_color = "green" if side == "YES" else "red"
                        print(
                            color(
                                f"[KALSHI-GAMMA] BUY {side} {ticker} @ {entry_price} "
                                f"qty={quantity} setup={reversion['setup_mode']} "
                                f"drift={laplace['laplace_drift']} fourier={fourier['fourier_pred']}",
                                buy_color,
                            ),
                            flush=True,
                        )
                else:
                    event.update({
                        "action": "OBSERVE",
                        "can_trade": can_trade,
                        "spread_ok": spread_is_ok,
                        "depth_ok": depth_is_ok,
                        "trades_this_hour": len(trade_times),
                    })
                    drift = color(laplace["laplace_drift"], bias_color(laplace["laplace_drift"]))
                    fourier_pred = color(fourier["fourier_pred"], bias_color(fourier["fourier_pred"]))
                    spread = summary["yes_spread"] if summary["yes_spread"] is not None else "NA"
                    print(
                        color("[KALSHI-GAMMA] OBSERVE", "cyan")
                        + f" {ticker} spot={spot:.2f} strike={strike} "
                        + f"drift={drift} fourier={fourier_pred} spread={spread} depth={liquidity}",
                        flush=True,
                    )

            write_event(event)
        except Exception as exc:
            print(f"[KALSHI-GAMMA ERROR] {exc}", flush=True)
            write_event({"timestamp": now.isoformat(), "mode": "kalshi_sandbox_paper", "error": str(exc)})
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    run()
