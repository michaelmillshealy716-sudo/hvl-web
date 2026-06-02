"""Conservative offline trainer for the Kalshi bankroll paper engine.

The trainer never places orders and never edits engine code. It reads historical
JSONL journals, writes a report, and emits a small bounded config file consumed
by ``hvl.kalshi.kalshi_bankroll_engine``.
"""
from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from hvl.utils.paths import PRIVATE_DATA_DIR, PRIVATE_JOURNAL_DIR, REPO_ROOT


TRAINER_VERSION = "conservative_rules_v1"
CONFIG_SCHEMA_VERSION = 1
FEATURE_SCHEMA_VERSION = 1

DEFAULT_OUTPUT_DIR = PRIVATE_DATA_DIR / "kalshi_training"
DEFAULT_REPORT_PATH = DEFAULT_OUTPUT_DIR / "training_report.json"
DEFAULT_CONFIG_PATH = DEFAULT_OUTPUT_DIR / "bankroll_model_config.json"

DEFAULTS = {
    "min_confidence": 0.60,
    "drop_threshold_usd": -500.0,
    "rally_threshold_usd": 500.0,
    "no_entry_final_seconds": 900.0,
    "min_hold_seconds": 0.0,
    "exit_confirm_ticks": 3.0,
    "max_trade_usd": 25.0,
    "trade_fraction": 0.20,
}

SIDE_MIN_CONFIDENCE_DEFAULTS = {
    "YES": 0.60,
    "NO": 0.60,
}

BOUNDS = {
    "min_confidence": [0.55, 0.95],
    "drop_threshold_usd": [-600.0, -400.0],
    "rally_threshold_usd": [400.0, 600.0],
    "no_entry_final_seconds": [900.0, 3600.0],
    "min_hold_seconds": [0.0, 300.0],
    "exit_confirm_ticks": [1.0, 6.0],
    "side_min_confidence": [0.55, 0.95],
    "max_trade_usd": [10.0, 25.0],
    "trade_fraction": [0.05, 0.20],
}

CONFIDENCE_BUCKETS = [
    (0.0, 0.60, "<0.60"),
    (0.60, 0.70, "0.60-0.70"),
    (0.70, 0.80, "0.70-0.80"),
    (0.80, 0.90, "0.80-0.90"),
    (0.90, 1.01, ">=0.90"),
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _as_float(value, default: Optional[float] = None) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value, default: Optional[int] = None) -> Optional[int]:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _timestamp_epoch(value) -> Optional[float]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return rows
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _unique_paths(paths: Iterable[Path]) -> list[Path]:
    seen = set()
    unique = []
    for path in paths:
        try:
            key = path.resolve()
        except OSError:
            key = path
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique


def _history_roots(extra_roots: Iterable[Path] = ()) -> list[Path]:
    env_roots = [
        Path(chunk).expanduser()
        for chunk in os.getenv("KALSHI_BANKROLL_HISTORY_ROOTS", "").split(os.pathsep)
        if chunk.strip()
    ]
    roots = [
        *extra_roots,
        *env_roots,
        Path.home() / "hvl_complete_runtime",
        REPO_ROOT,
    ]
    return _unique_paths(root for root in roots if root.exists())


def discover_source_files(extra_roots: Iterable[Path] = ()) -> list[Path]:
    candidates: list[Path] = []
    for root in _history_roots(extra_roots):
        candidates.extend((root / "data" / "private" / "journals").glob("*kalshi*.jsonl"))
        candidates.extend(root.glob("*kalshi*.jsonl"))
    candidates.extend(PRIVATE_JOURNAL_DIR.glob("*kalshi*.jsonl"))
    candidates.extend(REPO_ROOT.glob("*kalshi*.jsonl"))
    return sorted(_unique_paths(candidates), key=lambda path: str(path))


def _confidence_bucket(value) -> str:
    confidence = _as_float(value)
    if confidence is None:
        return "unknown"
    for low, high, label in CONFIDENCE_BUCKETS:
        if low <= confidence < high:
            return label
    return "unknown"


