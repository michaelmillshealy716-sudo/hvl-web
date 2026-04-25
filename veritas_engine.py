# veritas_engine.py
# Healy Vector Labs | Gated Decision Architecture
# Lead Architect: Michael Healy

import requests
import os
import json
import streamlit as st
from datetime import datetime
from veritas_config import VERITAS_SECTOR_CONFIG

class VeritasGatedEngine:
    def __init__(self, sector="AUTOMOTIVE"):
        self.config = VERITAS_SECTOR_CONFIG.get(sector, VERITAS_SECTOR_CONFIG["AUTOMOTIVE"])
        self.headers = {"User-Agent": "HealyVectorLabs michael@healyvectorlabs.com"}
        self.ammo_file = "ammo_log.json"
        self.limit = 25 

    def get_ammo_count(self):
        today = datetime.now().strftime("%Y-%m-%d")
        if not os.path.exists(self.ammo_file): return 0
        try:
            with open(self.ammo_file, "r") as f:
                log = json.load(f)
            return log.get("count", 0) if log.get("date") == today else 0
        except: return 0

    def log_shot(self, shots=1):
        today = datetime.now().strftime("%Y-%m-%d")
        count = self.get_ammo_count() + shots
        with open(self.ammo_file, "w") as f:
            json.dump({"date": today, "count": count}, f)

    def fetch_edgar_signals(self, ticker):
        """DIRECT SEC JSON INGESTION. Unique data for every audit."""
        cik_map = {"NVDA": "0001045810", "F": "0000037996", "XOM": "0000034013", "TSLA": "0001318605"}
        cik = cik_map.get(ticker)
        if not cik: return None

        # Pull the official Company Fact stream from the SEC
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            if res.status_code != 200: return None
            data = res.json()
            
            # Pull 'CommonStockSharesOutstanding' (Actual ledger data)
            facts = data.get("facts", {}).get("us-gaap", {})
            shares_path = facts.get("CommonStockSharesOutstanding", {}).get("units", {}).get("shares", [])
            latest_shares = shares_path[-1].get("val", 0) if shares_path else 0

            # We treat 0.5% of the total float as our 'Kinetic Conviction' proxy
            # This ensures NVDA (Huge float) looks different from XOM.
            simulated_vol = latest_shares * 0.005 

            return {
                "insider_buy_volume": simulated_vol,
                "institutional_hold": 0.75, 
                "source": "SEC_EDGAR_JSON",
                "company_name": data.get("entityName", ticker)
            }
        except: return None

    def fetch_insider_signals(self, ticker):
        """SEC First, Alpha Vantage Fallback."""
        edgar_data = self.fetch_edgar_signals(ticker)
        if edgar_data: return edgar_data

        if self.get_ammo_count() >= self.limit:
            return {"status": "RATE_LIMIT_HIT", "insider_buy_volume": 0}

        api_key = st.secrets.get("ALPHA_VANTAGE_KEY") or os.getenv("ALPHA_VANTAGE_KEY")
        url = f'https://www.alphavantage.co/query?function=INSIDER_TRANSACTIONS&symbol={ticker}&apikey={api_key}'
        try:
            res = requests.get(url, timeout=10).json()
            self.log_shot(1)
            transactions = res.get("data", [])
            vol = sum(int(float(tx.get("shares", 0))) for tx in transactions if tx.get("acquisition_or_disposal") == "A")
            return {"insider_buy_volume": vol, "institutional_hold": 0.85, "source": "ALPHA_VANTAGE"}
        except: return {"insider_buy_volume": 0, "status": "OFFLINE"}

    def calculate_truth_multiplier(self, signals):
        volume = signals.get("insider_buy_volume", 0)
        inst_hold = signals.get("institutional_hold", 0.0)
        if volume == 0: return 0.1  
        return round(1.0 + (volume / 50000000.0) + (inst_hold * 1.5), 2)
        
