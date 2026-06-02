"""
Patient $100 -> $200 Kalshi BTC bankroll paper engine.

Sibling to ``hvl.kalshi.kalshi_gamma_regime_engine``.  Reuses the same data
plumbing (``KalshiClient``, ``orderbook_summary``, ``parse_strike``,
``fetch_spot``, ``TelemetryState``) without forking it, but maintains its
own bankroll, journal, gates, and slower poll cadence.

Highlights:
  * Drives entries from ``btc_taylor_forecast.TaylorForecaster``.
  * Sizes each paper entry as ``current_bankroll * TRADE_FRACTION`` clipped
    to ``[MIN_TRADE_USD, MAX_TRADE_USD]``.
  * Halts new entries once bankroll >= goal (``HARVEST``) or below the hard
    floor.  Existing positions are still managed to exit.
  * Gates the contrarian side behind a stricter ``high_liquidity_ok`` check
    so the engine only takes the wrong-way bet when the book is deep enough
    to scratch cleanly.
  * Paper only.  No live broker submission.
"""
from __future__ import annotations

import json
import os
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from dotenv import load_dotenv

from hvl.kalshi.btc_taylor_forecast import (
    FORECAST_DROP,
    FORECAST_FLAT,
    FORECAST_RALLY,
    FORECAST_WARMING_UP,
    TaylorForecaster,
)
from hvl.kalshi.kalshi_client import KalshiClient, orderbook_summary, parse_strike
from hvl.kalshi.kalshi_gamma_regime_engine import (
    TelemetryState,
    cached_markets,
    close_price,
    depth_ok,
    fetch_spot,
    kalshi_api_fields,
    market_score,
    midpoint,
    seconds_to_close,
    side_book_ok,
    side_price,
    spread_ok,
)
from hvl.utils.paths import PRIVATE_DATA_DIR, PRIVATE_JOURNAL_DIR, SECRETS_DIR


load_dotenv(SECRETS_DIR / ".env")


def _env_bool(name: str, default: str) -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


# -- Bankroll constraints --
BANKROLL_START_USD = float(os.getenv("KALSHI_BANKROLL_START_USD", "100"))
BANKROLL_GOAL_USD = float(os.getenv("KALSHI_BANKROLL_GOAL_USD", "200"))
BANKROLL_MIN_TRADE_USD = float(os.getenv("KALSHI_BANKROLL_MIN_TRADE_USD", "10"))
BANKROLL_MAX_TRADE_USD = float(os.getenv("KALSHI_BANKROLL_MAX_TRADE_USD", "25"))
BANKROLL_TRADE_FRACTION = float(os.getenv("KALSHI_BANKROLL_TRADE_FRACTION", "0.20"))
BANKROLL_HARD_FLOOR_USD = float(os.getenv("KALSHI_BANKROLL_HARD_FLOOR_USD", "75"))

# -- High-liquidity gate (used to permit the contrarian side under DROP/RALLY) --
HIGH_LIQ_DEPTH = int(float(os.getenv("KALSHI_BANKROLL_HIGH_LIQ_DEPTH", "150")))
HIGH_LIQ_SPREAD = float(os.getenv("KALSHI_BANKROLL_HIGH_LIQ_SPREAD", "0.02"))
HIGH_LIQ_DECAY_MAX = float(os.getenv("KALSHI_BANKROLL_HIGH_LIQ_DECAY_MAX", "0"))

# -- Forecast parameters --
_FORECAST_HORIZONS_RAW = os.getenv("KALSHI_BANKROLL_FORECAST_HORIZONS_MIN", "15,30,60")
FORECAST_HORIZONS_SECONDS = tuple(
    float(chunk.strip()) * 60.0 for chunk in _FORECAST_HORIZONS_RAW.split(",") if chunk.strip()
) or (900.0, 1800.0, 3600.0)
FORECAST_EMA_WINDOW = float(os.getenv("KALSHI_BANKROLL_FORECAST_EMA_WINDOW", "30"))
FORECAST_SHORT_WINDOW = float(os.getenv("KALSHI_BANKROLL_FORECAST_SHORT_WINDOW", "60"))
FORECAST_MID_WINDOW = float(os.getenv("KALSHI_BANKROLL_FORECAST_MID_WINDOW", "180"))
FORECAST_LONG_WINDOW = float(os.getenv("KALSHI_BANKROLL_FORECAST_LONG_WINDOW", "600"))
FORECAST_DROP_USD = float(os.getenv("KALSHI_BANKROLL_FORECAST_DROP_USD", "-500"))
FORECAST_RALLY_USD = float(os.getenv("KALSHI_BANKROLL_FORECAST_RALLY_USD", "500"))
FORECAST_CONFIRM_TICKS = int(float(os.getenv("KALSHI_BANKROLL_FORECAST_CONFIRM_TICKS", "3")))
FORECAST_MIN_CONFIDENCE = float(os.getenv("KALSHI_BANKROLL_MIN_CONFIDENCE", "0.60"))
_DEFAULT_FORECAST_DROP_USD = FORECAST_DROP_USD
_DEFAULT_FORECAST_RALLY_USD = FORECAST_RALLY_USD
_DEFAULT_FORECAST_MIN_CONFIDENCE = FORECAST_MIN_CONFIDENCE

# -- Policy / loop --
ALLOW_FLAT_ENTRIES = _env_bool("KALSHI_BANKROLL_ALLOW_FLAT_ENTRIES", "false")
ALLOW_COUNTER_LIQUIDITY = _env_bool("KALSHI_BANKROLL_ALLOW_COUNTER_LIQUIDITY", "false")
POLL_SECONDS = float(os.getenv("KALSHI_BANKROLL_POLL_SECONDS", "5.0"))
MARKET_REFRESH_SECONDS = float(os.getenv("KALSHI_BANKROLL_MARKET_REFRESH_SECONDS", "60"))
EXIT_CONFIRM_TICKS = int(float(os.getenv("KALSHI_BANKROLL_EXIT_CONFIRM_TICKS", "3")))
MIN_HOLD_SECONDS = float(os.getenv("KALSHI_BANKROLL_MIN_HOLD_SECONDS", "0"))
LATE_EXIT_SECONDS = float(os.getenv("KALSHI_BANKROLL_LATE_EXIT_SECONDS", "600"))
# No NEW entries inside the final window before the contract closes.  Existing
# positions are still managed/exited; this only blocks fresh BUYs so the engine
# stops opening trades it will immediately have to sweep near expiry.
NO_ENTRY_FINAL_SECONDS = float(os.getenv("KALSHI_BANKROLL_NO_ENTRY_FINAL_SECONDS", "900"))
EXECUTION_DELAY_SECONDS = float(os.getenv("KALSHI_BANKROLL_EXECUTION_DELAY_SECONDS", "0.5"))
MAX_ORDERBOOK_SCAN = max(1, int(float(os.getenv("KALSHI_BANKROLL_MAX_ORDERBOOK_SCAN", "20"))))
_DEFAULT_BANKROLL_MAX_TRADE_USD = BANKROLL_MAX_TRADE_USD
_DEFAULT_BANKROLL_TRADE_FRACTION = BANKROLL_TRADE_FRACTION
_DEFAULT_NO_ENTRY_FINAL_SECONDS = NO_ENTRY_FINAL_SECONDS
_DEFAULT_EXIT_CONFIRM_TICKS = EXIT_CONFIRM_TICKS
_DEFAULT_MIN_HOLD_SECONDS = MIN_HOLD_SECONDS
_DEFAULT_SIDE_MIN_CONFIDENCE = {
    "YES": FORECAST_MIN_CONFIDENCE,
    "NO": FORECAST_MIN_CONFIDENCE,
}
SIDE_MIN_CONFIDENCE = dict(_DEFAULT_SIDE_MIN_CONFIDENCE)
SIDE_BIAS = {
    "preferred_side": None,
    "penalized_side": None,
    "confidence_adjustments": {},
    "reason": None,
}