def _seconds_bucket(value) -> str:
    seconds = _as_float(value)
    if seconds is None:
        return "unknown"
    if seconds < 900:
        return "<15m"
    if seconds < 3600:
        return "15m-1h"
    if seconds < 14400:
        return "1h-4h"
    return ">=4h"


def _hold_time_bucket(value) -> str:
    seconds = _as_float(value)
    if seconds is None:
        return "unknown"
    if seconds < 120:
        return "<2m"
    if seconds < 300:
        return "2m-5m"
    if seconds < 900:
        return "5m-15m"
    if seconds < 3600:
        return "15m-1h"
    return ">=1h"


def _entry_price_bucket(value) -> str:
    price = _as_float(value)
    if price is None:
        return "unknown"
    if price < 0.30:
        return "<0.30"
    if price < 0.50:
        return "0.30-0.50"
    if price < 0.70:
        return "0.50-0.70"
    return ">=0.70"


def _trade_from_ledger_row(row: dict, source_file: Path) -> Optional[dict]:
    pnl = _as_float(row.get("realized_pnl"))
    entry_price = _as_float(row.get("entry_price"))
    exit_price = _as_float(row.get("exit_price"))
    quantity = _as_int(row.get("quantity"))
    if pnl is None or entry_price is None or exit_price is None or not quantity:
        return None
    entry_spot = _as_float(row.get("entry_spot"))
    entry_strike = _as_float(row.get("entry_strike"))
    return {
        "source_type": "ledger",
        "source_file": str(source_file),
        "mode": row.get("mode"),
        "engine_name": row.get("engine_name"),
        "side": row.get("side"),
        "ticker": row.get("ticker"),
        "quantity": quantity,
        "entry_timestamp": row.get("entry_timestamp"),
        "entry_price": entry_price,
        "entry_notional": _as_float(row.get("entry_notional"), entry_price * quantity),
        "entry_seconds_to_close": _as_float(row.get("entry_seconds_to_close")),
        "entry_forecast_state": row.get("entry_forecast_state"),
        "entry_forecast_confidence": _as_float(row.get("entry_forecast_confidence")),
        "entry_forecast_projected_30m": _as_float(row.get("entry_forecast_projected_30m")),
        "entry_forecast_projected_60m": _as_float(row.get("entry_forecast_projected_60m")),
        "entry_spot": entry_spot,
        "entry_strike": entry_strike,
        "spot_strike_distance": (
            round(entry_spot - entry_strike, 4)
            if entry_spot is not None and entry_strike is not None
            else None
        ),
        "exit_timestamp": row.get("exit_timestamp"),
        "exit_price": exit_price,
        "exit_reason": row.get("exit_reason"),
        "exit_seconds_to_close": _as_float(row.get("exit_seconds_to_close")),
        "held_seconds": _as_float(row.get("held_seconds")),
        "realized_pnl": pnl,
        "return_pct": _as_float(row.get("return_pct")),
        "win": bool(pnl > 0),
    }


