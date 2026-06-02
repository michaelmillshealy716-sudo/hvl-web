"""Kalshi bankroll trainer.

This is the searchable machine-learning entrypoint for the conservative
Kalshi bankroll trainer. It emits the bounded config consumed by
``hvl.kalshi.kalshi_bankroll_engine``:

    data/private/kalshi_training/bankroll_model_config.json

The implementation currently lives behind the stable Kalshi module path so
existing launchd/terminal commands keep working during this reorganization.
Future trainer variants should live in this package.
"""
from __future__ import annotations

from hvl.kalshi.kalshi_bankroll_trainer import (
    BOUNDS,
    CONFIG_SCHEMA_VERSION,
    DEFAULT_CONFIG_PATH,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REPORT_PATH,
    DEFAULTS,
    FEATURE_SCHEMA_VERSION,
    SIDE_MIN_CONFIDENCE_DEFAULTS,
    TRAINER_VERSION,
    build_report,
    discover_source_files,
    main,
    normalize_trades,
    parse_args,
    recommend_config,
    run_training,
)

__all__ = [
    "BOUNDS",
    "CONFIG_SCHEMA_VERSION",
    "DEFAULT_CONFIG_PATH",
    "DEFAULT_OUTPUT_DIR",
    "DEFAULT_REPORT_PATH",
    "DEFAULTS",
    "FEATURE_SCHEMA_VERSION",
    "SIDE_MIN_CONFIDENCE_DEFAULTS",
    "TRAINER_VERSION",
    "build_report",
    "discover_source_files",
    "main",
    "normalize_trades",
    "parse_args",
    "recommend_config",
    "run_training",
]


if __name__ == "__main__":
    main()