MODEL_CONFIG_PATH = Path(os.getenv(
    "KALSHI_BANKROLL_MODEL_CONFIG_PATH",
    PRIVATE_DATA_DIR / "kalshi_training" / "bankroll_model_config.json",
))
MODEL_CONFIG_RELOAD_SECONDS = float(os.getenv("KALSHI_BANKROLL_MODEL_CONFIG_RELOAD_SECONDS", "300"))
MODEL_CONFIG_BOUNDS = {
    "min_confidence": (0.55, 0.95),
    "drop_threshold_usd": (
        _DEFAULT_FORECAST_DROP_USD * 1.20,
        _DEFAULT_FORECAST_DROP_USD * 0.80,
    ),
    "rally_threshold_usd": (
        _DEFAULT_FORECAST_RALLY_USD * 0.80,
        _DEFAULT_FORECAST_RALLY_USD * 1.20,
    ),
    "no_entry_final_seconds": (900.0, 3600.0),
    "min_hold_seconds": (0.0, 300.0),
    "exit_confirm_ticks": (1.0, 6.0),
    "side_min_confidence": (0.55, 0.95),
    "max_trade_usd": (BANKROLL_MIN_TRADE_USD, min(25.0, _DEFAULT_BANKROLL_MAX_TRADE_USD)),
    "trade_fraction": (0.05, min(0.20, _DEFAULT_BANKROLL_TRADE_FRACTION)),
}
_MODEL_CONFIG_STATE = {
    "active": False,
    "version": None,
    "reason": "no model config loaded",
    "loaded_at": None,
    "path": str(MODEL_CONFIG_PATH),
    "error": None,
    "applied": {},
    "disable_sides": [],
    "side_min_confidence": dict(SIDE_MIN_CONFIDENCE),
    "side_bias": dict(SIDE_BIAS),
}
_MODEL_CONFIG_LAST_CHECK = 0.0
_MODEL_CONFIG_MTIME = None

SERIES_TICKER = os.getenv("KALSHI_BTC_SERIES_TICKER", "KXBTCD")

JOURNAL_PATH = Path(os.getenv(
    "KALSHI_BANKROLL_JOURNAL_PATH",
    PRIVATE_JOURNAL_DIR / "kalshi_bankroll_journal.jsonl",
))

# Separate, human-readable ledger that holds exactly one row per completed
# paper trade (entry + exit paired) with full P/L and decision context.  This
# is derived bookkeeping; the tick-level JOURNAL_PATH above remains the system
# of record.
TRADE_LEDGER_PATH = Path(os.getenv(
    "KALSHI_BANKROLL_TRADE_LEDGER_PATH",
    PRIVATE_JOURNAL_DIR / "kalshi_bankroll_trade_ledger.jsonl",
))

# Local spot deque sized for ``long_window`` worth of derivative context plus
# margin.  Independent of the regime engine's TelemetryState so we can keep a
# longer history without disturbing the regime engine's own configuration.
_LOCAL_SPOT_HORIZON_SECONDS = max(FORECAST_LONG_WINDOW * 2.0, 1800.0)
_LOCAL_SPOT_MAXLEN = max(600, int(_LOCAL_SPOT_HORIZON_SECONDS / max(POLL_SECONDS, 0.1)) + 50)

USE_COLOR = os.getenv("USE_COLOR", "true").strip().lower() not in {"0", "false", "no", "off"}
_COLOR_CODES = {
    "green": "\033[92m",
    "red": "\033[91m",
    "yellow": "\033[93m",
    "cyan": "\033[96m",
    "gray": "\033[90m",
    "reset": "\033[0m",
}


def color(text, name: str) -> str:
    if not USE_COLOR:
        return str(text)
    return f"{_COLOR_CODES.get(name, '')}{text}{_COLOR_CODES['reset']}"


def _model_config_clip(name: str, value) -> Optional[float]:
    number = _as_float(value)
    if number is None or name not in MODEL_CONFIG_BOUNDS:
        return None
    low, high = MODEL_CONFIG_BOUNDS[name]
    return min(float(high), max(float(low), number))


def _model_config_parameters(raw: dict) -> dict:
    params = raw.get("parameters") if isinstance(raw.get("parameters"), dict) else raw
    applied = {}
    for src_key, dst_key in (
        ("min_confidence", "min_confidence"),
        ("drop_threshold_usd", "drop_threshold_usd"),
        ("rally_threshold_usd", "rally_threshold_usd"),
        ("no_entry_final_seconds", "no_entry_final_seconds"),
        ("min_hold_seconds", "min_hold_seconds"),
        ("exit_confirm_ticks", "exit_confirm_ticks"),
        ("max_trade_usd", "max_trade_usd"),
        ("trade_fraction", "trade_fraction"),
    ):
        clipped = _model_config_clip(src_key, params.get(src_key))
        if clipped is not None:
            applied[dst_key] = clipped
    side_min_confidence = params.get("side_min_confidence") or raw.get("side_min_confidence") or {}
    applied_side_min_confidence = dict(_DEFAULT_SIDE_MIN_CONFIDENCE)
    if isinstance(side_min_confidence, dict):
        low, high = MODEL_CONFIG_BOUNDS["side_min_confidence"]
        for side in ("YES", "NO"):
            value = _as_float(side_min_confidence.get(side))
            if value is not None:
                applied_side_min_confidence[side] = min(high, max(low, value))
    applied["side_min_confidence"] = applied_side_min_confidence
    side_bias = params.get("side_bias") or raw.get("side_bias") or {}
    applied["side_bias"] = side_bias if isinstance(side_bias, dict) else {}
    disable_sides = params.get("disable_sides") or raw.get("disable_sides") or []
    if isinstance(disable_sides, str):
        disable_sides = [disable_sides]
    applied["disable_sides"] = [
        side for side in disable_sides
        if side in {"YES", "NO"} and len(disable_sides) == 1
    ]
    return applied


def _apply_model_config(raw: dict, applied: dict) -> None:
    global BANKROLL_MAX_TRADE_USD
    global BANKROLL_TRADE_FRACTION
    global FORECAST_DROP_USD
    global FORECAST_RALLY_USD
    global FORECAST_MIN_CONFIDENCE
    global NO_ENTRY_FINAL_SECONDS
    global MIN_HOLD_SECONDS
    global EXIT_CONFIRM_TICKS
    global SIDE_MIN_CONFIDENCE
    global SIDE_BIAS

    BANKROLL_MAX_TRADE_USD = applied.get("max_trade_usd", _DEFAULT_BANKROLL_MAX_TRADE_USD)
    BANKROLL_TRADE_FRACTION = applied.get("trade_fraction", _DEFAULT_BANKROLL_TRADE_FRACTION)
    FORECAST_DROP_USD = applied.get("drop_threshold_usd", _DEFAULT_FORECAST_DROP_USD)
    FORECAST_RALLY_USD = applied.get("rally_threshold_usd", _DEFAULT_FORECAST_RALLY_USD)
    FORECAST_MIN_CONFIDENCE = applied.get("min_confidence", _DEFAULT_FORECAST_MIN_CONFIDENCE)
    NO_ENTRY_FINAL_SECONDS = applied.get("no_entry_final_seconds", _DEFAULT_NO_ENTRY_FINAL_SECONDS)
    MIN_HOLD_SECONDS = applied.get("min_hold_seconds", _DEFAULT_MIN_HOLD_SECONDS)
    EXIT_CONFIRM_TICKS = int(applied.get("exit_confirm_ticks", _DEFAULT_EXIT_CONFIRM_TICKS))
    SIDE_MIN_CONFIDENCE = applied.get("side_min_confidence", dict(_DEFAULT_SIDE_MIN_CONFIDENCE))
    SIDE_BIAS = applied.get("side_bias", {})
    _MODEL_CONFIG_STATE.update({
        "active": bool(raw.get("promoted", True)),
        "version": raw.get("model_config_version") or raw.get("config_version") or raw.get("trained_at"),
        "reason": raw.get("reason"),
        "loaded_at": datetime.now(timezone.utc).isoformat(),
        "path": str(MODEL_CONFIG_PATH),
        "error": None,
        "applied": {
            "min_confidence": FORECAST_MIN_CONFIDENCE,
            "drop_threshold_usd": FORECAST_DROP_USD,
            "rally_threshold_usd": FORECAST_RALLY_USD,
            "no_entry_final_seconds": NO_ENTRY_FINAL_SECONDS,
            "min_hold_seconds": MIN_HOLD_SECONDS,
            "exit_confirm_ticks": EXIT_CONFIRM_TICKS,
            "max_trade_usd": BANKROLL_MAX_TRADE_USD,
            "trade_fraction": BANKROLL_TRADE_FRACTION,
            "side_min_confidence": SIDE_MIN_CONFIDENCE,
            "side_bias": SIDE_BIAS,
        },
        "disable_sides": applied.get("disable_sides", []),
        "side_min_confidence": SIDE_MIN_CONFIDENCE,
        "side_bias": SIDE_BIAS,
    })