def _trade_from_pair(entry: dict, exit_row: dict, source_file: Path) -> Optional[dict]:
    quantity = _as_int(exit_row.get("quantity"), _as_int(entry.get("quantity")))
    entry_price = _as_float(entry.get("entry_price"))
    exit_price = _as_float(exit_row.get("exit_price"))
    if not quantity or entry_price is None or exit_price is None:
        return None
    pnl = _as_float(exit_row.get("realized_pnl"))
    if pnl is None:
        pnl = (exit_price - entry_price) * quantity
    entry_ts = entry.get("timestamp") or entry.get("entry_timestamp")
    exit_ts = exit_row.get("timestamp") or exit_row.get("exit_timestamp")
    held = _as_float(exit_row.get("held_seconds"))
    if held is None:
        entry_epoch = _timestamp_epoch(entry_ts)
        exit_epoch = _timestamp_epoch(exit_ts)
        held = max(0.0, exit_epoch - entry_epoch) if entry_epoch and exit_epoch else None
    entry_spot = _as_float(entry.get("spot") or entry.get("entry_spot"))
    entry_strike = _as_float(entry.get("strike") or entry.get("entry_strike"))
    entry_notional = _as_float(entry.get("entry_notional"), entry_price * quantity)
    return_pct = round((pnl / entry_notional) * 100.0, 4) if entry_notional else None
    return {
        "source_type": "paired_journal",
        "source_file": str(source_file),
        "mode": exit_row.get("mode") or entry.get("mode"),
        "engine_name": exit_row.get("engine_name") or entry.get("engine_name"),
        "side": exit_row.get("side") or entry.get("side"),
        "ticker": entry.get("ticker") or entry.get("active_ticker"),
        "quantity": quantity,
        "entry_timestamp": entry_ts,
        "entry_price": entry_price,
        "entry_notional": entry_notional,
        "entry_seconds_to_close": _as_float(entry.get("seconds_to_close") or entry.get("entry_seconds_to_close")),
        "entry_forecast_state": entry.get("forecast_state") or entry.get("entry_forecast_state"),
        "entry_forecast_confidence": _as_float(entry.get("forecast_confidence") or entry.get("entry_forecast_confidence")),
        "entry_forecast_projected_30m": _as_float(entry.get("projected_30m") or entry.get("entry_forecast_projected_30m")),
        "entry_forecast_projected_60m": _as_float(entry.get("projected_60m") or entry.get("entry_forecast_projected_60m")),
        "entry_spot": entry_spot,
        "entry_strike": entry_strike,
        "spot_strike_distance": (
            round(entry_spot - entry_strike, 4)
            if entry_spot is not None and entry_strike is not None
            else None
        ),
        "exit_timestamp": exit_ts,
        "exit_price": exit_price,
        "exit_reason": exit_row.get("exit_reason"),
        "exit_seconds_to_close": _as_float(exit_row.get("seconds_to_close") or exit_row.get("exit_seconds_to_close")),
        "held_seconds": held,
        "realized_pnl": pnl,
        "return_pct": return_pct,
        "win": bool(pnl > 0),
    }


def _normalize_paired_trades(rows: list[dict], source_file: Path) -> list[dict]:
    trades: list[dict] = []
    open_positions: dict[tuple[str, str], dict] = {}
    fallback_position: Optional[dict] = None
    for row in rows:
        action = row.get("action")
        if action == "BUY":
            key = (str(row.get("ticker") or row.get("active_ticker")), str(row.get("side")))
            open_positions[key] = row
            fallback_position = row
            continue
        if action != "SELL":
            continue
        key = (str(row.get("ticker") or row.get("active_ticker")), str(row.get("side")))
        entry = open_positions.pop(key, None)
        if entry is None and fallback_position is not None:
            entry = fallback_position
            fallback_position = None
        if entry is None:
            continue
        trade = _trade_from_pair(entry, row, source_file)
        if trade:
            trades.append(trade)
    return trades


def normalize_trades(source_files: Iterable[Path]) -> tuple[list[dict], dict]:
    trades: list[dict] = []
    source_stats = {}
    seen_fingerprints = set()
    for path in source_files:
        rows = _read_jsonl(path)
        ledger_trades = [_trade_from_ledger_row(row, path) for row in rows]
        ledger_trades = [trade for trade in ledger_trades if trade]
        paired_trades = _normalize_paired_trades(rows, path)
        selected = ledger_trades if ledger_trades else paired_trades
        added = 0
        for trade in selected:
            fingerprint = (
                trade.get("source_type"),
                trade.get("ticker"),
                trade.get("side"),
                trade.get("entry_timestamp"),
                trade.get("exit_timestamp"),
                trade.get("quantity"),
                trade.get("realized_pnl"),
            )
            if fingerprint in seen_fingerprints:
                continue
            seen_fingerprints.add(fingerprint)
            trades.append(trade)
            added += 1
        source_stats[str(path)] = {
            "rows": len(rows),
            "ledger_trades": len(ledger_trades),
            "paired_trades": len(paired_trades),
            "selected_trades": added,
        }
    return trades, source_stats


