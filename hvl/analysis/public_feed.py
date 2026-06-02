"""Build a sanitized public showcase feed from local runtime artifacts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

from hvl.analysis.analyze_trade_journal import load_events, pair_trades
from hvl.utils.paths import PRIVATE_DATA_DIR, PRIVATE_JOURNAL_DIR, PRIVATE_RUNTIME_DIR, REPO_ROOT, WEB_DATA_DIR


PUBLIC_FEED_PATH = WEB_DATA_DIR / "public_feed.json"


def _read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback


def _as_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _as_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _first_present(*values):
    for value in values:
        if value is not None:
            return value
    return None


def _round_float(value, digits=2):
    number = _as_float(value)
    return round(number, digits) if number is not None else None


def _read_jsonl(path: Path):
    if not path.exists():
        return []
    rows = []
    try:
        with path.open("r", encoding="utf-8") as journal:
            for line in journal:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    return rows


def _paper_summary(path: Path):
    events, warnings = load_events(path)
    trades, open_buy, unmatched_sells, replaced_buys = pair_trades(events)
    pnls = [trade["pnl"] for trade in trades if trade["pnl"] is not None]
    wins = [pnl for pnl in pnls if pnl > 0]
    return {
        "journal_present": path.exists(),
        "events": len(events),
        "completed_trades": len(trades),
        "open_position": bool(open_buy),
        "unmatched_sells": len(unmatched_sells),
        "replaced_buys": len(replaced_buys),
        "warnings": len(warnings),
        "total_pnl": round(sum(pnls), 2) if pnls else 0.0,
        "avg_pnl": round(mean(pnls), 2) if pnls else 0.0,
        "win_rate": round(len(wins) / len(pnls) * 100, 1) if pnls else None,
    }


def _kalshi_summary():
    rows = []
    total_events = 0
    paths = {
        *PRIVATE_JOURNAL_DIR.glob("kalshi_*.jsonl"),
        *REPO_ROOT.glob("kalshi_*.jsonl"),
    }
    for path in sorted(paths):
        journal_rows = _read_jsonl(path)
        events = len(journal_rows)
        paper_pnl = []
        last_mode = None
        last_error = None
        for event in journal_rows:
            last_mode = event.get("mode") or last_mode
            last_error = event.get("error") or last_error
            pnl = _as_float(event.get("paper_pnl") or event.get("realized_pnl"))
            if pnl is not None:
                paper_pnl.append(pnl)
        total_events += events
        rows.append(
            {
                "name": path.stem,
                "events": events,
                "mode": last_mode or "paper",
                "last_error": last_error,
                "paper_pnl": round(paper_pnl[-1], 2) if paper_pnl else None,
            }
        )
    return {"journals": rows, "events": total_events}


def _kalshi_btc_journal_path():
    candidates = [
        PRIVATE_JOURNAL_DIR / "kalshi_gamma_regime_journal.jsonl",
        REPO_ROOT / "kalshi_gamma_regime_journal.jsonl",
    ]
    existing = [path for path in candidates if path.exists()]
    if not existing:
        return candidates[0]
    return max(existing, key=lambda path: path.stat().st_mtime)


def _book_side(event, side):
    bid = event.get(f"{side}_bid") or {}
    return {
        "bid_price": _round_float(bid.get("price"), 4),
        "bid_quantity": _as_int(bid.get("quantity")),
        "ask_price": _round_float(event.get(f"{side}_ask"), 4),
        "spread": _round_float(event.get(f"{side}_spread"), 4),
    }


def _paper_position(active):
    if not isinstance(active, dict):
        return {"open": False}
    return {
        "open": True,
        "side": active.get("side"),
        "ticker": active.get("entry_ticker"),
        "entry_timestamp": active.get("entry_timestamp"),
        "entry_price": _round_float(active.get("entry_price"), 4),
        "quantity": _as_int(active.get("quantity")),
        "setup_mode": active.get("entry_setup_mode"),
        "spot_10m_delta": _round_float(active.get("entry_spot_10m_delta"), 2),
        "systemic_state": active.get("entry_systemic_state"),
        "systemic_delta_6h": _round_float(active.get("entry_systemic_delta_6h"), 2),
    }


def _trade_marker(event, action):
    if not event:
        return None
    marker = {
        "timestamp": event.get("timestamp"),
        "action": action,
        "ticker": event.get("ticker") or event.get("active_ticker"),
        "side": event.get("side"),
        "price": _round_float(event.get("entry_price") if action == "BUY" else event.get("exit_price"), 4),
        "quantity": _as_int(event.get("quantity")),
        "setup_mode": event.get("entry_setup_mode") or event.get("setup_mode"),
    }
    if action == "SELL":
        marker["exit_reason"] = event.get("exit_reason")
        marker["realized_pnl"] = _round_float(event.get("realized_pnl"), 4)
    return marker


def _kalshi_gamma_proxy(event):
    explicit = _first_present(
        event.get("gamma"),
        event.get("gamma_signal"),
        event.get("gamma_proxy"),
    )
    if explicit is not None:
        return {
            "label": "gamma",
            "value": _round_float(explicit, 4),
        }
    return {
        "label": "strike_distance_proxy",
        "value": _round_float(event.get("strike_distance"), 2),
        "impulse": _round_float(event.get("spot_10m_delta"), 2),
        "laplace_score": _round_float(event.get("laplace_score"), 4),
    }


def _kalshi_btc_chart_points(events, limit=96):
    points = []
    cumulative_realized = 0.0
    for event in events[-limit:]:
        spot = _round_float(event.get("spot"), 2)
        if spot is None:
            continue
        realized_pnl = _round_float(event.get("realized_pnl"), 4)
        total_realized = _round_float(event.get("total_realized_pnl"), 4)
        if total_realized is None and realized_pnl is not None:
            cumulative_realized = round(cumulative_realized + realized_pnl, 4)
            total_realized = cumulative_realized
        elif total_realized is not None:
            cumulative_realized = total_realized
        points.append(
            {
                "timestamp": event.get("timestamp"),
                "time": event.get("timestamp"),
                "spot": spot,
                "action": event.get("action"),
                "side": event.get("side") or event.get("side_intent"),
                "regime": event.get("macro_regime"),
                "systemic_state": event.get("systemic_state"),
                "realized_pnl": realized_pnl,
                "cumulative_realized_pnl": total_realized,
                "hypothetical_x100_pnl": _round_float(total_realized * 100 if total_realized is not None else None, 2),
                "gamma_proxy": _kalshi_gamma_proxy(event),
            }
        )
    return points


def _kalshi_btc_trade_markers(events, limit=24):
    markers = []
    for event in events:
        action = event.get("action")
        if action not in {"BUY", "SELL"}:
            continue
        marker = _trade_marker(event, action)
        if marker:
            marker["spot"] = _round_float(event.get("spot"), 2)
            marker["regime"] = event.get("macro_regime")
            markers.append(marker)
    return markers[-limit:]


def _kalshi_btc_summary():
    path = _kalshi_btc_journal_path()
    events = _read_jsonl(path)
    source = {
        "engine_name": "kalshi_gamma_regime_engine",
        "journal_name": path.name,
    }
    if not events:
        return {
            **source,
            "journal_present": path.exists(),
            "events": 0,
            "mode": "kalshi_regime_paper",
            "engine_mode": None,
            "last_update": None,
            "source": source,
            "chart_points": [],
        }

    last = events[-1]
    source = {
        **source,
        "mode": last.get("mode"),
        "engine_mode": last.get("engine_mode"),
        "last_update": last.get("timestamp"),
    }
    buys = [event for event in events if event.get("action") == "BUY"]
    sells = [event for event in events if event.get("action") == "SELL"]
    accounting_event = next(
        (
            event
            for event in reversed(events)
            if event.get("action") in {"BUY", "HOLD", "SELL"}
            and event.get("total_realized_pnl") is not None
        ),
        last,
    )
    active_position = _paper_position(last.get("active_position"))
    if active_position["open"]:
        active_position["unrealized_pnl"] = _round_float(last.get("unrealized_pnl"), 4)
        active_position["held_seconds"] = _round_float(last.get("active_held_seconds"), 2)

    return {
        **source,
        "source": source,
        "journal_present": path.exists(),
        "events": len(events),
        "mode": last.get("mode") or "kalshi_regime_paper",
        "engine_mode": last.get("engine_mode"),
        "last_update": last.get("timestamp"),
        "performance": {
            "total_realized_pnl": _round_float(accounting_event.get("total_realized_pnl"), 4),
            "unrealized_pnl": _round_float(last.get("unrealized_pnl"), 4),
            "hypothetical_x100_realized_pnl": _round_float(
                _as_float(accounting_event.get("total_realized_pnl")) * 100
                if _as_float(accounting_event.get("total_realized_pnl")) is not None
                else None,
                2,
            ),
            "scale_note": (
                "Shows what the same paper signal path would represent at 100x notional size "
                "before fees, slippage, fills, limits, and risk controls."
            ),
        },
        "spot": {
            "price": _round_float(last.get("spot"), 2),
            "source": last.get("spot_source"),
            "age_seconds": _round_float(last.get("spot_age_seconds"), 2),
            "stale": bool(last.get("spot_stale")),
        },
        "market": {
            "ticker": last.get("ticker"),
            "strike": _round_float(last.get("strike"), 2),
            "seconds_to_close": _round_float(last.get("seconds_to_close"), 2),
            "title": last.get("title"),
        },
        "regime": {
            "state": last.get("macro_regime"),
            "allowed_side": last.get("macro_regime_allowed_side"),
            "gate_open": bool(last.get("macro_regime_gate_open")),
            "confirm_count": _as_int(last.get("macro_regime_confirm_count")),
            "delta_1h": _round_float(last.get("macro_regime_1h_delta"), 2),
            "delta_4h": _round_float(last.get("macro_regime_4h_delta"), 2),
            "delta_6h": _round_float(last.get("macro_regime_6h_delta"), 2),
            "window_1h_seconds": _as_int(last.get("macro_regime_1h_window_seconds")),
            "window_4h_seconds": _as_int(last.get("macro_regime_4h_window_seconds")),
            "window_6h_seconds": _as_int(last.get("macro_regime_6h_window_seconds")),
        },
        "systemic": {
            "state": last.get("systemic_state"),
            "side": last.get("systemic_side"),
            "gate_open": last.get("systemic_gate_open"),
            "entry_ready": last.get("systemic_entry_ready"),
            "block_reason": last.get("systemic_block_reason"),
            "delta_1h": _round_float(last.get("systemic_delta_1h"), 2),
            "delta_4h": _round_float(last.get("systemic_delta_4h"), 2),
            "delta_6h": _round_float(last.get("systemic_delta_6h"), 2),
            "max_countermove_10m": _round_float(last.get("systemic_max_countermove_10m"), 2),
            "max_trades_per_hour": _as_int(last.get("systemic_max_trades_per_hour")),
            "loss_cooldown_seconds": _round_float(last.get("systemic_loss_cooldown_seconds"), 2),
        },
        "session": {
            "state": last.get("session_state"),
            "utc_hour": _round_float(last.get("session_utc_hour"), 4),
            "regular": last.get("session_regular"),
            "after_hours": last.get("session_after_hours"),
            "breakout_window": last.get("session_breakout_window"),
            "breakout_ready": last.get("session_breakout_ready"),
            "breakout_side": last.get("session_breakout_side"),
            "trade_allowed": last.get("session_trade_allowed"),
            "block_reason": last.get("session_block_reason"),
            "after_hours_max_trades_per_hour": _as_int(last.get("session_after_hours_max_trades_per_hour")),
            "after_hours_max_drawdown": _round_float(last.get("session_after_hours_max_drawdown"), 2),
        },
        "impulse": {
            "spot_5m_delta": _round_float(last.get("spot_5m_delta"), 2),
            "spot_5m_window_seconds": _as_int(last.get("spot_5m_window_seconds")),
            "spot_10m_delta": _round_float(last.get("spot_10m_delta"), 2),
            "spot_10m_direction": last.get("spot_10m_direction"),
            "spot_10m_impulse_ok": last.get("spot_10m_impulse_ok"),
            "spot_10m_window_seconds": _as_int(last.get("spot_10m_window_seconds")),
            "spot_20m_delta": _round_float(last.get("spot_20m_delta"), 2),
            "spot_20m_window_seconds": _as_int(last.get("spot_20m_window_seconds")),
        },
        "alpha_stack": {
            "laplace_drift": last.get("laplace_drift"),
            "laplace_score": _round_float(last.get("laplace_score"), 4),
            "fourier_pred": last.get("fourier_pred"),
            "fourier_slope": _round_float(last.get("fourier_slope"), 4),
            "strike_distance": _round_float(last.get("strike_distance"), 2),
            "strike_reversion_side": last.get("strike_reversion_side"),
            "strike_reversion_confidence": _round_float(last.get("strike_reversion_confidence"), 4),
            "strike_reversion_ready": last.get("strike_reversion_ready"),
            "reversal_ready": last.get("reversal_ready"),
            "fast_reversal_side": last.get("fast_reversal_side"),
            "reversal_confirm_ticks": _as_int(last.get("reversal_confirm_ticks")),
        },
        "decision": {
            "action": last.get("action"),
            "side_intent": last.get("side_intent") or last.get("side") or last.get("macro_regime_allowed_side"),
            "setup_mode": last.get("entry_setup_mode") or last.get("setup_mode"),
            "engine_mode": last.get("engine_mode"),
            "can_trade": last.get("can_trade"),
            "spread_ok": last.get("spread_ok"),
            "depth_ok": last.get("depth_ok"),
            "macro_entry_ready": last.get("macro_entry_ready"),
            "session_entry_ready": last.get("session_entry_ready"),
            "entry_ready": last.get("entry_ready"),
            "systemic_entry_ready": last.get("systemic_entry_ready"),
            "systemic_trade_count_ok": last.get("systemic_trade_count_ok"),
            "systemic_loss_cooldown_active": last.get("systemic_loss_cooldown_active"),
            "session_trade_count_ok": last.get("session_trade_count_ok"),
            "risk_entry_blocked": last.get("risk_entry_blocked"),
            "base_risk_entry_blocked": last.get("base_risk_entry_blocked"),
            "session_risk_entry_blocked": last.get("session_risk_entry_blocked"),
            "falling_knife_risk": last.get("falling_knife_risk"),
            "trades_this_hour": _as_int(last.get("trades_this_hour")),
        },
        "book": {
            "yes": _book_side(last, "yes"),
            "no": _book_side(last, "no"),
            "liquidity": _as_int(last.get("liquidity")),
            "liquidity_decay": _round_float(last.get("liquidity_decay"), 4),
        },
        "api_health": {
            "kalshi_api_status": last.get("kalshi_api_status"),
            "kalshi_api_state": last.get("kalshi_api_state"),
            "kalshi_request_status_code": _as_int(last.get("kalshi_request_status_code")),
            "kalshi_request_elapsed_ms": _as_int(last.get("kalshi_request_elapsed_ms")),
            "kalshi_request_retry_count": _as_int(last.get("kalshi_request_retry_count")),
            "kalshi_market_cache_age_seconds": _round_float(last.get("kalshi_market_cache_age_seconds"), 2),
            "kalshi_orderbook_scan_count": _as_int(last.get("kalshi_orderbook_scan_count")),
            "kalshi_api_error": last.get("kalshi_api_error") or last.get("kalshi_error"),
        },
        "position": active_position,
        "last_paper_entry": _trade_marker(buys[-1], "BUY") if buys else None,
        "last_paper_exit": _trade_marker(sells[-1], "SELL") if sells else None,
        "chart_points": _kalshi_btc_chart_points(events),
        "trade_markers": _kalshi_btc_trade_markers(events),
    }


def _kalshi_bankroll_journal_path():
    candidates = [
        PRIVATE_JOURNAL_DIR / "kalshi_bankroll_journal.jsonl",
        REPO_ROOT / "kalshi_bankroll_journal.jsonl",
    ]
    existing = [path for path in candidates if path.exists()]
    if not existing:
        return candidates[0]
    return max(existing, key=lambda path: path.stat().st_mtime)


def _kalshi_bankroll_ledger_path():
    candidates = [
        PRIVATE_JOURNAL_DIR / "kalshi_bankroll_trade_ledger.jsonl",
        REPO_ROOT / "kalshi_bankroll_trade_ledger.jsonl",
    ]
    existing = [path for path in candidates if path.exists()]
    if not existing:
        return candidates[0]
    return max(existing, key=lambda path: path.stat().st_mtime)


def _kalshi_bankroll_model_config_path():
    candidates = [
        PRIVATE_DATA_DIR / "kalshi_training" / "bankroll_model_config.json",
        REPO_ROOT / "bankroll_model_config.json",
    ]
    existing = [path for path in candidates if path.exists()]
    if not existing:
        return candidates[0]
    return max(existing, key=lambda path: path.stat().st_mtime)


def _bankroll_trade_ledger(rows, limit=50):
    ledger = []
    for row in rows[-limit:]:
        ledger.append(
            {
                "trade_id": _as_int(row.get("trade_id")),
                "side": row.get("side"),
                "ticker": row.get("ticker"),
                "quantity": _as_int(row.get("quantity")),
                "entry_timestamp": row.get("entry_timestamp"),
                "entry_price": _round_float(row.get("entry_price"), 4),
                "entry_notional": _round_float(row.get("entry_notional"), 2),
                "entry_spot": _round_float(row.get("entry_spot"), 2),
                "entry_strike": _round_float(row.get("entry_strike"), 2),
                "entry_forecast_state": row.get("entry_forecast_state"),
                "entry_forecast_confidence": _round_float(row.get("entry_forecast_confidence"), 4),
                "entry_min_hold_seconds": _round_float(row.get("entry_min_hold_seconds"), 0),
                "entry_exit_confirm_ticks": _as_int(row.get("entry_exit_confirm_ticks")),
                "entry_side_min_confidence": _round_float(row.get("entry_side_min_confidence"), 4),
                "exit_timestamp": row.get("exit_timestamp"),
                "exit_price": _round_float(row.get("exit_price"), 4),
                "exit_spot": _round_float(row.get("exit_spot"), 2),
                "exit_reason": row.get("exit_reason"),
                "held_seconds": _round_float(row.get("held_seconds"), 1),
                "realized_pnl": _round_float(row.get("realized_pnl"), 4),
                "return_pct": _round_float(row.get("return_pct"), 4),
                "max_unrealized_pnl": _round_float(row.get("max_unrealized_pnl"), 4),
                "min_unrealized_pnl": _round_float(row.get("min_unrealized_pnl"), 4),
                "win": _as_bool(row.get("win")),
                "bankroll_after": _round_float(row.get("bankroll_after_usd"), 2),
            }
        )
    return ledger


def _bankroll_trade_stats(rows):
    if not rows:
        return {
            "trades": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": None,
            "total_realized_pnl": 0.0,
            "avg_pnl": None,
            "best_pnl": None,
            "worst_pnl": None,
            "avg_hold_seconds": None,
        }
    pnls = [float(r.get("realized_pnl") or 0.0) for r in rows]
    holds = [float(r.get("held_seconds") or 0.0) for r in rows]
    wins = sum(1 for r in rows if r.get("win"))
    losses = len(rows) - wins
    total = sum(pnls)
    return {
        "trades": len(rows),
        "wins": wins,
        "losses": losses,
        "win_rate": round(wins / len(rows), 4),
        "total_realized_pnl": round(total, 4),
        "avg_pnl": round(total / len(rows), 4),
        "best_pnl": round(max(pnls), 4),
        "worst_pnl": round(min(pnls), 4),
        "avg_hold_seconds": round(sum(holds) / len(holds), 1) if holds else None,
    }


def _bankroll_position(active):
    if not isinstance(active, dict):
        return {"open": False}
    return {
        "open": True,
        "side": active.get("side"),
        "ticker": active.get("entry_ticker"),
        "entry_timestamp": active.get("entry_timestamp"),
        "entry_price": _round_float(active.get("entry_price"), 4),
        "quantity": _as_int(active.get("quantity")),
        "entry_notional": _round_float(active.get("entry_notional"), 2),
        "forecast_state": active.get("entry_forecast_state"),
        "forecast_confidence": _round_float(active.get("entry_forecast_confidence"), 4),
        "projected_60m": _round_float(active.get("entry_forecast_projected_60m"), 2),
        "required_high_liquidity": _as_bool(active.get("entry_required_high_liquidity")),
        "min_hold_seconds": _round_float(active.get("entry_min_hold_seconds"), 0),
        "exit_confirm_ticks": _as_int(active.get("entry_exit_confirm_ticks")),
        "side_min_confidence": _round_float(active.get("entry_side_min_confidence"), 4),
        "restored_from_journal": _as_bool(active.get("restored_from_journal")),
    }


def _bankroll_chart_points(events, limit=120):
    points = []
    for event in events[-limit:]:
        bankroll = _round_float(event.get("bankroll_current_usd"), 2)
        if bankroll is None:
            continue
        points.append(
            {
                "timestamp": event.get("timestamp"),
                "time": event.get("timestamp"),
                "bankroll": bankroll,
                "drawdown": _round_float(event.get("bankroll_drawdown_usd"), 2),
                "spot": _round_float(event.get("spot"), 2),
                "forecast_state": event.get("forecast_state"),
                "forecast_side": event.get("forecast_side"),
                "forecast_confidence": _round_float(event.get("forecast_confidence"), 4),
                "projected_30m": _round_float(event.get("projected_30m"), 2),
                "action": event.get("action"),
            }
        )
    return points


def _bankroll_trade_markers(events, limit=24):
    markers = []
    for event in events:
        action = event.get("action")
        if action not in {"BUY", "SELL"}:
            continue
        markers.append(
            {
                "timestamp": event.get("timestamp"),
                "action": action,
                "ticker": event.get("ticker") or event.get("active_ticker"),
                "side": event.get("side"),
                "price": _round_float(
                    event.get("entry_price") if action == "BUY" else event.get("exit_price"), 4
                ),
                "quantity": _as_int(event.get("quantity")),
                "notional": _round_float(event.get("entry_notional"), 2),
                "exit_reason": event.get("exit_reason") if action == "SELL" else None,
                "realized_pnl": _round_float(event.get("realized_pnl"), 4) if action == "SELL" else None,
                "bankroll": _round_float(event.get("bankroll_current_usd"), 2),
            }
        )
    return markers[-limit:]


def _kalshi_bankroll_defaults():
    return {
        "bankroll": {
            "start": 100.0,
            "goal": 200.0,
            "current": 100.0,
            "drawdown": 0.0,
            "harvest_active": False,
            "floor_blocked": False,
            "hard_floor": 75.0,
            "min_trade": 10.0,
            "max_trade": 25.0,
            "trade_fraction": 0.20,
            "realized_pnl": 0.0,
        },
        "forecast": {
            "state": None,
            "side": None,
            "pending_state": None,
            "projected_15m": None,
            "projected_30m": None,
            "projected_60m": None,
            "derivative_1": None,
            "derivative_2": None,
            "derivative_3": None,
            "confidence": None,
            "min_confidence": 0.60,
            "confirm_count": None,
            "confirm_ticks_required": None,
            "drop_threshold_usd": -500.0,
            "rally_threshold_usd": 500.0,
            "data_span_seconds": None,
            "sample_count": None,
        },
        "high_liquidity": {
            "required": False,
            "depth_threshold": 150,
            "spread_threshold": 0.02,
            "decay_max": 0.0,
            "yes_depth": None,
            "no_depth": None,
            "yes_spread": None,
            "no_spread": None,
            "ok": False,
        },
        "decision": {
            "action": "OBSERVE",
            "side_intent": None,
            "notional": None,
            "target_notional": None,
            "quantity": None,
            "entry_price": None,
            "block_reason": "no_data_yet",
            "counter_side_eligible": False,
            "no_entry_final_seconds": 900,
            "min_hold_seconds": 0,
            "exit_confirm_ticks": 3,
            "candidate_min_confidence": 0.60,
            "final_window_blocked": False,
        },
        "model_config": {
            "active": False,
            "version": None,
            "confidence": None,
            "reason": None,
            "loaded_at": None,
            "error": None,
            "applied": {},
            "disable_sides": [],
            "side_min_confidence": {"YES": 0.60, "NO": 0.60},
            "side_bias": {},
        },
        "position": {"open": False},
        "spot": {"price": None, "source": None, "stale": None},
        "market": {"ticker": None, "strike": None, "seconds_to_close": None, "title": None},
    }


def _kalshi_bankroll_summary():
    path = _kalshi_bankroll_journal_path()
    events = _read_jsonl(path)
    ledger_path = _kalshi_bankroll_ledger_path()
    ledger_rows = _read_jsonl(ledger_path)
    model_config_path = _kalshi_bankroll_model_config_path()
    model_config_file = _read_json(model_config_path, {})
    source = {
        "engine_name": "kalshi_bankroll_engine",
        "journal_name": path.name,
        "ledger_name": ledger_path.name,
        "model_config_name": model_config_path.name,
    }
    defaults = _kalshi_bankroll_defaults()
    if not events:
        return {
            **source,
            "journal_present": path.exists(),
            "ledger_present": ledger_path.exists(),
            "model_config_present": model_config_path.exists(),
            "events": 0,
            "mode": "kalshi_bankroll_paper",
            "last_update": None,
            **defaults,
            "chart_points": [],
            "trade_markers": [],
            "trade_ledger": _bankroll_trade_ledger(ledger_rows),
            "trade_stats": _bankroll_trade_stats(ledger_rows),
        }

    last = events[-1]
    high_liq = last.get("high_liquidity") or {}
    model_parameters = model_config_file.get("parameters") if isinstance(model_config_file.get("parameters"), dict) else {}
    return {
        **source,
        "journal_present": path.exists(),
        "ledger_present": ledger_path.exists(),
        "model_config_present": model_config_path.exists(),
        "events": len(events),
        "mode": last.get("mode") or "kalshi_bankroll_paper",
        "last_update": last.get("timestamp"),
        "bankroll": {
            "start": _round_float(last.get("bankroll_start_usd"), 2),
            "goal": _round_float(last.get("bankroll_goal_usd"), 2),
            "current": _round_float(last.get("bankroll_current_usd"), 2),
            "drawdown": _round_float(last.get("bankroll_drawdown_usd"), 2),
            "harvest_active": _as_bool(last.get("harvest_active")),
            "floor_blocked": _as_bool(last.get("bankroll_floor_blocked")),
            "hard_floor": _round_float(last.get("bankroll_hard_floor_usd"), 2),
            "min_trade": _round_float(last.get("bankroll_min_trade_usd"), 2),
            "max_trade": _round_float(last.get("bankroll_max_trade_usd"), 2),
            "trade_fraction": _round_float(last.get("bankroll_trade_fraction"), 4),
            "realized_pnl": _round_float(last.get("total_realized_pnl"), 4),
        },
        "forecast": {
            "state": last.get("forecast_state"),
            "side": last.get("forecast_side"),
            "pending_state": last.get("forecast_pending_state"),
            "projected_15m": _round_float(last.get("projected_15m"), 2),
            "projected_30m": _round_float(last.get("projected_30m"), 2),
            "projected_60m": _round_float(last.get("projected_60m"), 2),
            "derivative_1": _round_float(last.get("derivative_1"), 6),
            "derivative_2": _round_float(last.get("derivative_2"), 8),
            "derivative_3": _round_float(last.get("derivative_3"), 10),
            "confidence": _round_float(last.get("forecast_confidence"), 4),
            "min_confidence": _round_float(last.get("forecast_min_confidence"), 4),
            "confirm_count": _as_int(last.get("forecast_confirm_count")),
            "confirm_ticks_required": _as_int(last.get("forecast_confirm_ticks_required")),
            "drop_threshold_usd": _round_float(last.get("forecast_drop_threshold_usd"), 2),
            "rally_threshold_usd": _round_float(last.get("forecast_rally_threshold_usd"), 2),
            "data_span_seconds": _round_float(last.get("forecast_data_span_seconds"), 2),
            "sample_count": _as_int(last.get("forecast_sample_count")),
        },
        "high_liquidity": {
            "required": _as_bool(last.get("high_liquidity_required")),
            "depth_threshold": _as_int(high_liq.get("depth_threshold")),
            "spread_threshold": _round_float(high_liq.get("spread_threshold"), 4),
            "decay_max": _round_float(high_liq.get("decay_max"), 4),
            "yes_depth": _as_int(high_liq.get("yes_depth")),
            "no_depth": _as_int(high_liq.get("no_depth")),
            "yes_spread": _round_float(high_liq.get("yes_spread"), 4),
            "no_spread": _round_float(high_liq.get("no_spread"), 4),
            "depth_ok": _as_bool(high_liq.get("depth_ok")),
            "spread_ok": _as_bool(high_liq.get("spread_ok")),
            "decay_ok": _as_bool(high_liq.get("decay_ok")),
            "ok": _as_bool(high_liq.get("ok")),
        },
        "decision": {
            "action": last.get("action"),
            "side_intent": (
                last.get("side_intent") or last.get("side") or last.get("forecast_side")
            ),
            "notional": _round_float(
                _first_present(last.get("entry_notional"), last.get("candidate_notional")), 2
            ),
            "target_notional": _round_float(last.get("target_notional"), 2),
            "quantity": _as_int(_first_present(last.get("quantity"), last.get("candidate_quantity"))),
            "entry_price": _round_float(
                _first_present(last.get("entry_price"), last.get("candidate_entry_price")), 4
            ),
            "block_reason": last.get("block_reason"),
            "counter_side_eligible": _as_bool(last.get("counter_side_eligible")),
            "no_entry_final_seconds": _round_float(last.get("no_entry_final_seconds"), 0),
            "min_hold_seconds": _round_float(
                _first_present(last.get("min_hold_seconds"), model_parameters.get("min_hold_seconds")), 0
            ),
            "exit_confirm_ticks": _as_int(
                _first_present(last.get("exit_confirm_ticks_required"), model_parameters.get("exit_confirm_ticks"))
            ),
            "candidate_min_confidence": _round_float(
                _first_present(last.get("candidate_min_confidence"), model_parameters.get("min_confidence")), 4
            ),
            "final_window_blocked": _as_bool(last.get("final_window_blocked")),
        },
        "model_config": {
            "present": model_config_path.exists(),
            "active": _as_bool(last.get("model_config_active")),
            "version": last.get("model_config_version") or model_config_file.get("model_config_version"),
            "confidence": model_config_file.get("confidence"),
            "reason": last.get("model_config_reason") or model_config_file.get("reason"),
            "loaded_at": last.get("model_config_loaded_at"),
            "error": last.get("model_config_error"),
            "applied": last.get("model_config_applied") or model_config_file.get("parameters") or {},
            "disable_sides": last.get("model_config_disable_sides") or model_config_file.get("disable_sides") or [],
            "side_min_confidence": (
                last.get("model_config_side_min_confidence")
                or model_config_file.get("side_min_confidence")
                or model_parameters.get("side_min_confidence")
                or {}
            ),
            "side_bias": (
                last.get("model_config_side_bias")
                or model_config_file.get("side_bias")
                or model_parameters.get("side_bias")
                or {}
            ),
            "sample_count": _as_int(model_config_file.get("sample_count")),
            "trained_at": model_config_file.get("trained_at"),
        },
        "position": _bankroll_position(last.get("active_position")),
        "spot": {
            "price": _round_float(last.get("spot"), 2),
            "source": last.get("spot_source"),
            "stale": _as_bool(last.get("spot_stale")),
            "age_seconds": _round_float(last.get("spot_age_seconds"), 2),
        },
        "market": {
            "ticker": last.get("ticker"),
            "strike": _round_float(last.get("strike"), 2),
            "seconds_to_close": _round_float(last.get("seconds_to_close"), 2),
            "title": last.get("title"),
        },
        "chart_points": _bankroll_chart_points(events),
        "trade_markers": _bankroll_trade_markers(events),
        "trade_ledger": _bankroll_trade_ledger(ledger_rows),
        "trade_stats": _bankroll_trade_stats(ledger_rows),
    }


def _team_rows(teams):
    if not isinstance(teams, dict):
        return []
    rows = []
    for code, team in teams.items():
        if not isinstance(team, dict):
            continue
        strike = _first_present(team.get("strike_chance"), team.get("strike"))
        if strike is None and not any(
            key in team
            for key in ("two_point_chance", "three_point_chance", "hamiltonian", "H", "psi_squared", "psi_sq")
        ):
            continue
        rows.append(
            {
                "code": code,
                "role": team.get("role"),
                "offense": team.get("offense"),
                "display_name": team.get("display_name"),
                "record": team.get("record"),
                "score": _as_int(team.get("score")),
                "rating": _round_float(team.get("rating"), 2),
                "strike_chance": _round_float(strike, 2),
                "two_point_chance": _round_float(team.get("two_point_chance"), 2),
                "three_point_chance": _round_float(team.get("three_point_chance"), 2),
                "moneyline": _as_int(team.get("moneyline")),
                "implied_probability": _round_float(team.get("implied_probability"), 4),
                "model_win_probability": _round_float(team.get("model_win_probability"), 4),
                "injury_impact": _round_float(team.get("injury_impact"), 2),
                "hamiltonian": _round_float(team.get("hamiltonian") or team.get("H"), 4),
                "psi_squared": _round_float(team.get("psi_squared") or team.get("psi_sq"), 2),
            }
        )
    return rows


def _series_points(limit=12):
    series = _read_json(PRIVATE_RUNTIME_DIR / "series_history.json", [])
    if not isinstance(series, list):
        return []
    points = []
    for row in series[-limit:]:
        if not isinstance(row, dict):
            continue
        possession = row.get("possession") if isinstance(row.get("possession"), dict) else {}
        matchup = row.get("matchup") if isinstance(row.get("matchup"), dict) else {}
        if not matchup or not isinstance(possession.get("probabilities"), dict):
            continue
        teams = row.get("teams") if "teams" in row else row
        teams = teams if isinstance(teams, dict) else {}
        team_rows = _team_rows(teams)
        points.append(
            {
                "time": row.get("timestamp"),
                "entropy": row.get("entropy"),
                "matchup": matchup,
                "possession": possession,
                "teams": team_rows,
            }
        )
    return points


def _sanitize_macro_series(rows, limit=60):
    if not isinstance(rows, list):
        return []
    points = []
    for row in rows[-limit:]:
        if not isinstance(row, dict):
            continue
        point = {
            "time": row.get("timestamp") or row.get("time"),
            "spread": _round_float(_first_present(row.get("spread"), row.get("spread_delta")), 4),
            "z_score": _round_float(row.get("z_score"), 4),
            "primary": _round_float(_first_present(row.get("primary"), row.get("a_price"), row.get("left_price")), 4),
            "hedge": _round_float(_first_present(row.get("hedge"), row.get("b_price"), row.get("right_price")), 4),
            "status": row.get("status") or row.get("state"),
        }
        points.append(point)
    return points


def _sanitize_macro_markers(rows, limit=12):
    if not isinstance(rows, list):
        return []
    markers = []
    for row in rows[-limit:]:
        if not isinstance(row, dict):
            continue
        markers.append(
            {
                "time": row.get("timestamp") or row.get("time"),
                "symbol": row.get("symbol") or row.get("ticker"),
                "side": row.get("side") or row.get("action"),
                "price": _round_float(row.get("price"), 4),
                "reason": row.get("reason") or row.get("setup"),
            }
        )
    return markers


def _macro_pair_summary(raw, key, label):
    if not isinstance(raw, dict):
        raw = {}
    pair = raw.get(key) or raw.get(label) or {}
    if not isinstance(pair, dict):
        pair = {}
    series = pair.get("series") or raw.get(f"{key}_series") or []
    markers = pair.get("paper_buy_markers") or pair.get("markers") or raw.get(f"{key}_paper_buy_markers") or []
    return {
        "pair": pair.get("pair") or label,
        "last_update": pair.get("last_update") or pair.get("timestamp"),
        "status": pair.get("status") or pair.get("state") or "awaiting_feed",
        "regime": pair.get("regime") or pair.get("regime_label"),
        "volatility": pair.get("volatility") or pair.get("volatility_label"),
        "spread_delta": _round_float(_first_present(pair.get("spread_delta"), pair.get("latest_delta"), pair.get("delta")), 4),
        "z_score": _round_float(pair.get("z_score"), 4),
        "divergence_confirmed": _as_bool(_first_present(pair.get("divergence_confirmed"), pair.get("confirmed"))),
        "series": _sanitize_macro_series(series),
        "paper_buy_markers": _sanitize_macro_markers(markers),
    }


def _robinhood_macro_summary():
    raw = _read_json(PRIVATE_RUNTIME_DIR / "robinhood_macro.json", {})
    arbitrage = _read_json(PRIVATE_RUNTIME_DIR / "arbitrage.json", {})
    inverse_arb = _read_json(PRIVATE_RUNTIME_DIR / "inverse_arb.json", {})
    source_present = any(isinstance(item, dict) and item for item in (raw, arbitrage, inverse_arb))
    merged = {}
    for item in (arbitrage, inverse_arb, raw):
        if isinstance(item, dict):
            merged.update(item)

    uso_xom = _macro_pair_summary(merged, "uso_xom", "USO/XOM")
    tsla_wti = _macro_pair_summary(merged, "tsla_wti", "TSLA/WTI")
    pair_statuses = [uso_xom.get("status"), tsla_wti.get("status")]
    live_status = next((status for status in pair_statuses if status and status != "awaiting_feed"), None)

    return {
        "source": "sanitized private runtime artifacts",
        "status": live_status or ("available" if source_present else "awaiting_feed"),
        "last_update": merged.get("last_update") or merged.get("timestamp"),
        "pairs": {
            "uso_xom": uso_xom,
            "tsla_wti": tsla_wti,
        },
        "fleet_summary": merged.get("fleet_summary") or merged.get("summary"),
    }


def _nba_physics_explainer(live_score):
    """Plain-language + desk-level reading of the possession physics."""
    barrier = _as_float(live_score.get("defensive_barrier"))
    pressure = "heavy" if (barrier is not None and barrier >= 0.5) else "light"
    return {
        "headline": "What the possession math is actually doing",
        "simple": (
            "Think of the next shot like a coin that has not landed yet. Fast, well-spaced "
            "ball movement tilts the odds toward a made 2 or 3, while a defender crowding the "
            "shooter tilts them back toward a miss. The numbers below are just that tilt, "
            "written out."
        ),
        "technical": (
            "H = K-hat + V-hat. K-hat encodes velocity-driven off-diagonal coupling (speed, "
            "burst, spacing x shot-zone bias) that moves amplitude into the 2- and 3-point "
            "states. V-hat is a diagonal defensive potential barrier from rim/closeout pressure "
            "that suppresses those transitions. The state evolves under "
            "i*sigma*dPsi/dt = H*Psi, and the reported probabilities are |Psi|^2 of the evolved "
            "state."
        ),
        "captions": {
            "kinetic": "Kinetic (K-hat) = how movement opens scoring lanes.",
            "potential": "Potential (V-hat) = how the defense walls those lanes off.",
            "hamiltonian": "Total (H = K-hat + V-hat) = the full energy the shot evolves under.",
            "sigma": "Sigma = the clock speed of the evolution (how fast the odds settle).",
        },
        "defensive_read": f"Current defensive pressure reads as {pressure}.",
    }


def _nba_live_summary(live_score):
    if not isinstance(live_score, dict):
        live_score = {}
    return {
        "game": live_score.get("game") or {
            "id": live_score.get("game_id"),
            "away": (live_score.get("matchup") or {}).get("away"),
            "home": (live_score.get("matchup") or {}).get("home"),
        },
        "matchup": live_score.get("matchup", {}),
        "teams": _team_rows(live_score.get("teams", {})),
        "odds": live_score.get("odds", {}),
        "injuries": live_score.get("injuries", []),
        "live_adjustments": live_score.get("live_adjustments", {}),
        "possession": live_score.get("possession", {}),
        "entropy": live_score.get("entropy"),
        "hamiltonian": live_score.get("hamiltonian"),
        "kinetic": live_score.get("kinetic"),
        "potential": live_score.get("potential"),
        "sigma": live_score.get("sigma"),
        "physics_explainer": _nba_physics_explainer(live_score),
        "defensive_barrier": live_score.get("defensive_barrier"),
        "offensive_velocity": live_score.get("offensive_velocity"),
        "court_position": live_score.get("court_position"),
        "threshold": live_score.get("threshold"),
        "source": live_score.get("source"),
        "last_update": live_score.get("timestamp"),
        "series": _series_points(),
    }


def build_public_feed():
    live_score = _read_json(PRIVATE_RUNTIME_DIR / "live_score.json", {})
    web_status = _read_json(PRIVATE_RUNTIME_DIR / "web_status.json", {})
    robinhood_macro = _robinhood_macro_summary()
    nba_live = _nba_live_summary(live_score)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "labels": {
            "execution": "paper/simulation/delayed",
            "disclaimer": (
                "Showcase telemetry only. Paper/simulation results and hypothetical scale views "
                "are not financial advice; no live broker execution is exposed."
            ),
        },
        "system": {
            "last_updated": web_status.get("last_updated") or live_score.get("timestamp"),
            "source": "sanitized local runtime artifacts",
        },
        "btc": {
            "signal": "guarded prediction-contract paper router",
            "mode": "paper",
            "performance": _paper_summary(PRIVATE_JOURNAL_DIR / "trade_journal.jsonl"),
        },
        "kalshi": _kalshi_summary(),
        "kalshi_btc": _kalshi_btc_summary(),
        "kalshi_bankroll": _kalshi_bankroll_summary(),
        "robinhood_macro": robinhood_macro,
        "nba_live": nba_live,
        "fase_veritas": {
            "entropy": live_score.get("entropy"),
            "matchup": live_score.get("matchup", {}),
            "possession": live_score.get("possession", {}),
            "teams": live_score.get("teams", {}),
            "team_rows": _team_rows(live_score.get("teams", {})),
            "hamiltonian": live_score.get("hamiltonian"),
            "defensive_barrier": live_score.get("defensive_barrier"),
            "offensive_velocity": live_score.get("offensive_velocity"),
            "court_position": live_score.get("court_position"),
            "threshold": live_score.get("threshold"),
            "projections": web_status.get("projections", {}),
            "series": _series_points(),
        },
    }


def write_public_feed(path: Path = PUBLIC_FEED_PATH):
    feed = build_public_feed()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(feed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def main():
    path = write_public_feed()
    print(f"Wrote sanitized public feed: {path}")


if __name__ == "__main__":
    main()