def reload_model_config(force: bool = False) -> dict:
    global _MODEL_CONFIG_LAST_CHECK
    global _MODEL_CONFIG_MTIME

    now = time.time()
    if not force and (now - _MODEL_CONFIG_LAST_CHECK) < MODEL_CONFIG_RELOAD_SECONDS:
        return _MODEL_CONFIG_STATE
    _MODEL_CONFIG_LAST_CHECK = now
    if not MODEL_CONFIG_PATH.exists():
        _MODEL_CONFIG_STATE.update({
            "active": False,
            "version": None,
            "reason": "model config file not found",
            "error": None,
            "path": str(MODEL_CONFIG_PATH),
            "applied": {},
            "disable_sides": [],
            "side_min_confidence": dict(_DEFAULT_SIDE_MIN_CONFIDENCE),
            "side_bias": dict(SIDE_BIAS),
        })
        return _MODEL_CONFIG_STATE
    try:
        mtime = MODEL_CONFIG_PATH.stat().st_mtime
        if not force and _MODEL_CONFIG_MTIME == mtime:
            return _MODEL_CONFIG_STATE
        raw = json.loads(MODEL_CONFIG_PATH.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("model config must be a JSON object")
        applied = _model_config_parameters(raw)
        _apply_model_config(raw, applied)
        _MODEL_CONFIG_MTIME = mtime
    except Exception as exc:
        _MODEL_CONFIG_STATE.update({
            "active": False,
            "error": str(exc),
            "reason": "failed to load model config",
            "path": str(MODEL_CONFIG_PATH),
        })
    return _MODEL_CONFIG_STATE


def _model_config_event_fields() -> dict:
    return {
        "model_config_active": bool(_MODEL_CONFIG_STATE.get("active")),
        "model_config_version": _MODEL_CONFIG_STATE.get("version"),
        "model_config_reason": _MODEL_CONFIG_STATE.get("reason"),
        "model_config_path": _MODEL_CONFIG_STATE.get("path"),
        "model_config_loaded_at": _MODEL_CONFIG_STATE.get("loaded_at"),
        "model_config_error": _MODEL_CONFIG_STATE.get("error"),
        "model_config_applied": _MODEL_CONFIG_STATE.get("applied") or {},
        "model_config_disable_sides": _MODEL_CONFIG_STATE.get("disable_sides") or [],
        "model_config_side_min_confidence": _MODEL_CONFIG_STATE.get("side_min_confidence") or {},
        "model_config_side_bias": _MODEL_CONFIG_STATE.get("side_bias") or {},
    }


def sync_forecaster_model_config(forecaster: TaylorForecaster) -> None:
    forecaster.drop_threshold = FORECAST_DROP_USD
    forecaster.rally_threshold = FORECAST_RALLY_USD
    forecaster.min_confidence = FORECAST_MIN_CONFIDENCE


def write_event(event: dict) -> None:
    event.update(_model_config_event_fields())
    JOURNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with JOURNAL_PATH.open("a", encoding="utf-8") as journal:
        journal.write(json.dumps(event, sort_keys=True) + "\n")


def write_trade_ledger(record: dict) -> None:
    """Append one completed paper trade (entry+exit paired) to the ledger."""
    TRADE_LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TRADE_LEDGER_PATH.open("a", encoding="utf-8") as ledger:
        ledger.write(json.dumps(record, sort_keys=True) + "\n")


def _next_trade_id() -> int:
    """Monotonic trade counter derived from the existing ledger length."""
    if not TRADE_LEDGER_PATH.exists():
        return 1
    try:
        count = sum(
            1 for line in TRADE_LEDGER_PATH.read_text(encoding="utf-8", errors="ignore").splitlines()
            if line.strip()
        )
    except OSError:
        return 1
    return count + 1


def _as_float(value, default: Optional[float] = None) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _timestamp_epoch(value) -> Optional[float]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _held_seconds(active: dict, exit_epoch: Optional[float] = None) -> Optional[float]:
    exit_epoch = exit_epoch or time.time()
    entry_epoch = _as_float(active.get("entry_epoch"))
    if entry_epoch is None or active.get("restored_from_journal"):
        entry_epoch = _timestamp_epoch(active.get("entry_timestamp"))
    if entry_epoch is None:
        return None
    return max(0.0, exit_epoch - entry_epoch)


def _active_is_expired(active: dict, now: datetime) -> bool:
    close_seconds = seconds_to_close(active.get("entry_close_time"), now)
    return close_seconds is not None and close_seconds <= 0


def _settlement_price_for_spot(side: str, spot: Optional[float], strike: Optional[float]) -> Optional[float]:
    """Paper settlement approximation for expired BTC binary contracts."""
    if spot is None or strike is None:
        return None
    if side == "YES":
        return 1.0 if spot > strike else 0.0
    if side == "NO":
        return 1.0 if spot <= strike else 0.0
    return None


def _completed_trade_record(
    active: dict,
    *,
    exit_timestamp: str,
    exit_price: float,
    exit_spot: Optional[float],
    exit_reason: str,
    exit_seconds_to_close: Optional[float],
    held_seconds: Optional[float],
    proceeds: float,
    pnl: float,
    bankroll_current: float,
    realized_pnl: float,
) -> dict:
    entry_notional = _as_float(active.get("entry_notional"), 0.0) or 0.0
    return_pct = round((pnl / entry_notional) * 100.0, 4) if entry_notional else None
    return {
        "trade_id": active.get("trade_id"),
        "mode": "kalshi_bankroll_paper",
        "engine_name": "kalshi_bankroll_engine",
        "side": active.get("side"),
        "ticker": active.get("entry_ticker"),
        "quantity": active.get("quantity"),
        "entry_timestamp": active.get("entry_timestamp"),
        "entry_price": active.get("entry_price"),
        "entry_notional": round(entry_notional, 4),
        "entry_spot": active.get("entry_spot"),
        "entry_strike": active.get("entry_strike"),
        "entry_seconds_to_close": active.get("entry_seconds_to_close"),
        "entry_forecast_state": active.get("entry_forecast_state"),
        "entry_forecast_confidence": active.get("entry_forecast_confidence"),
        "entry_forecast_projected_30m": active.get("entry_forecast_projected_30m"),
        "entry_forecast_projected_60m": active.get("entry_forecast_projected_60m"),
        "entry_min_hold_seconds": active.get("entry_min_hold_seconds"),
        "entry_exit_confirm_ticks": active.get("entry_exit_confirm_ticks"),
        "entry_side_min_confidence": active.get("entry_side_min_confidence"),
        "entry_side_bias": active.get("entry_side_bias"),
        "exit_timestamp": exit_timestamp,
        "exit_price": exit_price,
        "exit_spot": exit_spot,
        "exit_proceeds_usd": round(proceeds, 4),
        "exit_reason": exit_reason,
        "exit_seconds_to_close": exit_seconds_to_close,
        "held_seconds": round(held_seconds, 2) if held_seconds is not None else None,
        "realized_pnl": round(pnl, 4),
        "return_pct": return_pct,
        "max_unrealized_pnl": round(active.get("max_unrealized_pnl", 0.0), 4),
        "min_unrealized_pnl": round(active.get("min_unrealized_pnl", 0.0), 4),
        "win": bool(pnl > 0),
        "bankroll_after_usd": round(bankroll_current, 4),
        "total_realized_pnl": round(realized_pnl, 4),
        "restored_from_journal": bool(active.get("restored_from_journal")),
    }


def load_state_from_journal():
    """Resume bankroll, realized P/L, and any open paper position from disk.

    The journal is the system of record; the engine restarts at whatever the
    last accounting row says.  If the last action was a BUY without a
    matching SELL the orphaned position is rehydrated so its notional is not
    silently double-spent on restart.
    """
    bankroll = BANKROLL_START_USD
    realized = 0.0
    active: Optional[dict] = None
    if not JOURNAL_PATH.exists():
        return bankroll, realized, active
    try:
        rows = []
        for line in JOURNAL_PATH.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except OSError:
        return bankroll, realized, active

    for row in rows:
        if "bankroll_current_usd" in row:
            try:
                bankroll = float(row["bankroll_current_usd"])
            except (TypeError, ValueError):
                pass
        if "total_realized_pnl" in row:
            try:
                realized = float(row["total_realized_pnl"])
            except (TypeError, ValueError):
                pass

    for row in reversed(rows):
        action = row.get("action")
        if action == "SELL":
            break
        if action == "BUY":
            try:
                quantity = int(float(row.get("quantity") or 0))
            except (TypeError, ValueError):
                quantity = 0
            if quantity <= 0:
                break
            active = {
                "trade_id": row.get("trade_id"),
                "side": row.get("side"),
                "entry_price": row.get("entry_price"),
                "entry_notional": row.get("entry_notional"),
                "quantity": quantity,
                "entry_timestamp": row.get("timestamp"),
                "entry_epoch": time.time(),
                "entry_ticker": row.get("ticker") or row.get("active_ticker"),
                "entry_close_time": row.get("market_close_time"),
                "entry_spot": row.get("spot"),
                "entry_strike": row.get("strike"),
                "entry_seconds_to_close": row.get("seconds_to_close"),
                "entry_forecast_state": row.get("forecast_state"),
                "entry_forecast_confidence": row.get("forecast_confidence"),
                "entry_forecast_projected_30m": row.get("projected_30m"),
                "entry_forecast_projected_60m": row.get("projected_60m"),
                "entry_min_hold_seconds": row.get("min_hold_seconds"),
                "entry_exit_confirm_ticks": row.get("exit_confirm_ticks_required"),
                "entry_side_min_confidence": row.get("candidate_min_confidence"),
                "entry_side_bias": row.get("side_bias"),
                "max_unrealized_pnl": 0.0,
                "min_unrealized_pnl": 0.0,
                "exit_confirm_ticks": 0,
                "restored_from_journal": True,
            }
            now = datetime.now(timezone.utc)
            if _active_is_expired(active, now):
                latest_spot = next(
                    (
                        _as_float(history_row.get("spot"))
                        for history_row in reversed(rows)
                        if _as_float(history_row.get("spot")) is not None
                    ),
                    None,
                )
                strike = _as_float(active.get("entry_strike"))
                if strike is None:
                    strike = _as_float(parse_strike(active.get("entry_ticker")))
                exit_price = _settlement_price_for_spot(active.get("side"), latest_spot, strike)
                settlement_status = "spot_settlement"
                if exit_price is None:
                    exit_price = 0.0
                    settlement_status = "unknown_settlement_assumed_zero"
                entry_price = _as_float(active.get("entry_price"), 0.0) or 0.0
                proceeds = exit_price * quantity
                pnl = (exit_price - entry_price) * quantity
                bankroll += proceeds
                realized += pnl
                close_seconds = seconds_to_close(active.get("entry_close_time"), now)
                held = _held_seconds(active, now.timestamp())
                settlement_event = {
                    "timestamp": now.isoformat(),
                    "mode": "kalshi_bankroll_paper",
                    "engine_name": "kalshi_bankroll_engine",
                    "action": "SELL",
                    "side": active.get("side"),
                    "ticker": active.get("entry_ticker"),
                    "market_close_time": active.get("entry_close_time"),
                    "seconds_to_close": close_seconds,
                    "spot": latest_spot,
                    "strike": strike,
                    "exit_reason": "contract_expired_on_restart",
                    "exit_price": exit_price,
                    "quantity": quantity,
                    "exit_proceeds_usd": round(proceeds, 4),
                    "realized_pnl": round(pnl, 4),
                    "total_realized_pnl": round(realized, 4),
                    "bankroll_current_usd": round(bankroll, 4),
                    "bankroll_start_usd": BANKROLL_START_USD,
                    "bankroll_goal_usd": BANKROLL_GOAL_USD,
                    "bankroll_drawdown_usd": round(BANKROLL_START_USD - bankroll, 4),
                    "expired_position_reconciled": True,
                    "settlement_status": settlement_status,
                    "active_position": active,
                }
                write_event(settlement_event)
                write_trade_ledger(_completed_trade_record(
                    active,
                    exit_timestamp=now.isoformat(),
                    exit_price=exit_price,
                    exit_spot=latest_spot,
                    exit_reason="contract_expired_on_restart",
                    exit_seconds_to_close=close_seconds,
                    held_seconds=held,
                    proceeds=proceeds,
                    pnl=pnl,
                    bankroll_current=bankroll,
                    realized_pnl=realized,
                ))
                active = None
            break
    return bankroll, realized, active


def high_liquidity_diagnostic(summary: dict, liquidity_decay: Optional[float]) -> dict:
    """Strict liquidity gate for the contrarian side under DROP/RALLY."""
    yes_bid = summary.get("yes_bid") or {}
    no_bid = summary.get("no_bid") or {}
    yes_depth = int(yes_bid.get("quantity") or 0)
    no_depth = int(no_bid.get("quantity") or 0)
    yes_spread = summary.get("yes_spread")
    no_spread = summary.get("no_spread")
    depth_ok_flag = yes_depth >= HIGH_LIQ_DEPTH and no_depth >= HIGH_LIQ_DEPTH
    spread_ok_flag = (
        yes_spread is not None and yes_spread <= HIGH_LIQ_SPREAD
        and no_spread is not None and no_spread <= HIGH_LIQ_SPREAD
    )
    decay_ok_flag = (liquidity_decay is None) or (float(liquidity_decay) >= HIGH_LIQ_DECAY_MAX)
    return {
        "ok": bool(depth_ok_flag and spread_ok_flag and decay_ok_flag),
        "depth_threshold": HIGH_LIQ_DEPTH,
        "spread_threshold": HIGH_LIQ_SPREAD,
        "decay_max": HIGH_LIQ_DECAY_MAX,
        "yes_depth": yes_depth,
        "no_depth": no_depth,
        "yes_spread": yes_spread,
        "no_spread": no_spread,
        "depth_ok": bool(depth_ok_flag),
        "spread_ok": bool(spread_ok_flag),
        "decay_ok": bool(decay_ok_flag),
    }


def select_bankroll_market(client: KalshiClient, spot: float):
    """Pick the strike-nearest BTC market with both sides quotable.

    Reuses ``cached_markets`` from the regime engine to share the same
    market-list cache and avoid pounding the markets endpoint.  The market
    chosen here is just the *candidate*; the actual high-liquidity gate is
    applied later at entry time so we don't reject markets that may still be
    useful purely for forecasting.
    """
    markets, cache_meta = cached_markets(client)
    candidates = [m for m in markets if parse_strike(m.get("ticker")) is not None]
    if not candidates:
        return None, None, {**cache_meta, "kalshi_orderbook_scan_count": 0}
    ordered = sorted(candidates, key=lambda m: market_score(m, spot))
    fallback = ordered[0]
    quoted = None
    scan_count = 0
    for market in ordered[:MAX_ORDERBOOK_SCAN]:
        scan_count += 1
        summary = orderbook_summary(client.orderbook(market["ticker"], depth=100))
        if summary["yes_bid"]["price"] is not None and summary["no_bid"]["price"] is not None:
            if quoted is None:
                quoted = (market, summary)
            high_liq = high_liquidity_diagnostic(summary, 0.0)
            if high_liq["ok"]:
                return market, summary, {**cache_meta, "kalshi_orderbook_scan_count": scan_count}
    if quoted is not None:
        market, summary = quoted
        return market, summary, {**cache_meta, "kalshi_orderbook_scan_count": scan_count}
    scan_count += 1
    return fallback, orderbook_summary(client.orderbook(fallback["ticker"], depth=100)), {
        **cache_meta,
        "kalshi_orderbook_scan_count": scan_count,
    }


def compute_sizing(bankroll_current: float, entry_price: Optional[float]) -> dict:
    """Bankroll-aware sizing per the plan."""
    target = max(0.0, bankroll_current) * BANKROLL_TRADE_FRACTION
    notional = min(BANKROLL_MAX_TRADE_USD, max(BANKROLL_MIN_TRADE_USD, target))
    if notional > bankroll_current:
        notional = max(0.0, bankroll_current)
    if entry_price is None or entry_price <= 0:
        return {
            "target_notional": round(target, 4),
            "notional": round(notional, 4),
            "quantity": 0,
            "block_reason": "no_entry_price",
        }
    if notional < BANKROLL_MIN_TRADE_USD:
        return {
            "target_notional": round(target, 4),
            "notional": round(notional, 4),
            "quantity": 0,
            "block_reason": "bankroll_floor_blocked",
        }
    quantity = int(notional // entry_price)
    if quantity <= 0:
        return {
            "target_notional": round(target, 4),
            "notional": round(notional, 4),
            "quantity": 0,
            "block_reason": "quantity_zero",
        }
    return {
        "target_notional": round(target, 4),
        "notional": round(quantity * entry_price, 4),
        "quantity": quantity,
        "block_reason": None,
    }


def _spot_window_append(window: deque, timestamp: float, spot: float) -> None:
    if spot and spot > 0:
        window.append((float(timestamp), float(spot)))
        while window and (timestamp - window[0][0]) > _LOCAL_SPOT_HORIZON_SECONDS:
            window.popleft()


def _candidate_for_state(forecast_state: str) -> Optional[str]:
    if forecast_state == FORECAST_RALLY:
        return "YES"
    if forecast_state == FORECAST_DROP:
        return "NO"
    return None


def _contrarian_for_state(forecast_state: str) -> Optional[str]:
    if forecast_state == FORECAST_RALLY:
        return "NO"
    if forecast_state == FORECAST_DROP:
        return "YES"
    return None


def _side_required_confidence(side: Optional[str]) -> float:
    low, high = MODEL_CONFIG_BOUNDS["side_min_confidence"]
    raw_base = SIDE_MIN_CONFIDENCE.get(side, FORECAST_MIN_CONFIDENCE) if side else FORECAST_MIN_CONFIDENCE
    base = _as_float(raw_base, FORECAST_MIN_CONFIDENCE) or FORECAST_MIN_CONFIDENCE
    adjustments = SIDE_BIAS.get("confidence_adjustments") if isinstance(SIDE_BIAS, dict) else {}
    adjustment = _as_float((adjustments or {}).get(side), 0.0) if side else 0.0
    adjusted_floor = FORECAST_MIN_CONFIDENCE + adjustment
    return min(high, max(low, max(FORECAST_MIN_CONFIDENCE, base, adjusted_floor)))


def run() -> None:
    client = KalshiClient()
    telemetry = TelemetryState()
    model_config = reload_model_config(force=True)
    forecaster = TaylorForecaster(
        ema_window_seconds=FORECAST_EMA_WINDOW,
        short_window_seconds=FORECAST_SHORT_WINDOW,
        mid_window_seconds=FORECAST_MID_WINDOW,
        long_window_seconds=FORECAST_LONG_WINDOW,
        horizons_seconds=FORECAST_HORIZONS_SECONDS,
        drop_threshold_usd=FORECAST_DROP_USD,
        rally_threshold_usd=FORECAST_RALLY_USD,
        confirm_ticks=FORECAST_CONFIRM_TICKS,
        min_confidence=FORECAST_MIN_CONFIDENCE,
    )
    bankroll_current, realized_pnl, active = load_state_from_journal()
    local_spot_window: deque = deque(maxlen=_LOCAL_SPOT_MAXLEN)
    selected_market = None
    selected_at = 0.0

    print("[KALSHI-BANKROLL] paper bankroll engine online", flush=True)
    print(f"[KALSHI-BANKROLL] env={client.env} rest={client.base_url}", flush=True)
    print(f"[KALSHI-BANKROLL] journal={JOURNAL_PATH}", flush=True)
    print(f"[KALSHI-BANKROLL] model_config={MODEL_CONFIG_PATH}", flush=True)
    if model_config.get("version"):
        print(
            f"[KALSHI-BANKROLL] model_config_version={model_config.get('version')} "
            f"active={model_config.get('active')}",
            flush=True,
        )
    print(
        f"[KALSHI-BANKROLL] bankroll={bankroll_current:.2f} "
        f"goal={BANKROLL_GOAL_USD:.2f} floor={BANKROLL_HARD_FLOOR_USD:.2f}",
        flush=True,
    )
    if active:
        print(
            f"[KALSHI-BANKROLL] restored active position side={active['side']} "
            f"ticker={active['entry_ticker']} qty={active['quantity']} "
            f"entry={active['entry_price']}",
            flush=True,
        )
    print("[KALSHI-BANKROLL] no live orders submitted", flush=True)

    while True:
        now = datetime.now(timezone.utc)
        try:
            reload_model_config()
            sync_forecaster_model_config(forecaster)
            spot_meta = fetch_spot()
            spot = float(spot_meta["price"] or 0.0)
            fresh_spot = spot > 0 and not spot_meta["stale"]
            tick_epoch = time.time()
            _spot_window_append(local_spot_window, tick_epoch, spot)

            kalshi_api_state = "ok"
            kalshi_error = None
            kalshi_market_cache_age_seconds = None
            kalshi_orderbook_scan_count = 0
            market = selected_market
            summary = None
            refresh_market = (
                fresh_spot
                and (selected_market is None or (time.time() - selected_at) >= MARKET_REFRESH_SECONDS)
            )
            if refresh_market:
                try:
                    market, summary, selection_meta = select_bankroll_market(client, spot)
                    selected_market = market
                    selected_at = time.time()
                    kalshi_market_cache_age_seconds = selection_meta.get("kalshi_market_cache_age_seconds")
                    kalshi_orderbook_scan_count = selection_meta.get("kalshi_orderbook_scan_count", 0)
                except Exception as exc:
                    kalshi_api_state = "market_discovery_degraded"
                    kalshi_error = str(exc)
                    market = selected_market

            if not market:
                action = "stale_spot_wait" if not fresh_spot else "no_market_selected"
                write_event({
                    "timestamp": now.isoformat(),
                    "mode": "kalshi_bankroll_paper",
                    "action": action,
                    "spot": spot,
                    "spot_source": spot_meta["source"],
                    "spot_age_seconds": spot_meta["age_seconds"],
                    "spot_stale": spot_meta["stale"],
                    "spot_error": spot_meta["error"],
                    "bankroll_current_usd": round(bankroll_current, 4),
                    "bankroll_start_usd": BANKROLL_START_USD,
                    "bankroll_goal_usd": BANKROLL_GOAL_USD,
                    "bankroll_drawdown_usd": round(BANKROLL_START_USD - bankroll_current, 4),
                    "bankroll_hard_floor_usd": BANKROLL_HARD_FLOOR_USD,
                    "total_realized_pnl": round(realized_pnl, 4),
                    **kalshi_api_fields(
                        client,
                        status=kalshi_api_state,
                        error=kalshi_error,
                        market_cache_age_seconds=kalshi_market_cache_age_seconds,
                        orderbook_scan_count=kalshi_orderbook_scan_count,
                    ),
                })
                print(f"[KALSHI-BANKROLL] {action}", flush=True)
                time.sleep(POLL_SECONDS)
                continue

            if summary is None:
                try:
                    kalshi_orderbook_scan_count += 1
                    summary = orderbook_summary(client.orderbook(market["ticker"], depth=100))
                except Exception as exc:
                    write_event({
                        "timestamp": now.isoformat(),
                        "mode": "kalshi_bankroll_paper",
                        "action": "orderbook_degraded",
                        "ticker": market.get("ticker"),
                        "spot": spot,
                        "bankroll_current_usd": round(bankroll_current, 4),
                        "bankroll_goal_usd": BANKROLL_GOAL_USD,
                        **kalshi_api_fields(
                            client,
                            status="orderbook_degraded",
                            error=str(exc),
                            market_cache_age_seconds=kalshi_market_cache_age_seconds,
                            orderbook_scan_count=kalshi_orderbook_scan_count,
                        ),
                    })
                    print(f"[KALSHI-BANKROLL] orderbook degraded: {exc}", flush=True)
                    time.sleep(POLL_SECONDS)
                    continue

            ticker = market["ticker"]
            market_close_time = market.get("close_time") or market.get("expiration_time")
            market_seconds_to_close = seconds_to_close(market_close_time, now)
            yes_mid = midpoint(summary["yes_bid"]["price"], summary["yes_ask"])
            no_mid = midpoint(summary["no_bid"]["price"], summary["no_ask"])
            liquidity = summary["yes_bid"]["quantity"] + summary["no_bid"]["quantity"]
            telemetry.update(
                timestamp=tick_epoch, spot=spot, yes_mid=yes_mid, no_mid=no_mid, liquidity=liquidity,
            )
            laplace = telemetry.laplace_drift()
            liquidity_decay = laplace.get("liquidity_decay")
            forecast = forecaster.update(local_spot_window)
            high_liq = high_liquidity_diagnostic(summary, liquidity_decay)
            spread_is_ok = spread_ok(summary)
            depth_is_ok = depth_ok(summary)
            strike = parse_strike(ticker)
            harvest_active = bankroll_current >= BANKROLL_GOAL_USD
            floor_blocked = bankroll_current < BANKROLL_HARD_FLOOR_USD
            final_window_blocked = (
                market_seconds_to_close is not None
                and market_seconds_to_close <= NO_ENTRY_FINAL_SECONDS
            )

            event = {
                "timestamp": now.isoformat(),
                "mode": "kalshi_bankroll_paper",
                "engine_name": "kalshi_bankroll_engine",
                "ticker": ticker,
                "event_ticker": market.get("event_ticker"),
                "market_close_time": market_close_time,
                "seconds_to_close": market_seconds_to_close,
                "title": market.get("title") or market.get("subtitle"),
                "spot": spot,
                "spot_source": spot_meta["source"],
                "spot_age_seconds": spot_meta["age_seconds"],
                "spot_stale": spot_meta["stale"],
                "strike": strike,
                "yes_bid": summary["yes_bid"],
                "yes_ask": summary["yes_ask"],
                "yes_spread": summary["yes_spread"],
                "no_bid": summary["no_bid"],
                "no_ask": summary["no_ask"],
                "no_spread": summary["no_spread"],
                "liquidity": liquidity,
                "liquidity_decay": liquidity_decay,
                "spread_ok": spread_is_ok,
                "depth_ok": depth_is_ok,
                "bankroll_current_usd": round(bankroll_current, 4),
                "bankroll_start_usd": BANKROLL_START_USD,
                "bankroll_goal_usd": BANKROLL_GOAL_USD,
                "bankroll_min_trade_usd": BANKROLL_MIN_TRADE_USD,
                "bankroll_max_trade_usd": BANKROLL_MAX_TRADE_USD,
                "bankroll_trade_fraction": BANKROLL_TRADE_FRACTION,
                "bankroll_hard_floor_usd": BANKROLL_HARD_FLOOR_USD,
                "bankroll_drawdown_usd": round(BANKROLL_START_USD - bankroll_current, 4),
                "bankroll_floor_blocked": floor_blocked,
                "no_entry_final_seconds": NO_ENTRY_FINAL_SECONDS,
                "min_hold_seconds": MIN_HOLD_SECONDS,
                "exit_confirm_ticks_required": EXIT_CONFIRM_TICKS,
                "side_min_confidence": SIDE_MIN_CONFIDENCE,
                "side_bias": SIDE_BIAS,
                "final_window_blocked": bool(final_window_blocked),
                "harvest_active": harvest_active,
                "total_realized_pnl": round(realized_pnl, 4),
                "high_liquidity": high_liq,
                **forecast,
                **kalshi_api_fields(
                    client,
                    status=kalshi_api_state,
                    error=kalshi_error,
                    market_cache_age_seconds=kalshi_market_cache_age_seconds,
                    orderbook_scan_count=kalshi_orderbook_scan_count,
                ),
            }

            if active:
                active_ticker = active["entry_ticker"]
                active_close_time = active.get("entry_close_time") or market_close_time
                active_seconds_to_close = seconds_to_close(active_close_time, now)
                if active_seconds_to_close is not None and active_seconds_to_close <= 0:
                    active_strike = _as_float(active.get("entry_strike"))
                    if active_strike is None:
                        active_strike = _as_float(parse_strike(active_ticker))
                    exit_px = _settlement_price_for_spot(active.get("side"), spot, active_strike)
                    settlement_status = "spot_settlement"
                    if exit_px is None:
                        exit_px = 0.0
                        settlement_status = "unknown_settlement_assumed_zero"
                    quantity = int(float(active.get("quantity") or 0))
                    entry_price = _as_float(active.get("entry_price"), 0.0) or 0.0
                    proceeds = exit_px * quantity
                    pnl = (exit_px - entry_price) * quantity
                    bankroll_current += proceeds
                    realized_pnl += pnl
                    held = _held_seconds(active)
                    event.update({
                        "action": "SELL",
                        "side": active.get("side"),
                        "active_position": active,
                        "active_ticker": active_ticker,
                        "active_close_time": active_close_time,
                        "active_seconds_to_close": active_seconds_to_close,
                        "exit_reason": "contract_expired",
                        "exit_price": exit_px,
                        "quantity": quantity,
                        "exit_proceeds_usd": round(proceeds, 4),
                        "realized_pnl": round(pnl, 4),
                        "total_realized_pnl": round(realized_pnl, 4),
                        "bankroll_current_usd": round(bankroll_current, 4),
                        "bankroll_drawdown_usd": round(BANKROLL_START_USD - bankroll_current, 4),
                        "settlement_status": settlement_status,
                        "expired_position_reconciled": True,
                    })
                    write_trade_ledger(_completed_trade_record(
                        active,
                        exit_timestamp=now.isoformat(),
                        exit_price=exit_px,
                        exit_spot=spot,
                        exit_reason="contract_expired",
                        exit_seconds_to_close=active_seconds_to_close,
                        held_seconds=held,
                        proceeds=proceeds,
                        pnl=pnl,
                        bankroll_current=bankroll_current,
                        realized_pnl=realized_pnl,
                    ))
                    active = None
                    write_event(event)
                    time.sleep(POLL_SECONDS)
                    continue
                if active_ticker == ticker:
                    active_summary = summary
                else:
                    try:
                        kalshi_orderbook_scan_count += 1
                        active_summary = orderbook_summary(
                            client.orderbook(active_ticker, depth=100)
                        )
                    except Exception as exc:
                        # Treat as stale book; do not flip ticks, just log and continue.
                        write_event({
                            **event,
                            "action": "HOLD",
                            "active_position": active,
                            "active_ticker": active_ticker,
                            "active_book_error": str(exc),
                        })
                        time.sleep(POLL_SECONDS)
                        continue

                active_late_window = (
                    active_seconds_to_close is not None
                    and 0 <= active_seconds_to_close <= LATE_EXIT_SECONDS
                )
                exit_px = close_price(active_summary, active["side"])
                pnl = (
                    (exit_px - active["entry_price"]) * active["quantity"]
                    if exit_px is not None and active["entry_price"] is not None
                    else 0.0
                )
                active["max_unrealized_pnl"] = max(active.get("max_unrealized_pnl", 0.0), pnl)
                active["min_unrealized_pnl"] = min(active.get("min_unrealized_pnl", 0.0), pnl)
                forecast_state = forecast.get("forecast_state")
                forecast_aligned = (
                    (active["side"] == "YES" and forecast_state == FORECAST_RALLY)
                    or (active["side"] == "NO" and forecast_state == FORECAST_DROP)
                )
                if forecast_aligned:
                    active["exit_confirm_ticks"] = 0
                elif forecast_state == FORECAST_WARMING_UP:
                    pass
                else:
                    active["exit_confirm_ticks"] = active.get("exit_confirm_ticks", 0) + 1

                active_held_seconds = _held_seconds(active)
                min_hold_blocks_flip = (
                    active_held_seconds is not None
                    and active_held_seconds < MIN_HOLD_SECONDS
                    and active["exit_confirm_ticks"] >= EXIT_CONFIRM_TICKS
                )
                exit_reason = None
                if not side_book_ok(active_summary, active["side"]):
                    exit_reason = "broken_book"
                    exit_px = exit_px if exit_px is not None else 0.0
                    pnl = (exit_px - (active["entry_price"] or 0.0)) * active["quantity"]
                elif (bankroll_current + pnl) >= BANKROLL_GOAL_USD:
                    exit_reason = "bankroll_goal_locked"
                elif active_late_window:
                    exit_reason = "late_window_sweep"
                elif active["exit_confirm_ticks"] >= EXIT_CONFIRM_TICKS and not min_hold_blocks_flip:
                    exit_reason = "forecast_flipped"

                event.update({
                    "action": "HOLD",
                    "active_position": active,
                    "active_ticker": active_ticker,
                    "active_close_time": active_close_time,
                    "active_seconds_to_close": active_seconds_to_close,
                    "active_late_window": active_late_window,
                    "active_yes_bid": active_summary["yes_bid"],
                    "active_yes_ask": active_summary["yes_ask"],
                    "active_yes_spread": active_summary["yes_spread"],
                    "active_no_bid": active_summary["no_bid"],
                    "active_no_ask": active_summary["no_ask"],
                    "active_no_spread": active_summary["no_spread"],
                    "active_held_seconds": round(active_held_seconds, 2) if active_held_seconds is not None else None,
                    "active_forecast_aligned": bool(forecast_aligned),
                    "exit_confirm_ticks": active["exit_confirm_ticks"],
                    "min_hold_blocks_flip": bool(min_hold_blocks_flip),
                    "unrealized_pnl": round(pnl, 4),
                })

                if exit_reason is not None and exit_px is not None:
                    proceeds = exit_px * active["quantity"]
                    bankroll_current += proceeds
                    realized_pnl += pnl
                    event.update({
                        "action": "SELL",
                        "side": active["side"],
                        "exit_reason": exit_reason,
                        "exit_price": exit_px,
                        "quantity": active["quantity"],
                        "exit_proceeds_usd": round(proceeds, 4),
                        "realized_pnl": round(pnl, 4),
                        "total_realized_pnl": round(realized_pnl, 4),
                        "bankroll_current_usd": round(bankroll_current, 4),
                        "bankroll_drawdown_usd": round(BANKROLL_START_USD - bankroll_current, 4),
                        "harvest_active": bankroll_current >= BANKROLL_GOAL_USD,
                    })
                    print(
                        color(
                            "\n".join((
                                "========== BANKROLL PAPER SELL ==========",
                                f"side={active['side']} ticker={active_ticker}",
                                f"exit_price={exit_px} qty={active['quantity']} "
                                f"pnl={pnl:.2f} bankroll={bankroll_current:.2f}",
                                f"reason={exit_reason}",
                                "==========================================",
                            )),
                            "green" if pnl >= 0 else "red",
                        ),
                        flush=True,
                    )
                    held_seconds = round(time.time() - active["entry_epoch"], 2)
                    entry_notional = active.get("entry_notional") or 0.0
                    return_pct = (
                        round((pnl / entry_notional) * 100.0, 4)
                        if entry_notional else None
                    )
                    write_trade_ledger({
                        "trade_id": active.get("trade_id"),
                        "mode": "kalshi_bankroll_paper",
                        "engine_name": "kalshi_bankroll_engine",
                        "side": active["side"],
                        "ticker": active_ticker,
                        "quantity": active["quantity"],
                        "entry_timestamp": active.get("entry_timestamp"),
                        "entry_price": active.get("entry_price"),
                        "entry_notional": round(entry_notional, 4),
                        "entry_spot": active.get("entry_spot"),
                        "entry_strike": active.get("entry_strike"),
                        "entry_seconds_to_close": active.get("entry_seconds_to_close"),
                        "entry_forecast_state": active.get("entry_forecast_state"),
                        "entry_forecast_confidence": active.get("entry_forecast_confidence"),
                        "entry_forecast_projected_30m": active.get("entry_forecast_projected_30m"),
                        "entry_forecast_projected_60m": active.get("entry_forecast_projected_60m"),
                        "entry_min_hold_seconds": active.get("entry_min_hold_seconds"),
                        "entry_exit_confirm_ticks": active.get("entry_exit_confirm_ticks"),
                        "entry_side_min_confidence": active.get("entry_side_min_confidence"),
                        "entry_side_bias": active.get("entry_side_bias"),
                        "exit_timestamp": now.isoformat(),
                        "exit_price": exit_px,
                        "exit_spot": spot,
                        "exit_proceeds_usd": round(proceeds, 4),
                        "exit_reason": exit_reason,
                        "exit_seconds_to_close": active_seconds_to_close,
                        "held_seconds": held_seconds,
                        "realized_pnl": round(pnl, 4),
                        "return_pct": return_pct,
                        "max_unrealized_pnl": round(active.get("max_unrealized_pnl", 0.0), 4),
                        "min_unrealized_pnl": round(active.get("min_unrealized_pnl", 0.0), 4),
                        "win": bool(pnl > 0),
                        "bankroll_after_usd": round(bankroll_current, 4),
                        "total_realized_pnl": round(realized_pnl, 4),
                        "restored_from_journal": bool(active.get("restored_from_journal")),
                    })
                    active = None
            else:
                forecast_state = forecast.get("forecast_state")
                forecast_confidence = float(forecast.get("forecast_confidence") or 0.0)
                candidate_side = _candidate_for_state(forecast_state)
                contrarian_side = _contrarian_for_state(forecast_state)
                side_required_confidence = _side_required_confidence(candidate_side)
                counter_side_eligible = bool(
                    ALLOW_COUNTER_LIQUIDITY and contrarian_side and high_liq["ok"]
                )
                requires_high_liq = False
                block_reason = None

                if harvest_active:
                    block_reason = "harvest_active"
                elif floor_blocked:
                    block_reason = "bankroll_floor_blocked"
                elif not fresh_spot:
                    block_reason = "stale_spot"
                elif not spread_is_ok or not depth_is_ok:
                    block_reason = "book_not_clean"
                elif forecast_state == FORECAST_WARMING_UP:
                    block_reason = "forecast_warming_up"
                elif forecast_state == FORECAST_FLAT:
                    if not ALLOW_FLAT_ENTRIES:
                        block_reason = "forecast_flat"
                    else:
                        block_reason = "forecast_flat_no_side"
                elif candidate_side is None:
                    block_reason = "no_candidate_side"
                elif forecast_confidence < side_required_confidence:
                    block_reason = "forecast_low_side_confidence"
                elif candidate_side in (_MODEL_CONFIG_STATE.get("disable_sides") or []):
                    block_reason = "model_config_side_disabled"
                elif not side_book_ok(summary, candidate_side):
                    block_reason = "side_book_unavailable"
                elif (
                    market_seconds_to_close is not None
                    and market_seconds_to_close <= NO_ENTRY_FINAL_SECONDS
                ):
                    block_reason = "inside_final_window_no_new_entries"

                # If we ever choose to take the contrarian side (off by default),
                # require the strict high-liquidity gate.
                if (
                    block_reason is None
                    and ALLOW_COUNTER_LIQUIDITY
                    and contrarian_side is not None
                    and counter_side_eligible
                    and os.getenv("KALSHI_BANKROLL_FORCE_COUNTER", "false").strip().lower()
                    in {"1", "true", "yes", "on"}
                ):
                    candidate_side = contrarian_side
                    requires_high_liq = True
                    side_required_confidence = _side_required_confidence(candidate_side)
                    if forecast_confidence < side_required_confidence:
                        block_reason = "forecast_low_side_confidence"

                entry_price = side_price(summary, candidate_side) if candidate_side else None
                if block_reason is None:
                    sizing = compute_sizing(bankroll_current, entry_price)
                else:
                    sizing = {
                        "target_notional": round(
                            max(0.0, bankroll_current) * BANKROLL_TRADE_FRACTION, 4
                        ),
                        "notional": 0.0,
                        "quantity": 0,
                        "block_reason": block_reason,
                    }
                if sizing.get("block_reason") and block_reason is None:
                    block_reason = sizing["block_reason"]
                if (
                    block_reason is None
                    and sizing["quantity"] > 0
                    and sizing["notional"] > bankroll_current
                ):
                    block_reason = "insufficient_bankroll"

                event["high_liquidity_required"] = requires_high_liq
                event["candidate_min_confidence"] = side_required_confidence

                if block_reason is None and candidate_side and sizing["quantity"] > 0:
                    cost = sizing["notional"]
                    bankroll_current -= cost
                    trigger_ts = time.time()
                    if EXECUTION_DELAY_SECONDS > 0:
                        time.sleep(EXECUTION_DELAY_SECONDS)
                    execution_delay_ms = int((time.time() - trigger_ts) * 1000)
                    active = {
                        "trade_id": _next_trade_id(),
                        "side": candidate_side,
                        "entry_price": entry_price,
                        "entry_notional": cost,
                        "quantity": sizing["quantity"],
                        "entry_timestamp": now.isoformat(),
                        "entry_epoch": time.time(),
                        "entry_ticker": ticker,
                        "entry_close_time": market_close_time,
                        "entry_spot": spot,
                        "entry_strike": strike,
                        "entry_seconds_to_close": market_seconds_to_close,
                        "entry_forecast_state": forecast_state,
                        "entry_forecast_confidence": forecast_confidence,
                        "entry_forecast_projected_30m": forecast.get("projected_30m"),
                        "entry_forecast_projected_60m": forecast.get("projected_60m"),
                        "entry_bankroll_before_usd": round(bankroll_current + cost, 4),
                        "entry_required_high_liquidity": requires_high_liq,
                        "entry_min_hold_seconds": MIN_HOLD_SECONDS,
                        "entry_exit_confirm_ticks": EXIT_CONFIRM_TICKS,
                        "entry_side_min_confidence": side_required_confidence,
                        "entry_side_bias": SIDE_BIAS,
                        "max_unrealized_pnl": 0.0,
                        "min_unrealized_pnl": 0.0,
                        "exit_confirm_ticks": 0,
                    }
                    event.update({
                        "action": "BUY",
                        "side": candidate_side,
                        "side_intent": candidate_side,
                        "entry_price": entry_price,
                        "quantity": sizing["quantity"],
                        "entry_notional": cost,
                        "target_notional": sizing["target_notional"],
                        "bankroll_current_usd": round(bankroll_current, 4),
                        "bankroll_drawdown_usd": round(BANKROLL_START_USD - bankroll_current, 4),
                        "counter_side_eligible": counter_side_eligible,
                        "candidate_min_confidence": side_required_confidence,
                        "execution_delay_ms": execution_delay_ms,
                    })
                    print(
                        color(
                            "\n".join((
                                "========== BANKROLL PAPER BUY ==========",
                                f"side={candidate_side} ticker={ticker}",
                                f"entry_price={entry_price} qty={sizing['quantity']} "
                                f"notional={cost:.2f}",
                                f"forecast={forecast_state} confidence={forecast_confidence:.2f}",
                                f"bankroll={bankroll_current:.2f}/{BANKROLL_GOAL_USD:.2f}",
                                "========================================",
                            )),
                            "green" if candidate_side == "YES" else "red",
                        ),
                        flush=True,
                    )
                else:
                    event.update({
                        "action": "OBSERVE",
                        "side_intent": candidate_side,
                        "block_reason": block_reason,
                        "target_notional": sizing["target_notional"],
                        "candidate_entry_price": entry_price,
                        "candidate_notional": sizing["notional"],
                        "candidate_quantity": sizing["quantity"],
                        "candidate_min_confidence": side_required_confidence,
                        "counter_side_eligible": counter_side_eligible,
                    })
                    proj30m = forecast.get("projected_30m") or 0.0
                    print(
                        color("[KALSHI-BANKROLL] OBSERVE", "cyan")
                        + f" {ticker} spot={spot:.2f} "
                        + f"forecast={forecast_state} side={candidate_side or 'none'} "
                        + f"proj30m={proj30m:+.1f} conf={forecast_confidence:.2f} "
                        + f"bank={bankroll_current:.2f}/{BANKROLL_GOAL_USD:.2f} "
                        + f"block={block_reason}",
                        flush=True,
                    )

            event.update(kalshi_api_fields(
                client,
                status=kalshi_api_state,
                error=kalshi_error,
                market_cache_age_seconds=kalshi_market_cache_age_seconds,
                orderbook_scan_count=kalshi_orderbook_scan_count,
            ))
            write_event(event)
        except Exception as exc:
            print(f"[KALSHI-BANKROLL ERROR] {exc}", flush=True)
            write_event({
                "timestamp": now.isoformat(),
                "mode": "kalshi_bankroll_paper",
                "error": str(exc),
                "bankroll_current_usd": round(bankroll_current, 4),
            })
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    run()