def _stats(rows: list[dict]) -> dict:
    if not rows:
        return {"count": 0, "wins": 0, "losses": 0, "win_rate": None, "realized_pnl": 0.0, "avg_pnl": None}
    pnls = [_as_float(row.get("realized_pnl"), 0.0) or 0.0 for row in rows]
    wins = sum(1 for pnl in pnls if pnl > 0)
    total = sum(pnls)
    return {
        "count": len(rows),
        "wins": wins,
        "losses": len(rows) - wins,
        "win_rate": round(wins / len(rows), 4),
        "realized_pnl": round(total, 4),
        "avg_pnl": round(total / len(rows), 4),
    }


def _group_stats(trades: list[dict], key_func) -> dict:
    groups: dict[str, list[dict]] = defaultdict(list)
    for trade in trades:
        groups[str(key_func(trade) or "unknown")].append(trade)
    return {key: _stats(rows) for key, rows in sorted(groups.items())}


def _side_forecast_key(row: dict) -> str:
    side = row.get("side") or "unknown"
    state = row.get("entry_forecast_state") or "unknown"
    return f"{side}:{state}"


def _engine_mode_key(row: dict) -> str:
    engine = row.get("engine_name") or "unknown_engine"
    mode = row.get("mode") or row.get("source_type") or "unknown_mode"
    return f"{engine}:{mode}"


def build_report(trades: list[dict], source_stats: dict) -> dict:
    losing_groups: dict[tuple[str, str, str, str, str], list[dict]] = defaultdict(list)
    for trade in trades:
        if (_as_float(trade.get("realized_pnl"), 0.0) or 0.0) >= 0:
            continue
        key = (
            str(trade.get("side") or "unknown"),
            str(trade.get("entry_forecast_state") or "unknown"),
            _confidence_bucket(trade.get("entry_forecast_confidence")),
            _seconds_bucket(trade.get("entry_seconds_to_close")),
            _entry_price_bucket(trade.get("entry_price")),
        )
        losing_groups[key].append(trade)

    common_losers = []
    for key, rows in losing_groups.items():
        side, state, confidence, seconds, price = key
        stats = _stats(rows)
        common_losers.append({
            "side": side,
            "forecast_state": state,
            "confidence_bucket": confidence,
            "seconds_to_close_bucket": seconds,
            "entry_price_bucket": price,
            **stats,
        })
    common_losers.sort(key=lambda row: (row["realized_pnl"], -row["count"]))

    return {
        "schema_version": CONFIG_SCHEMA_VERSION,
        "trainer_version": TRAINER_VERSION,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source_stats": source_stats,
        "summary": _stats(trades),
        "pnl_by_engine_mode": _group_stats(trades, _engine_mode_key),
        "pnl_by_source_file": _group_stats(trades, lambda row: row.get("source_file")),
        "pnl_by_exit_reason": _group_stats(trades, lambda row: row.get("exit_reason")),
        "pnl_by_hold_time_bucket": _group_stats(trades, lambda row: _hold_time_bucket(row.get("held_seconds"))),
        "pnl_by_side": _group_stats(trades, lambda row: row.get("side")),
        "pnl_by_side_forecast_state": _group_stats(trades, _side_forecast_key),
        "pnl_by_forecast_state": _group_stats(trades, lambda row: row.get("entry_forecast_state")),
        "pnl_by_confidence_bucket": _group_stats(trades, lambda row: _confidence_bucket(row.get("entry_forecast_confidence"))),
        "pnl_by_seconds_to_close_bucket": _group_stats(trades, lambda row: _seconds_bucket(row.get("entry_seconds_to_close"))),
        "pnl_by_entry_price_bucket": _group_stats(trades, lambda row: _entry_price_bucket(row.get("entry_price"))),
        "common_losing_structures": common_losers[:12],
    }


