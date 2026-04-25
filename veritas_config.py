# veritas_config.py
# Sector-specific weighting logic for Healy Vector Labs.

VERITAS_SECTOR_CONFIG = {
    "AUTOMOTIVE": {
        "primary_gate": "insider",
        "threshold": 0.40,
        "weights": {
            "insider": 0.50,        # SEC Form 4 data
            "unit_velocity": 0.35,  # Physical production
            "sentiment": 0.15       # Market hype
        }
    },
    "TECH": {
        "primary_gate": "insider",
        "threshold": 0.30,         # Tech insiders often sell for tax reasons; lower threshold
        "weights": {
            "insider": 0.40,        # Key, but less so than heavy industry
            "unit_velocity": 0.30,  # Map this to User Growth/Downloads
            "sentiment": 0.30       # Hype matters more in Tech (Speculation)
        }
    },
    "ENERGY": {
        "primary_gate": "unit_velocity",
        "threshold": 0.50,
        "weights": {
            "insider": 0.30,
            "unit_velocity": 0.60,
            "sentiment": 0.10
        }
    }
}