def _bounded(name: str, value: float) -> float:
    low, high = BOUNDS[name]
    return min(high, max(low, float(value)))


def _bounded_side_min_confidence(values: dict) -> dict:
    low, high = BOUNDS["side_min_confidence"]
    bounded = {}
    for side in ("YES", "NO"):
        value = _as_float(values.get(side), SIDE_MIN_CONFIDENCE_DEFAULTS[side])
        bounded[side] = min(high, max(low, float(value)))
    return bounded


def _stats_underperformed(stats: dict, min_count: int = 3, max_win_rate: float = 0.45) -> bool:
    return (
        stats.get("count", 0) >= min_count
        and stats.get("realized_pnl", 0.0) < 0
        and (stats.get("win_rate") or 0.0) < max_win_rate
    )


def recommend_config(report: dict, source_files: list[Path], min_completed_trades: int) -> dict:
    summary = report["summary"]
    total = summary["count"]
    win_rate = summary["win_rate"] or 0.0
    total_pnl = summary["realized_pnl"]
    recommendations = []
    params = dict(DEFAULTS)
    side_min_confidence = dict(SIDE_MIN_CONFIDENCE_DEFAULTS)
    side_bias = {
        "preferred_side": None,
        "penalized_side": None,
        "confidence_adjustments": {},
        "reason": None,
    }

    promoted = total >= min_completed_trades
    confidence = "low"
    reason = f"Only {total} completed trades; keeping conservative defaults."

    if promoted:
        confidence = "medium" if total < 100 else "high"
        reason = "Conservative rules trained from completed Kalshi paper trades."
        if total_pnl < 0 or win_rate < 0.45:
            params["trade_fraction"] = 0.10
            params["max_trade_usd"] = 15.0
            params["drop_threshold_usd"] = -550.0
            params["rally_threshold_usd"] = 550.0
            recommendations.append("Reduce sizing and require larger projected moves after negative realized P/L.")
        elif total_pnl > 0 and win_rate >= 0.55:
            params["trade_fraction"] = 0.15
            recommendations.append("Keep sizing below the manual maximum despite positive historical P/L.")

        confidence_stats = report["pnl_by_confidence_bucket"]
        low_conf = confidence_stats.get("0.60-0.70") or {}
        if low_conf.get("count", 0) >= 3 and low_conf.get("realized_pnl", 0.0) < 0:
            params["min_confidence"] = 0.75
            recommendations.append("Raise minimum confidence because lower-confidence entries lost money.")

        final_window = report["pnl_by_seconds_to_close_bucket"].get("<15m") or {}
        if final_window.get("count", 0) >= 2 and final_window.get("realized_pnl", 0.0) < 0:
            params["no_entry_final_seconds"] = 1800.0
            recommendations.append("Widen final no-entry window because sub-15m entries underperformed.")

        short_holds = report["pnl_by_hold_time_bucket"].get("<2m") or {}
        if short_holds.get("count", 0) >= 2 and short_holds.get("realized_pnl", 0.0) < 0:
            params["min_hold_seconds"] = 120.0
            params["exit_confirm_ticks"] = max(params["exit_confirm_ticks"], 4.0)
            recommendations.append("Require a short minimum hold and extra exit confirmation because rapid flips lost money.")

        flipped_exits = report["pnl_by_exit_reason"].get("forecast_flipped") or {}
        if flipped_exits.get("count", 0) >= 2 and flipped_exits.get("realized_pnl", 0.0) < 0:
            params["exit_confirm_ticks"] = max(params["exit_confirm_ticks"], 5.0)
            recommendations.append("Slow forecast-flip exits because historical flip exits underperformed.")

        side_stats = report["pnl_by_side"]
        side_forecast_stats = report["pnl_by_side_forecast_state"]
        yes_stats = side_stats.get("YES") or {}
        no_stats = side_stats.get("NO") or {}
        yes_rally_stats = side_forecast_stats.get("YES:FORECAST_RALLY") or {}
        no_drop_stats = side_forecast_stats.get("NO:FORECAST_DROP") or {}

        if _stats_underperformed(yes_stats) or _stats_underperformed(yes_rally_stats, min_count=2):
            side_min_confidence["YES"] = 0.85
            side_bias["penalized_side"] = "YES"
            side_bias["confidence_adjustments"]["YES"] = 0.10
            recommendations.append("Penalize YES entries with a higher side-specific confidence gate.")

        if (
            no_stats.get("count", 0) >= 3
            and no_stats.get("realized_pnl", 0.0) > 0
            and no_drop_stats.get("realized_pnl", 0.0) >= 0
        ):
            side_min_confidence["NO"] = max(side_min_confidence["NO"], 0.75)
            side_bias["preferred_side"] = "NO"
            recommendations.append("Prefer NO/drop setups by keeping their gate conservative but below weak YES setups.")

        if side_bias["preferred_side"] or side_bias["penalized_side"]:
            side_bias["reason"] = "Historical side and side/forecast condition P/L favored stricter biased confidence gates."

    bounded_params = {name: _bounded(name, value) for name, value in params.items()}
    bounded_params["side_min_confidence"] = _bounded_side_min_confidence(side_min_confidence)
    bounded_params["side_bias"] = side_bias
    config_version = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    config = {
        "schema_version": CONFIG_SCHEMA_VERSION,
        "model_family": "kalshi_bankroll_conservative_rules",
        "model_version": TRAINER_VERSION,
        "model_config_version": config_version,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "trained_at": _utc_now(),
        "promoted": promoted,
        "sample_count": total,
        "min_completed_trades": min_completed_trades,
        "source_files": [str(path) for path in source_files],
        "confidence": confidence,
        "reason": reason,
        "recommendations": recommendations,
        "bounds": BOUNDS,
        "parameters": bounded_params,
        **bounded_params,
    }
    return config


def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(path)


def run_training(
    *,
    history_roots: Iterable[Path] = (),
    report_path: Path = DEFAULT_REPORT_PATH,
    config_path: Path = DEFAULT_CONFIG_PATH,
    dry_run: bool = False,
    min_completed_trades: int = 20,
) -> dict:
    source_files = discover_source_files(history_roots)
    trades, source_stats = normalize_trades(source_files)
    report = build_report(trades, source_stats)
    config = recommend_config(report, source_files, min_completed_trades)
    report["recommended_parameter_changes"] = config["parameters"]
    report["config_path"] = str(config_path)
    report["config_promoted"] = config["promoted"]
    _atomic_write_json(report_path, report)
    if not dry_run:
        _atomic_write_json(config_path, config)
    return {
        "dry_run": dry_run,
        "report_path": str(report_path),
        "config_path": str(config_path),
        "config_written": not dry_run,
        "trade_count": report["summary"]["count"],
        "config": config,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a bounded Kalshi bankroll model config from historical JSONL.")
    parser.add_argument("--history-root", action="append", default=[], help="Additional root containing Kalshi JSONL history.")
    parser.add_argument("--report-path", type=Path, default=Path(os.getenv("KALSHI_BANKROLL_TRAINING_REPORT_PATH", DEFAULT_REPORT_PATH)))
    parser.add_argument("--config-path", type=Path, default=Path(os.getenv("KALSHI_BANKROLL_MODEL_CONFIG_PATH", DEFAULT_CONFIG_PATH)))
    parser.add_argument("--dry-run", action="store_true", help="Write the report but do not promote/write the live config.")
    parser.add_argument(
        "--min-completed-trades",
        type=int,
        default=int(float(os.getenv("KALSHI_BANKROLL_MIN_COMPLETED_TRADES", "20"))),
        help="Minimum completed trades required before promoting non-default recommendations.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_training(
        history_roots=[Path(root).expanduser() for root in args.history_root],
        report_path=args.report_path.expanduser(),
        config_path=args.config_path.expanduser(),
        dry_run=args.dry_run,
        min_completed_trades=args.min_completed_trades,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
