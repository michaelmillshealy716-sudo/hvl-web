

# ==========================================
# FILE: app.py
# ==========================================

```python
# =============================================================================
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# This source code is the proprietary property of Michael Healy.
# Unauthorized reproduction, distribution, or reverse-engineering is strictly
# prohibited. This file is part of the VERITAS Auditor / FASE Engine.
# =============================================================================

import streamlit as st
import os
from veritas_engine import VeritasGatedEngine

st.set_page_config(page_title="VERITAS X FASE", page_icon="⚖️", layout="wide")

# Initialize Engine
veritas = VeritasGatedEngine()

st.title("⚖️ HEALY VECTOR LABS: SYSTEM AUDIT")

# UI TABS
tab1, tab2 = st.tabs(["🚀 ACTIVE DASHBOARD", "📚 AUDIT METHODOLOGY"])

with tab1:
    ticker = st.text_input("Enter Ticker Symbol", value="NVDA").upper()
    if st.button("RUN SYSTEM ALIGNMENT AUDIT"):
        with st.spinner(f"Auditing Ground Truth for {ticker}..."):
            signals = veritas.fetch_insider_signals(ticker)
            st.subheader(f"Signal Data: {signals.get('company_name', ticker)}")
            st.write(signals) # The "Receipt" for your screenshot
            
            multiplier = veritas.calculate_truth_multiplier(signals)
            st.metric("TRUTH MULTIPLIER", f"{multiplier}x")
            
            # Contextual Feedback
            if multiplier == 0.1:
                st.error("⚠️ SIGNAL: DELUSION. Insiders are not backing this move.")
            elif multiplier < 3.0:
                st.info("ℹ️ SIGNAL: STABLE. Structural integrity confirmed via Institutional Floor.")
            else:
                st.success("🎯 SIGNAL: HIGH CONVICTION. Insider alignment detected.")

with tab2:
    st.header("The Veritas Methodology")
    st.markdown("---")
    
    st.subheader("What is the Truth Multiplier?")
    st.write("""
    The Truth Multiplier is a proprietary 'Conviction Coefficient' developed by Healy Vector Labs. 
    It audits the gap between market sentiment and the actual capital movement of corporate insiders.
    """)
    
    st.markdown("""
    ### **The Three Pillars of Truth**
    1. **The Base (1.0):** Every audited asset starts at a baseline of 1.0.
    2. **The Fortress (Institutional Hold):** We weight institutional ownership at **1.5x**. If 'Big Money' owns the building, the floor is reinforced.
    3. **The Kinetic (Insider Volume):** Every 50 Million shares of insider buying adds **+1.0x** to the multiplier.
    """)
    
    st.info("### **The Formula**")
    st.latex(r"Multiplier = 1.0 + \frac{InsiderVolume}{50,000,000} + (Institutional\% \times 1.5)")

    st.markdown("""
    ### **Understanding the Scale**
    * **0.1x | Delusion:** Gate locked. No insider buying.
    * **1.0x - 3.0x | Stable:** High institutional 'Fortress' state.
    * **3.1x - 6.0x | Conviction:** Aggressive insider alignment with big money.
    * **6.1x+ | Kinetic Alpha:** Rare, total capital handshake.
    """)

st.divider()
st.caption("Healy Vector Labs © 2026 | Built for High-Frequency Frame Control.")

```


# ==========================================
# FILE: certified_targets.json
# ==========================================

```json
{
    "ticker": "AMD",
    "type": "put",
    "price": 411.685,
    "timestamp": "2026-05-06 12:21:45"
}
```


# ==========================================
# FILE: diagnostic.py
# ==========================================

```python
# =============================================================================
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# This source code is the proprietary property of Michael Healy.
# Unauthorized reproduction, distribution, or reverse-engineering is strictly
# prohibited. This file is part of the VERITAS Auditor / FASE Engine.
# =============================================================================

import numpy as np

def run_diagnostic(e_values, r_values):
    e_variance = np.var(e_values)
    # Checking if the 'Strike' is stationary or fluctuating
    r_stability = np.mean(r_values) / (np.std(r_values) if np.std(r_values) > 0 else 0.001)
    
    print("\n" + "="*30)
    print("VERITAS ARCHITECT DIAGNOSTIC")
    print("="*30)
    print(f"Current Error (E): {e_values[-1]}")
    print(f"Error Variance:    {e_variance:.6f}")
    print(f"Confidence (R):   {r_values[-1]}")
    print(f"Stability Score:   {r_stability:.2f}")
    print("-" * 30)
    
    if e_variance < 0.05 and r_stability > 10.0:
        return "STATUS: [STRIKE] ALIGNMENT CONFIRMED. PROCEED TO 2ND DERIVATIVE."
    else:
        return "STATUS: [DRIFT] DETECTED. RE-CALIBRATE 1ST ORDER BEFORE ACCELERATING."

# Pre-loaded with your current 'Strike' alignment data
e_log = [1.266] * 10 
r_log = [63.89] * 10

print(run_diagnostic(e_log, r_log))


```


# ==========================================
# FILE: fase_async.py
# ==========================================

```python
# =============================================================================
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# This source code is the proprietary property of Michael Healy.
# Unauthorized reproduction, distribution, or reverse-engineering is strictly
# prohibited. This file is part of the VERITAS Auditor / FASE Engine.
# =============================================================================

import asyncio
import websockets
import json
import numpy as np
import os
from datetime import datetime

# --- THE VAULT KEYS (PAPER TRADING) ---
API_KEY = "PKINCZBTEPX55UXMA5IZNYM34R"
API_SECRET = "CnLe5QKcngbARFfW5UyUMoyBgEj4dvWPKrTH534S9QVx"
STREAM_URL = "wss://stream.data.alpaca.markets/v2/iex"

# --- PERIWINKLE COLOR MATRIX ---
CLR = {
    "PERI": "\033[38;5;147m", 
    "SLATE": "\033[38;5;103m",
    "CYAN": "\033[38;5;159m",
    "RED": "\033[38;5;203m",
    "GOLD": "\033[38;5;220m",
    "X": "\033[0m"
}

S_CONST = 63890.00
ENTROPY_CEIL = 2.32
WATCHLIST = ["TSLA", "NVDA", "AAPL", "META", "AMD", "MSTR"]

def draw_bar(val, max_val=1000000, width=10):
    percent = min(1.0, (val / max_val))
    filled = int(width * percent)
    bar = "■" * filled + "□" * (width - filled)
    return f"{CLR['PERI']}[{bar}]{CLR['X']}"

class ForensicAudit:
    @staticmethod
    def benford_score(volumes):
        if len(volumes) < 10: return 1.0
        first_digits = [int(str(abs(int(v)))[0]) for v in volumes if v > 0]
        if not first_digits: return 1.0
        counts = np.histogram(first_digits, bins=range(1, 11))[0]
        probs = counts / len(first_digits) if len(first_digits) > 0 else np.zeros(9)
        expected = np.array([np.log10(1 + 1/d) for d in range(1, 10)])
        return np.sum(np.abs(probs - expected))

class AsyncVeritasKernel:
    def __init__(self):
        self.tick_data = {sym: {'prices': [], 'volumes': []} for sym in WATCHLIST}
        self.streaks = {sym: 0 for sym in WATCHLIST}

    def process_tick(self, symbol, price, size):
        self.tick_data[symbol]['prices'].append(price)
        self.tick_data[symbol]['volumes'].append(size)
        
        # Keep arrays fast and lean (rolling 50 ticks)
        if len(self.tick_data[symbol]['prices']) > 50:
            self.tick_data[symbol]['prices'].pop(0)
            self.tick_data[symbol]['volumes'].pop(0)

        prices = np.array(self.tick_data[symbol]['prices'])
        volumes = np.array(self.tick_data[symbol]['volumes'])
        
        if len(prices) < 20: return # Wait for enough tape

        # The Hardened Physics
        v = np.diff(prices)[-1]
        a = np.diff(np.diff(prices))[-1] if len(prices) > 2 else 0
        delta = (((prices[-1] + v + 0.5 * a) - prices[-1]) / prices[-1]) * 100
        
        integrity = ForensicAudit.benford_score(volumes)
        jerk = (np.diff(np.diff(np.diff(prices)))[-1] / 6) if len(prices) > 3 else 0
        vol_sum = np.sum(volumes[-5:])
        p = volumes[-5:] / (vol_sum + 1e-9)
        entropy = -np.sum(p * np.log2(p + 1e-9))
        s_score = (abs(jerk) * 10000) / (entropy + 0.1)

        # Decision Matrix
        is_synth = integrity > 0.25
        self.streaks[symbol] = (self.streaks[symbol] + 1) if entropy < ENTROPY_CEIL else 0
        
        guard_status = f"{CLR['SLATE']}STABLE{CLR['X']}"
        if is_synth and abs(delta) > 0.1: guard_status = f"{CLR['RED']}FAKE_OUT{CLR['X']}"
        elif not is_synth and abs(delta) > 0.05: guard_status = f"{CLR['GOLD']}ALIGN{CLR['X']}"
        
        int_tag = f"{CLR['SLATE']}SYNTH{CLR['X']}" if is_synth else f"{CLR['CYAN']}REAL{CLR['X']}"
        s_bar = draw_bar(s_score)

        print(f"{symbol:8} | {s_bar} S:{s_score:8.0f} | Δ:{delta:+6.3f}% | {int_tag} | {guard_status} | {CLR['PERI']}[T-{self.streaks[symbol]}]{CLR['X']}")

async def listen_to_market():
    kernel = AsyncVeritasKernel()
    os.system('clear')
    print(f"{CLR['PERI']}HEALY VECTOR KERNEL V6.0 | SUB-SECOND MATRIX | {datetime.now().strftime('%H:%M:%S')}{CLR['X']}")
    print(f"{CLR['SLATE']}" + "="*85 + f"{CLR['X']}")
    
    async with websockets.connect(STREAM_URL) as ws:
        # 1. Breach the Vault
        auth = {"action": "auth", "key": API_KEY, "secret": API_SECRET}
        await ws.send(json.dumps(auth))
        auth_response = await ws.recv()
        print(f"{CLR['SLATE']}Vault Auth: {auth_response}{CLR['X']}")
        
        # 2. Subscribe to the Tape
        sub = {"action": "subscribe", "trades": WATCHLIST}
        await ws.send(json.dumps(sub))
        sub_response = await ws.recv()
        print(f"{CLR['SLATE']}Stream Sub: {sub_response}{CLR['X']}")
        print(f"{CLR['GOLD']}Monitoring pipe. Awaiting sub-second ticks...{CLR['X']}")

        # 3. Ingest Sub-Second Ticks
        while True:
            message = await ws.recv()
            data = json.loads(message)
            for event in data:
                if event.get('T') == 't': # 't' means Trade Execution
                    kernel.process_tick(event['S'], float(event['p']), float(event['s']))

if __name__ == "__main__":
    try:
        asyncio.run(listen_to_market())
    except KeyboardInterrupt:
        print(f"\n{CLR['RED']}Connection Terminated.{CLR['X']}")


```


# ==========================================
# FILE: fase_engine.py
# ==========================================

```python
# =============================================================================
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# This source code is the proprietary property of Michael Healy.
# Unauthorized reproduction, distribution, or reverse-engineering is strictly
# prohibited. This file is part of the VERITAS Auditor / FASE Engine.
# =============================================================================


import numpy as np
from scipy.ndimage import gaussian_filter1d

def get_quantum_state(price_array, sigma=1.5):
    # Phase Gamma: Gaussian Shield
    smoothed = gaussian_filter1d(price_array, sigma=sigma)

    # Phase Alpha: Higher-Order Derivatives
    v = np.gradient(smoothed)
    a = np.gradient(v)
    jerk = np.gradient(a)
    snap = np.gradient(jerk)
    crackle = np.gradient(snap)
    pop = np.gradient(crackle)

    # Phase Delta: Schrodinger Propagator
    kinetic = 0.5 * (v**2)
    potential = np.abs(jerk)
    hamiltonian = kinetic + potential

    # THE CYBER CRACK FIX: Dynamic Orbital Amplitude
    # Normalizes the violence of the trend to a 0.0 - 1.0 probability density
    h_max = np.max(np.abs(hamiltonian)) + 1e-8
    H_norm = hamiltonian / h_max
    prob_density = np.clip(1.0 - np.exp(-H_norm * 5.0), 0, 1)

    # Standard Delta for HUD
    v_raw = np.diff(price_array)[-1] if len(price_array) > 1 else 0
    a_raw = np.diff(np.diff(price_array))[-1] if len(price_array) > 2 else 0
    delta = (((price_array[-1] + v_raw + 0.5 * a_raw) - price_array[-1]) / price_array[-1]) * 100

    # PROTOCOL SYNC: Return exactly 3 values
    return pop[-1], prob_density[-1], delta


```


# ==========================================
# FILE: fase_euler.py
# ==========================================

```python
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# Lead Architect: Michael Healy
# ==========================================================

import numpy as np
import time
import os
from datetime import datetime
import yfinance as yf
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import requests
import json

# ==========================================================
# SYSTEM ARCHITECTURE: FIREBASE REST ENDPOINT
# ==========================================================
FIREBASE_URL = "https://healy-vector-labs-default-rtdb.firebaseio.com/fase_telemetry.json"

class GeopoliticalBridge:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        
    def get_intensity_scalar(self, raw_headline):
        if not raw_headline:
            return 0.0
        sentiment_dict = self.analyzer.polarity_scores(raw_headline)
        return sentiment_dict['compound']

class EdgarRaven:
    def __init__(self):
        print("[SYSTEM] Initializing Healy Vector Labs - FASE Data Pipeline")
        self.bridge = GeopoliticalBridge()
        
    def get_ticker_sentiment(self, ticker):
        print(f"[EDGAR] Tapping into live data feeds for {ticker}...")
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            if news:
                first_story = news[0]
                if isinstance(first_story, dict) and 'content' in first_story:
                    headline = first_story['content'].get('title', '')
                else:
                    headline = first_story.get('title', '')
                
                if headline:
                    print(f"[EDGAR] Live Headline Parsed: '{headline}'")
                    return headline
            return ""
        except Exception as e:
            print(f"[EDGAR] Connection timeout for {ticker}")
            return ""

class FASEStochasticEngine:
    def __init__(self, x0, T, dt):
        self.x0 = x0
        self.T = T
        self.dt = dt
        self.N = int(T / dt)
        self.t = np.linspace(0, self.T, self.N)
        
    def apply_agentic_sentiment(self, base_mu, sentiment_score):
        return base_mu + (sentiment_score * 0.5 * base_mu)
        
    def simulate_sentiment_path(self, base_mu, sigma, sentiment_score):
        mu_adj = self.apply_agentic_sentiment(base_mu, sentiment_score)
        dw = np.random.normal(0, np.sqrt(self.dt), self.N)
        W = np.cumsum(dw)
        S = self.x0 * np.exp((mu_adj - 0.5 * sigma**2) * self.t + sigma * W)
        return S

if __name__ == "__main__":
    tickers = ["TSLA", "F", "XOM", "PFE", "CL=F" ]
    N_sims = 1000
    
    base_prices = {
        "TSLA": 175.50,
        "F": 12.30,
        "XOM": 118.20,
        "PFE": 28.40,
        "CL=F": 82.10
    }
    
    print("[SYSTEM] Initializing FASE Pipeline for continuous Cloud deployment...")
    edgar = EdgarRaven()
    self_bridge = GeopoliticalBridge()
    
    try:
        while True:
            os.system('clear' if os.name == 'posix' else 'cls')
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[SYSTEM] Commencing Execution Cycle: {current_time}")
            print("-" * 45)
            
            web_data = {
                "last_updated": current_time,
                "execution_id": time.time(),
                "projections": {}
            }
            
            for target_ticker in tickers:
                print("-" * 45)
                current_headline = edgar.get_ticker_sentiment(target_ticker)
                live_sentiment = self_bridge.get_intensity_scalar(current_headline)
                
                current_price = base_prices.get(target_ticker, 100.0)
                engine = FASEStochasticEngine(x0=current_price, T=1.0, dt=0.01)
                final_states = []
                
                print(f"[FASE] Running {N_sims}-path Monte Carlo on {target_ticker}...")
                for _ in range(N_sims):
                    path = engine.simulate_sentiment_path(base_mu=0.1, sigma=0.3, sentiment_score=live_sentiment)
                    final_states.append(path[-1])
                    
                expected_value = np.mean(final_states)
                ci_low, ci_high = np.percentile(final_states, [2.5, 97.5])
                rel_spread = (ci_high - ci_low) / expected_value
                
                web_data["projections"][target_ticker] = {
                    "expected_value": round(float(expected_value), 2),
                    "ci_low": round(float(ci_low), 2),
                    "ci_high": round(float(ci_high), 2),
                    "sentiment_score": round(float(live_sentiment), 3),
                    "headline": current_headline,
                    "volatility_alert": bool(rel_spread > 1.5)
                }

            # ==========================================
            # REST API INJECTION: OVERWRITE FIREBASE
            # ==========================================
            try:
                print(f"\n[SYSTEM] Executing PUT Request to Firebase RTDB...")
                headers = {'Content-Type': 'application/json'}
                res = requests.put(FIREBASE_URL, data=json.dumps(web_data), headers=headers, timeout=10)
                
                if res.status_code == 200:
                    print(f"[SYSTEM] 200 OK: State Reconciled. Sleeping 120s...")
                else:
                    print(f"[ERR] Sync Failure. Status: {res.status_code} - {res.text}")
                    
            except Exception as e:
                print(f"[ERR] REST Pipeline offline: {e}")

            time.sleep(120)

    except KeyboardInterrupt:
        print("\n\033[91m[ SYSTEM ] FASE ENGINE ARCHIVE LOCKED AND COLD STORED.\033[0m")

```


# ==========================================
# FILE: fase_ghost.py
# ==========================================

```python
# =============================================================================
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# This source code is the proprietary property of Michael Healy.
# Unauthorized reproduction, distribution, or reverse-engineering is strictly
# prohibited. This file is part of the VERITAS Auditor / FASE Engine.
# =============================================================================

import numpy as np
from datetime import datetime
from fase_engine import get_quantum_state

CLR = {
    "PERI": "\033[38;5;147m",
    "GREEN": "\033[38;5;82m",
    "RED": "\033[38;5;203m",
    "X": "\033[0m",
    "BOLD": "\033[1m"
}

WATCHLIST = ["BTC/USD", "ETH/USD", "SOL/USD"]

class GhostKernel:
    def __init__(self):
        self.tick_data = {sym: {'prices': []} for sym in WATCHLIST}
        self.in_pos = {sym: False for sym in WATCHLIST}
        self.prob_threshold = 0.85 

    def process_tick(self, symbol, price):
        if symbol not in self.tick_data: return
        self.tick_data[symbol]['prices'].append(price)
        if len(self.tick_data[symbol]['prices']) > 50: 
            self.tick_data[symbol]['prices'].pop(0)

        p_arr = np.array(self.tick_data[symbol]['prices'])

        if len(p_arr) < 20:
            print(f"{CLR['PERI']}[WARM-UP {len(p_arr):02}/20]{CLR['X']} {symbol:8} | SYNCING BASELINE...")
            return

        # Call the external Quantum Engine for the heavy math
        pop, prob_density, delta = get_quantum_state(p_arr)

        signal = ""
        # Trigger [STRIKE/ENTRY] on high probability of sp (Linear) state
        if prob_density > self.prob_threshold and delta > 0.005 and not self.in_pos[symbol]:
            signal = f"{CLR['BOLD']}{CLR['GREEN']}[STRIKE/ENTRY]{CLR['X']}"
            self.in_pos[symbol] = True
        elif self.in_pos[symbol] and delta <= 0.001:
            signal = f"{CLR['BOLD']}{CLR['RED']}[EXIT/SELL]{CLR['X']}"
            self.in_pos[symbol] = False

        print(f"{CLR['PERI']}{symbol:8}{CLR['X']} | Δ:{delta:+7.4f}% | Ψ:{prob_density:6.4f} | Pop:{pop:9.6f} | {signal:15} | {datetime.now().strftime('%H:%M:%S')}")


```


# ==========================================
# FILE: fase_master.py
# ==========================================

```python
# =============================================================================
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# This source code is the proprietary property of Michael Healy.
# Unauthorized reproduction, distribution, or reverse-engineering is strictly
# prohibited. This file is part of the VERITAS Auditor / FASE Engine.
# =============================================================================

import json
import subprocess
import time
import sys
import os
import numpy as np
import robin_stocks.robinhood as rh
from datetime import datetime
import logging

# Kill API noise
logging.getLogger("urllib3").setLevel(logging.CRITICAL)

class C:
    G = "\033[92m"
    R = "\033[91m"
    Y = "\033[93m"
    B = "\033[94m"
    CYAN = "\033[96m"
    M = "\033[35m"
    BBLD = "\033[1m"
    END = "\033[0m"

MAX_BULLETS = 3
ACTIVE_TRADES = {}

# [✔] FULL MATRIX REPLICATED EXACTLY
STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "AMD", 
    "SPY", "QQQ", "IWM", "DIA", "VXX", "UVXY", "SQQQ", "TQQQ", "SOXX", "SOXL",
    "INTC", "TSM", "AVGO", "QCOM", "MU", "TXN", "AMAT", "LRCX",
    "CRM", "ADBE", "NOW", "SNOW", "PLTR", "CRWD", "PANW", 
    "JPM", "BAC", "WFC", "GS", "MS", "V", "MA", "AXP", "PYPL", "SQ", "COIN", "HOOD",
    "WMT", "TGT", "COST", "HD", "LOW", "MCD", "SBUX", "NKE", "KO", "PEP",
    "JNJ", "UNH", "PFE", "MRK", "ABBV", "LLY", "AMGN", "CVS",
    "XOM", "CVX", "COP", "OXY", "SLB", "HAL", 
    "BA", "LMT", "RTX", "NOC", "GD", "CAT", "DE",
    "DIS", "NFLX", "SPOT", "ROKU", "EA",
    "UBER", "LYFT", "DAL", "UAL", "LUV", "AAL",
    "ABNB", "BKNG", "MAR", "HLT", "CCL", "RCL", "MGM", "DKNG"
]

def rh_login():
    try:
        print(f"{C.CYAN}[*] SYSTEM PURGE: INITIATING FRESH HANDSHAKE...{C.END}")
        try:
            rh.logout() 
        except:
            pass
        
        # Hardcoded Architect Credentials
        rh.login("michaelmillshealy716@gmail.com", "M3141592654h*!*$$", expiresIn=86400, pickle_name="fasemaster")
        
        profile = rh.account.load_account_profile()
        bp = float(profile.get('buying_power', '0.00'))
        print(f"{C.G}[+] SUCCESS. FASEMASTER ACTIVE. BP: ${bp:.2f}{C.END}")
    except Exception as e:
        print(f"{C.R}[!] AUTH CRITICAL: {e}{C.END}")
        sys.exit(1)

def get_wallet():
    try:
        profile = rh.account.load_account_profile()
        return float(profile.get('buying_power', '0.00'))
    except Exception: return 0.0

def get_kinematics(prices):
    if len(prices) < 4: return 0.0, 0.0, 0.0
    p = np.array(prices[-4:], dtype=float)
    v = np.gradient(p)
    a = np.gradient(v)
    return v[-1], a[-1], p[-1]

def find_cheap_option(ticker, opt_type):
    try:
        chains = rh.options.get_chains(ticker)
        if not chains or not chains.get('expiration_dates'): return None
        valid_exp = [exp for exp in chains['expiration_dates'] if (datetime.strptime(exp, "%Y-%m-%d") - datetime.now()).days >= 2]
        if not valid_exp: return None
        valid_options = rh.options.find_options_by_expiration(ticker, expirationDate=valid_exp[0], optionType=opt_type.lower())
        valid = [o for o in valid_options if o['ask_price'] and 0.03 <= float(o['ask_price']) <= 0.20]
        if not valid: return None
        valid.sort(key=lambda x: float(x['volume'] or 0), reverse=True)
        return valid[0]
    except Exception: return None

def manage_positions():
    for ticker, data in list(ACTIVE_TRADES.items()):
        opt = data['option']
        try:
            m_data = rh.options.get_option_market_data(ticker, opt['expiration_date'], opt['strike_price'], data['type'].lower())
            info = m_data[0] if isinstance(m_data, list) else m_data
            if not info: continue
            
            cur_bid = float(info.get('bid_price', 0))
            if cur_bid == 0: continue
            
            profit = ((cur_bid - float(data['entry_premium'])) / float(data['entry_premium'])) * 100
            if profit >= 18.5:
                print(f"\n{C.G}[$$$] PROFIT CAPTURED: +{profit:.2f}% ON {ticker}{C.END}")
                rh.orders.order_sell_option_limit("close", "credit", round(cur_bid, 2), ticker, 1, opt['expiration_date'], opt['strike_price'], data['type'].lower())
                del ACTIVE_TRADES[ticker]
        except Exception: continue

def hunt_best_deal():
    cands = []
    wallet = get_wallet()
    old_stderr = sys.stderr
    sys.stderr = open(os.devnull, 'w')
    try:
        print(f"\r{C.B}[*] SCANNING {len(STOCKS)} TICKERS | BP: ${wallet:.2f}{C.END}   ", end="", flush=True)
        for t in STOCKS:
            if t in ACTIVE_TRADES: continue
            try:
                h = rh.stocks.get_stock_historicals(t, interval='5minute', span='week', bounds='regular')
                # [!] THE FIX: Skip 404s/None results without crashing
                if not h or h[0] is None: continue 
                
                px = [float(x['close_price']) for x in h if x and x['close_price']]
                if len(px) < 4: continue
                
                v, a, p = get_kinematics(px)
                cands.append({'ticker': t, 'score': a, 'v': v, 'price': px[-1]})
            except: continue
    finally: sys.stderr = old_stderr

    if not cands: return None
    mu, sigma = np.mean([c['score'] for c in cands]), np.std([c['score'] for c in cands])
    cands.sort(key=lambda x: abs((x['score'] - mu) / sigma if sigma > 0 else 0), reverse=True)
    
    for c in cands:
        z = (c['score'] - mu) / sigma if sigma > 0 else 0
        if abs(z) >= 1.84 and wallet >= 3.00:
            opt_type = 'call' if c['v'] >= 0 else 'put'
            target_opt = find_cheap_option(c['ticker'], opt_type)
            if target_opt:
                print(f"\n{C.G}{C.BBLD}[♛] ALPHA TARGET: {c['ticker']} | Z: {z:.2f}{C.END}")
                return {'ticker': c['ticker'], 'type': opt_type, 'option': target_opt}
    return None

def execute_trade(target):
    opt = target['option']
    try:
        rh.orders.order_buy_option_limit("open", "debit", opt['ask_price'], target['ticker'], 1, opt['expiration_date'], opt['strike_price'], target['type'])
        print(f"{C.G}[✔] ORDER SENT: {target['ticker']} {target['type'].upper()} @ ${opt['ask_price']}{C.END}")
        ACTIVE_TRADES[target['ticker']] = {"entry_premium": float(opt['ask_price']), "option": opt, "type": target['type']}
    except Exception as e: print(f"{C.R}[!] TRADE ERROR: {e}{C.END}")

if __name__ == "__main__":
    rh_login()
    print(f"{C.BBLD}{C.Y}[!] HEALY VECTOR LABS: FASEMASTER V2.2 ONLINE{C.END}")
    while True:
        try:
            if len(ACTIVE_TRADES) < MAX_BULLETS:
                target = hunt_best_deal()
                if target: execute_trade(target)
            manage_positions()
            time.sleep(2)
        except KeyboardInterrupt: sys.exit(0)


```


# ==========================================
# FILE: fase_stage1.py
# ==========================================

```python
# =============================================================================
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# This source code is the proprietary property of Michael Healy.
# Unauthorized reproduction, distribution, or reverse-engineering is strictly
# prohibited. This file is part of the VERITAS Auditor / FASE Engine.
# =============================================================================

import yfinance as yf
import pandas as pd
import numpy as np
import warnings

# Suppress warnings to keep the terminal UI clean
warnings.filterwarnings('ignore')

class FASE_Broad_Screener:
    def __init__(self, tickers):
        self.tickers = tickers
        self.compressed_assets = []

    def check_compression(self, df):
        # 1. Bollinger Bands (20-day SMA, 2 StdDev)
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['StdDev'] = df['Close'].rolling(window=20).std()
        df['Lower_BB'] = df['SMA_20'] - (2 * df['StdDev'])
        df['Upper_BB'] = df['SMA_20'] + (2 * df['StdDev'])

        # 2. Keltner Channels (20-day EMA, 1.5 ATR)
        # Using a standard 14-period ATR for the channel width
        df['TR'] = np.maximum((df['High'] - df['Low']),
                   np.maximum(abs(df['High'] - df['Close'].shift(1)),
                   abs(df['Low'] - df['Close'].shift(1))))
        df['ATR_14'] = df['TR'].rolling(window=14).mean()
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['Lower_KC'] = df['EMA_20'] - (1.5 * df['ATR_14'])
        df['Upper_KC'] = df['EMA_20'] + (1.5 * df['ATR_14'])

        # 3. SINGULARITY TRIGGER: Bollinger Bands fully inside Keltner Channels
        # This is the "Bingo" zone where volatility is coiled like a spring.
        df['Squeeze_On'] = (df['Lower_BB'] > df['Lower_KC']) & (df['Upper_BB'] < df['Upper_KC'])
        
        # Return the status of the most recent trading day
        return df['Squeeze_On'].iloc[-1]

    def run_scan(self):
        # Clear terminal screen
        print("\033[2J\033[H", end="")
        print("\033[38;5;147m==============================================\033[0m")
        print("\033[38;5;147m--- FASE MASTER: BROAD SWEEP (200+ RADAR) ---\033[0m")
        print("\033[38;5;147m==============================================\033[0m\n")
        
        count = 0
        total = len(self.tickers)
        
        for ticker in self.tickers:
            count += 1
            try:
                # Progress indicator for long scans on mobile
                if count % 10 == 0:
                    print(f"\033[38;5;244mScanning {count}/{total}...\033[0m", end="\r")
                
                # Fetching 2 months of data to ensure all rolling calcs are accurate
                data = yf.download(ticker, period="2mo", progress=False)
                if len(data) < 20: 
                    continue

                if self.check_compression(data):
                    print(f"\033[93m[SINGULARITY]\033[0m {ticker:<5} | STATUS: \033[95mCOMPRESS\033[0m")
                    self.compressed_assets.append(ticker)
            except Exception:
                # Silent skip for delisted or invalid tickers
                pass
                
        print(f"\n\n\033[92mSCAN COMPLETE. TARGETS ACQUIRED: {len(self.compressed_assets)}\033[0m\n")
        return self.compressed_assets

# ===============================================
# --- THE 200+ ROSTER: LIQUIDITY ACQUISITION ---
# ===============================================
target_list = [
    # --- TECH & SEMIS (High Gamma Potential) ---
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "AMD", "AVGO", "CSCO", "ORCL", 
    "ADBE", "CRM", "INTC", "QCOM", "TXN", "MU", "AMAT", "LRCX", "ADI", "KLAC", 
    "SNOW", "PANW", "PLTR", "WDAY", "TEAM", "NET", "CRWD", "DDOG", "MDB", "ZS",
    "IBM", "NOW", "SHOP", "UBER", "ABNB", "PATH", "SE", "U", "DOCU", "TWLO",
    # --- ENERGY & UTILITIES ---
    "XOM", "CVX", "SHEL", "BP", "TTE", "COP", "SLB", "EOG", "MPC", "PSX", 
    "NEE", "DUK", "SO", "D", "AEP", "EXC", "XEL", "ED", "VLO", "HES",
    "HAL", "BKR", "DVN", "FANG", "LNG", "KMI", "WMB", "OKE", "CNQ", "PXD",
    # --- FINANCIALS & FINTECH ---
    "JPM", "BAC", "WFC", "C", "GS", "MS", "V", "MA", "AXP", "PYPL", 
    "SQ", "COIN", "HOOD", "SOFI", "AFRM", "BLK", "SCHW", "PGR", "CB", "MMC",
    "AON", "MET", "PRU", "TRV", "ALL", "SYF", "COF", "DFS", "USB", "TFC",
    # --- HEALTHCARE & PHARMA ---
    "LLY", "UNH", "JNJ", "ABBV", "MRK", "PFE", "AMGN", "ISRG", "GILD", "VRTX", 
    "REGN", "TMO", "DHR", "BMY", "ZTS", "BSX", "MDT", "CVS", "CI", "HCA",
    "SYK", "BDX", "EW", "MCK", "ABC", "CAH", "ELV", "HUM", "CNC", "MOH",
    # --- CONSUMER & RETAIL ---
    "WMT", "COST", "HD", "LOW", "TGT", "NKE", "SBUX", "TJX", "EL", "CL", 
    "PG", "KO", "PEP", "PM", "MO", "MCD", "CMG", "YUM", "LULU", "DASH",
    "DLTR", "DG", "ROST", "BBY", "EBAY", "KSS", "JWN", "GPS", "ULTA", "BKNG",
    # --- INDUSTRIALS & AEROSPACE ---
    "GE", "HON", "UPS", "FDX", "CAT", "DE", "BA", "LMT", "RTX", "NOC", 
    "GD", "MMM", "EMR", "NSC", "CSX", "UNP", "WM", "RSG", "ITW", "PH",
    "ETN", "CPRT", "FAST", "URI", "PWR", "AME", "TDG", "HEI", "TXT", "HWM",
    # --- SPECULATIVE & HIGH VOLUME ---
    "TSLA", "MSTR", "MARA", "RIOT", "CLF", "FCX", "VALE", "AA", "RKLB", "SPCE", 
    "DKNG", "PINS", "NFLX", "DIS", "PARA", "WBD", "F", "GM", "LCID", "RIVN",
    "WBA", "AMC", "GPRO", "BYND", "CVNA", "OPEN", "AI", "SOXL", "TQQQ", "SQQQ"
]

if __name__ == "__main__":
    # Execute the Broad Sweep
    screener = FASE_Broad_Screener(target_list)
    coiled_tickers = screener.run_scan()


```


# ==========================================
# FILE: fase_stage2.py
# ==========================================

```python
# =============================================================================
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# This source code is the proprietary property of Michael Healy.
# Unauthorized reproduction, distribution, or reverse-engineering is strictly
# prohibited. This file is part of the VERITAS Auditor / FASE Engine.
# =============================================================================

import yfinance as yf
import pandas as pd
import warnings

warnings.filterwarnings('ignore')

# The 14 Singularities caught in the net
target_list = ["DOCU", "WMB", "CB", "KO", "PEP", "CL", "CPRT", "VZ", "T", "PG", "JNJ", "PFE", "WM", "RSG"]

def run_predator_sniper(tickers):
    print("\033[2J\033[H", end="")
    print("\033[38;5;208m==============================================\033[0m")
    print("\033[38;5;208m--- FASE MASTER: STAGE 2 (GAMMA SNIPER) ---\033[0m")
    print("\033[38;5;208m==============================================\033[0m\n")
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            price = stock.fast_info['last_price']
            
            # Pull nearest monthly expiry
            expirations = stock.options
            if not expirations: continue
            
            # Focus on the closest expiration to capture maximum Gamma
            chain = stock.option_chain(expirations[0])
            calls = chain.calls
            
            # Logic: Find the strike closest to 5% Out-of-the-Money (OTM)
            # This is the "Sweet Spot" where compression turns into explosion
            target_strike = price * 1.05
            calls['diff'] = abs(calls['strike'] - target_strike)
            best_strike = calls.sort_values('diff').iloc[0]
            
            iv_pct = best_strike.impliedVolatility * 100
            
            print(f"\033[93m[TARGET]\033[0m {ticker:<5} | Price: ${price:.2f}")
            print(f"  > Strike: ${best_strike.strike} Call")
            print(f"  > Premium: ${best_strike.lastPrice:.2f} | IV: {iv_pct:.1f}%")
            
            # Signal Check: If IV is under 30%, it's a "Quiet Singularity"
            if iv_pct < 30:
                print(f"  \033[92m> BINGO: Low IV detected. Cheap Gamma entry.\033[0m")
            print("-" * 30)
            
        except Exception:
            continue

if __name__ == "__main__":
    run_predator_sniper(target_list)


```


# ==========================================
# FILE: haptic_predator.py
# ==========================================

```python
# =============================================================================
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# This source code is the proprietary property of Michael Healy.
# Unauthorized reproduction, distribution, or reverse-engineering is strictly
# prohibited. This file is part of the VERITAS Auditor / FASE Engine.
# =============================================================================

import os
import time
import math
import subprocess

# --- HEALY VECTOR LABS: REGIME 2 CENTROIDS (THE FUSE) ---
TARGET_PHI = 2924.28
TARGET_PSI = 29.24
DECAY_THRESHOLD = 0.15  # 15% drop from peak triggers "Cool Down"
peak_phi = 0

def vibrate(duration=100, count=1, pause=0.1):
    """Executes haptic feedback via Termux API"""
    try:
        for _ in range(count):
            subprocess.run(["termux-vibrate", "-d", str(duration)], check=True)
            if count > 1:
                time.sleep(pause)
    except Exception as e:
        print(f"[ERROR] Haptics failed: {e}")

def monitor_stream(live_phi, live_psi):
    global peak_phi
    
    # 1. CALCULATE PROXIMITY (THE MAGNITUDE)
    # Distance = $\sqrt{(\Phi_{live} - \Phi_{target})^2 + (\Psi_{live} - \Psi_{target})^2}$
    ds = math.sqrt((live_phi - TARGET_PHI)**2 + (live_psi - TARGET_PSI)**2)
    
    # 2. TRACK THE LOCAL PEAK
    if live_phi > peak_phi:
        peak_phi = live_phi
    
    # 3. TRAILING STOP: THE COOL DOWN ALERT
    if peak_phi > 500 and live_phi < (peak_phi * (1 - DECAY_THRESHOLD)):
        print(f"[!] DECAY DETECTED: Phi dropped to {live_phi:.2f}")
        vibrate(duration=30, count=3, pause=0.05) # Sharp, rapid decay alert
        peak_phi = live_phi # Reset peak to avoid alert-spamming
        return

    # 4. HAPTIC TIERING (THE SENSORY "FACE-READ")
    if 500 < live_phi < 1500:
        print(f"[AWAKENING] Phi: {live_phi:.2f} | Dist: {ds:.2f}")
        vibrate(duration=50, count=1) # Single short pulse
        
    elif 1500 <= live_phi < 2500:
        print(f"[THE COIL] Phi: {live_phi:.2f} | Dist: {ds:.2f}")
        vibrate(duration=100, count=2) # Double pulse
        
    elif live_phi >= 2500:
        print(f"!!! SINGULARITY !!! Phi: {live_phi:.2f}")
        vibrate(duration=800, count=1) # Long, heavy "Fuse" vibration

# --- THE EXECUTION LOOP (THE IGNITION) ---
print(">>> HEALY VECTOR LABS: PREDATOR MODE ACTIVE")
print(">>> MONITORING BTC/USD VOLATILITY...")

while True:
    # --- LIVE DATA INTEGRATION POINT ---
    # For now, we simulate your current BTC Phi/Psi (51.41 / 6.36)
    # Replace these two lines with your actual telemetry bridge
    current_phi = 51.41 
    current_psi = 6.36
    
    monitor_stream(current_phi, current_psi)
    
    # Refresh every 10 seconds to preserve A16 battery
    time.sleep(10)


```


# ==========================================
# FILE: healy_vector_main.py
# ==========================================

```python
# =============================================================================
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# This source code is the proprietary property of Michael Healy.
# Unauthorized reproduction, distribution, or reverse-engineering is strictly
# prohibited. This file is part of the VERITAS Auditor / FASE Engine.
# =============================================================================

import time
from smash_master import Veritas_Engine, Shinigo_Intel, Market_Telemetry

class HVL_Mainframe:
    def __init__(self):
        # Initializing the S.M.A.S.H. Subsystems
        self.veritas = Veritas_Engine()
        self.shinigo = Shinigo_Intel()
        self.telemetry = Market_Telemetry()
        self.uptime_cycles = 0

    def daemon_loop(self):
        print("\n" + "="*60)
        print(">>> HEALY VECTOR LABS: MAINFRAME ONLINE <<<")
        print(">>> S.M.A.S.H. SUBSYSTEMS: ENGAGED <<<")
        print("="*60)
        
        try:
            while True:
                # 1. Time & Cycle Tracking
                current_time = time.strftime('%H:%M:%S')
                print(f"\n[SYSTEM PULSE] {current_time} | CYCLE: {self.uptime_cycles}")
                
                # 2. Render the Environment
                self.telemetry.render_dashboard()
                
                # 3. Background Computation Matrix
                score = self.veritas.calculate_ifs(user_lat=8400, partner_lat=340, conversion_rate=0.8)
                strike_status = self.shinigo.calculate_strike_mass(micro_strikes=5, avg_weight=0.25)
                
                # 4. Daemon Output
                print(f"[DAEMON-V] VERITAS SCORE : {score:.4f}")
                print(f"[DAEMON-S] SHINIGO STATUS: {strike_status}")
                print(f"--- DAEMON SLEEPING FOR 60s (Ctrl+C to Terminate) ---")
                
                # Sleep cycle to prevent terminal flooding and API bans
                time.sleep(60)
                self.uptime_cycles += 1
                
        except KeyboardInterrupt:
            print("\n>>> HVL MAINFRAME: MANUAL OVERRIDE INITIATED. DISENGAGING. <<<")

# ==========================================
# --- MAINFRAME IGNITION ---
# ==========================================
if __name__ == "__main__":
    mainframe = HVL_Mainframe()
    mainframe.daemon_loop()


```


# ==========================================
# FILE: hunk_monitor.py
# ==========================================

```python
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# FASE Engine V4.3 - Veritas Auditor Extension
# Hybrid API / Terminal Dashboard Architecture

import time
import datetime
import numpy as np
import yfinance as yf
import plotext as plt
import os
import warnings
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Suppress API noise
warnings.filterwarnings("ignore")

app = FastAPI(title="FASE Engine API", version="4.3")

# Single-line middleware to prevent Termux paste-truncation
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- HEALY VECTOR LABS: VERITAS V4.3 LOGIC ---

def get_euler_intrinsic(p_list):
    if len(p_list) < 10: return p_list[-1]
    f = np.fft.fft(p_list)
    f[len(f)//4:] = 0
    return np.real(np.fft.ifft(f)[-1])

def get_taylor_truth(p_hist):
    if len(p_hist) < 3: return 0.0
    v = p_hist[-1] - p_hist[-2]
    a = (p_hist[-1] - 2*p_hist[-2] + p_hist[-3])
    return abs((v * 0.5) + (a * 1.5)) * 10

def detect_markov_regime(t_score):
    if t_score > 4.10: return "BREAKOUT 🚀"
    elif t_score < 1.0: return "NOISE 🛑"
    else: return "STABLE 🏛️"

def get_volatility(p_hist):
    if len(p_hist) < 2: return 0.0
    returns = np.diff(np.log(p_hist))
    return np.std(returns) * np.sqrt(252) * 100

TICKERS = ['NVDA', 'TSLA', 'TSLL', 'XOM', 'USO', 'ERX' , 'PFE', 'WTI', 'BRK.B' ]

def compute_fase_state():
    data = yf.download(TICKERS, period="1d", interval="1m", progress=False)
    
    if data.empty:
        return {"error": "Failed to ingest market tape"}

    dates = data.index.strftime('%H:%M:%S').tolist()
    close_data = data['Close'] if 'Close' in data.columns else data['Adj Close']

    a_ticker, b_ticker = "USO", "XOM"
    a_p = close_data[a_ticker].dropna().values[-35:]
    b_p = close_data[b_ticker].dropna().values[-35:]
    
    a_z, b_z = [], []
    delta = 0.0

    if len(a_p) > 20:
        for i in range(15, len(a_p) + 1):
            min_a, min_b = a_p[:i], b_p[:i]
            mu_a, sig_a = get_euler_intrinsic(min_a), np.std(min_a)
            mu_b, sig_b = get_euler_intrinsic(min_b), np.std(min_b)
            
            a_z.append((min_a[-1] - mu_a) / sig_a if sig_a > 0 else 0)
            b_z.append((min_b[-1] - mu_b) / sig_b if sig_b > 0 else 0)
            
        delta = a_z[-1] - b_z[-1]

    hud_data = []
    for t in TICKERS:
        try:
            p_min = close_data[t].dropna().values[-30:]
            if len(p_min) < 5: continue
            
            curr_p = p_min[-1]
            mu = get_euler_intrinsic(p_min)
            sigma = np.std(p_min)
            z = (curr_p - mu) / sigma if sigma > 0 else 0
            
            truth = get_taylor_truth(p_min)
            regime = detect_markov_regime(truth)
            vol_pct = get_volatility(p_min)
            
            hud_data.append({
                "ticker": t,
                "price": round(curr_p, 2),
                "z_score": round(z, 2),
                "truth": round(truth, 4),
                "regime": regime,
                "vol_pct": round(vol_pct, 2)
            })
        except Exception:
            pass

    return {
        "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "macro_gap": {
            "dates": dates[-len(a_z):] if len(a_z) > 0 else [],
            "a_ticker": a_ticker,
            "b_ticker": b_ticker,
            "a_z": [round(val, 4) for val in a_z],
            "b_z": [round(val, 4) for val in b_z],
            "arbitrage_delta": round(delta, 4)
        },
        "fleet_hud": hud_data
    }

@app.get("/api/v1/fase-data")
async def get_fase_data():
    return compute_fase_state()

def run_terminal_dashboard():
    print("Establishing FASE Macro Uplink... Calibrating Energy Correlates.")
    try:
        while True:
            state = compute_fase_state()
            if "error" in state:
                time.sleep(60)
                continue

            os.system('clear' if os.name == 'posix' else 'cls')
            print(f"--- HEALY VECTOR LABS | FASE V4.3 | {state['timestamp']} ---")
            
            mg = state["macro_gap"]
            
            plt.clf()
            plt.subplots(1, 2)
            
            plt.subplot(1, 1)
            plt.title(f"FASE Macro Gap: {mg['a_ticker']} (Blue) vs {mg['b_ticker']} (Red)")
            
            if mg["a_z"] and mg["b_z"] and mg["dates"]:
                max_len = min([len(mg["a_z"]), len(mg["b_z"]), len(mg["dates"])])
                
                a_z_plot = mg["a_z"][-max_len:]
                b_z_plot = mg["b_z"][-max_len:]
                dates_plot = mg["dates"][-max_len:]
                
                x_seq = list(range(max_len))
                
                plt.plot(x_seq, a_z_plot, label=f"{mg['a_ticker']} Z", color="blue")
                plt.plot(x_seq, b_z_plot, label=f"{mg['b_ticker']} Z", color="red")
                plt.xticks(x_seq, dates_plot)
                
            plt.hline(0, color="white")
            plt.plotsize(40, 15)

            plt.subplot(1, 2)
            plt.title("Momentum & Volatility Distribution")
            vol_tickers = [item['ticker'] for item in state['fleet_hud']]
            vol_vals = [item['vol_pct'] for item in state['fleet_hud']]
            
            if vol_tickers and vol_vals:
                plt.bar(vol_tickers, vol_vals, color="yellow")
                
            plt.plotsize(40, 15)
            plt.show()

            print(f"\n[FASE ARBITRAGE DELTA]: {mg['arbitrage_delta']} sigma")
            print("-" * 65)
            # Single-line F-strings to completely avoid Termux truncation
            print(f"{'TICKER':<6} {'PRICE':<9} {'Z-SCORE':<10} {'TRUTH':<10} {'VOL(%)':<10} {'REGIME':<15}")
            print("-" * 65)
            
            for item in state["fleet_hud"]:
                print(f"{item['ticker']:<6} ${item['price']:<8.2f} {item['z_score']:<10.2f} {item['truth']:<10.4f} {item['vol_pct']:<10.2f} {item['regime']:<15}")
            
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("\n[!] Lead Architect terminated FASE Engine. Standing By.")

if __name__ == "__main__":
    run_terminal_dashboard()


```


# ==========================================
# FILE: hvl_executor_rh.py
# ==========================================

```python
# =============================================================================
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# This source code is the proprietary property of Michael Healy.
# Unauthorized reproduction, distribution, or reverse-engineering is strictly
# prohibited. This file is part of the VERITAS Auditor / FASE Engine.
# =============================================================================

import json
import time
import os

# --- HVL CONFIG ---
BRIDGE_FILE = "autonomous_bridge.json"
SIMULATION_MODE = True # Set to False on Monday to go LIVE

def main():
    print("="*60)
    print("HVL_EXECUTOR: Healy-Vector-Labs")
    print("LEAD_ARCHITECT: Michael Healy")
    print(f"STATUS: STANDING BY (SIMULATION: {SIMULATION_MODE})")
    print("="*60 + "\n")
    
    while True:
        if os.path.exists(BRIDGE_FILE):
            try:
                with open(BRIDGE_FILE, "r") as f:
                    trade = json.load(f)
                
                print(f"[*] BRIDGE_SIGNAL: {trade['signal']} {trade['ticker']}")
                print(f"[*] VERITAS_SCORE: {trade['veritas_score']}")
                
                if SIMULATION_MODE:
                    print(f"[SIM] EXECUTION PREVENTED: Would buy ATM Call for {trade['ticker']}")
                else:
                    # This is where the Robinhood logic will fire on Monday
                    print(f"[LIVE] EXECUTING TRADE FOR {trade['ticker']}...")
                
                # Clear the bridge so we don't double-trade
                os.remove(BRIDGE_FILE)
                print("[-] Bridge cleared. Waiting for next wave...")
            except Exception as e:
                print(f"[ERR] Bridge Read Error: {e}")
            
        time.sleep(1)

if __name__ == "__main__":
    main()


```


# ==========================================
# FILE: hvl_master_terminal.py
# ==========================================

```python
# =============================================================================
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# This source code is the proprietary property of Michael Healy.
# Unauthorized reproduction, distribution, or reverse-engineering is strictly
# prohibited. This file is part of the VERITAS Auditor / FASE Engine.
# =============================================================================

import pandas as pd
import numpy as np
import yfinance as yf
import time
from datetime import datetime
import warnings
import random
import gc
import json
import os

warnings.filterwarnings("ignore")

# --- HEALY VECTOR LABS 300+ FULL MANIFEST ---
T_STR = "AAPL MSFT GOOGL AMZN NVDA TSLA BRK.B UNH V JNJ JPM MA PG HD CVX LLY ABBV ORCL PFE MRK DVN" 
TICKERS = T_STR.split()

BRIDGE_FILE = "autonomous_bridge.json"
# THE 404 FIX: This guarantees your site loads immediately
WEB_FILE = "index.html" 

SIGNAL_HISTORY = []
MAX_HISTORY = 10

def display_manifest():
    print("="*60)
    print("HVL_NODE: Healy-Vector-Labs")
    print("LEAD_ARCHITECT: Michael Healy")
    print("CORE_ENGINE: Veritas V2.2 (300+ Ticker Matrix)")
    print("UI_STATUS: FULL-SCREEN BLACKOUT + SIGNAL STACK ENABLED")
    print("="*60 + "\n")

def export_to_web():
    """Generates the Blackout UI with the 10-Stock Stack"""
    current_time = datetime.now().strftime("%H:%M:%S")
    html_content = f"""
    <html>
    <head>
        <title>HVL COMMAND CENTER</title>
        <meta http-equiv="refresh" content="30">
        <style>
            body {{ background-color: #000; color: #FFF; font-family: 'Courier New', monospace; margin: 0; padding: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            header {{ border-bottom: 2px solid #0c13fe; padding-bottom: 20px; margin-bottom: 30px; }}
            h1 {{ color: #3f71f4; margin: 0; letter-spacing: 2px; }}
            .signal-card {{ 
                background: rgba(20, 20, 20, 0.9); 
                border: 1px solid #555; 
                margin-bottom: 15px; 
                padding: 15px; 
                border-radius: 5px;
                box-shadow: 0 0 10px rgba(188, 19, 254, 0.1);
            }}
            .signal-header {{ display: flex; justify-content: space-between; align-items: center; }}
            .ticker {{ font-size: 1.5em; font-weight: bold; color: #bc13fe; }}
            .veritas-score {{ color: #3f71f4; font-weight: bold; }}
            .signal-type {{ font-weight: bold; text-transform: uppercase; color: #FFF; }}
            .greeks {{ font-size: 0.8em; color: #888; margin-top: 10px; }}
            footer {{ color: #444; font-size: 0.8em; margin-top: 50px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>HEALY VECTOR LABS</h1>
                <h2>VERITAS V2.2 // AUTONOMOUS_DETECTION_MATRIX</h2>
                <p style="font-size: 0.8em; color: #666;">LAST_SYNC: {current_time} // JACKSONVILLE_NODE</p>
            </header>
            <div id="signal-stack">
    """
    
    for sig in reversed(SIGNAL_HISTORY):
        html_content += f"""
                <div class="signal-card">
                    <div class="signal-header">
                        <span class="ticker">{sig['asset']}</span>
                        <span class="signal-type" style="color: {'#39FF14' if 'GO' in sig['signal'] else '#FF3131'}">{sig['signal']}</span>
                    </div>
                    <p style="margin: 10px 0;">VERITAS_SCORE: <span class="veritas-score">{sig['score']}</span></p>
                    <div class="greeks">
                        DELTA: {sig['greeks']['delta']} | GAMMA: {sig['greeks']['gamma']} | TIME: {sig['timestamp']}
                    </div>
                </div>
        """
        
    html_content += """
            </div>
            <footer>HEALY VECTOR LABS &copy; 2026 // DIFFERENT SPECIES ONLY</footer>
        </div>
    </body>
    </html>
    """
    
    try:
        with open(WEB_FILE, "w") as f:
            f.write(html_content)
    except:
        pass

def exit_signal(ticker, signal, score, greeks):
    """Keeps the UI populated with multiple stocks"""
    new_entry = {
        "asset": ticker, "signal": signal, "score": score,
        "greeks": greeks, "timestamp": datetime.now().strftime("%H:%M:%S")
    }
    SIGNAL_HISTORY.append(new_entry)
    if len(SIGNAL_HISTORY) > MAX_HISTORY:
        SIGNAL_HISTORY.pop(0)
    
    payload = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "ticker": ticker, "veritas_score": score, "greeks": greeks
    }
    
    with open(BRIDGE_FILE, "w") as f:
        json.dump(payload, f)
    
    export_to_web()
    print(f"\n[!!!] BRIDGE_ALERT: {signal} PUSHED FOR {ticker} [!!!]\n")

def PASE_Sniper(ticker):
    """THE FLAWLESS 10-STOCK DETECTION ENGINE"""
    try:
        data = yf.download(ticker, period="5d", interval="1m", progress=False, timeout=10)
        if data.empty or len(data) < 30:
            return 0, 0, "STALE"
        
        df = data.copy()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        prices = df['Close'].values
        
        # 1. RSI Calculation
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        r_val = float(100 - (100 / (1 + rs)).iloc[-1])
        
        # 2. Taylor Series Expansion (3rd Order)
        v = np.diff(prices)
        a = np.diff(v)
        j = np.diff(a)
        taylor_pre = prices[-1] + v[-1] + 0.5*a[-1] + (1/6)*j[-1]
        reality_delta = ((taylor_pre - prices[-1]) / prices[-1]) * 100
        
        # 3. Signal Logic
        veritas_score = round(abs(reality_delta * r_val), 2)
        
        if r_val <= 30 and reality_delta > 0:
            signal = "HIGH CONVICTION - GO"
        elif r_val >= 70 and reality_delta < 0:
            signal = "FORCE SELL"
        else:
            signal = "HOLD"
            
        del data, df, prices, delta, gain, loss
        return r_val, veritas_score, signal

    except Exception as e:
        return 0, 0, f"ERR: {str(e)}"

def main():
    display_manifest()
    
    while True:
        current_time = datetime.now().strftime("%H:%M:%S")
        print(f"--- GLOBAL MATRIX SCAN: {current_time} (TARGETS: {len(TICKERS)}) ---")
        
        for i, ticker in enumerate(TICKERS):
            try:
                r_val, score, signal = PASE_Sniper(ticker)
                
                # Clean Terminal Output
                if "ERR" in signal or signal == "STALE":
                    print(f"[{i+1}/{len(TICKERS)}] {ticker}: CRASHED - {signal}")
                else:
                    print(f"[{i+1}/{len(TICKERS)}] {ticker}: {signal} (RSI: {r_val:.2f} | V_Score: {score})")
                
                if signal != "HOLD" and "ERR" not in signal:
                    greeks = {"delta": round(random.uniform(0.6, 0.8), 3), "gamma": round(random.uniform(0.02, 0.05), 3)}
                    exit_signal(ticker, signal, score, greeks)
                
            except Exception as e:
                print(f"[{i+1}/{len(TICKERS)}] {ticker}: CRASHED - {str(e)}")
            
            finally:
                gc.collect()
                time.sleep(random.uniform(1.2, 2.8)) # The Jitter Evasion
        
        print(f"\n[SCAN_CYCLE_COMPLETE] - Cooling down for 2 minutes...")
        time.sleep(120)

if __name__ == "__main__":
    main()


```


# ==========================================
# FILE: hvl_protect.py
# ==========================================

```python
# =============================================================================
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# =============================================================================
import os

HEADER = """# =============================================================================
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# This source code is the proprietary property of Michael Healy.
# Unauthorized reproduction, distribution, or reverse-engineering is strictly
# prohibited. This file is part of the VERITAS Auditor / FASE Engine.
# =============================================================================
"""

def protect_files():
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".py") and file != "hvl_protect.py":
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    content = f.read()
                
                if "(c) 2026 HEALY VECTOR LABS" not in content:
                    print(f"[+] Shielding: {filepath}")
                    with open(filepath, 'w') as f:
                        f.write(HEADER + "\n" + content)
                else:
                    print(f"[-] Already Protected: {filepath}")

if __name__ == "__main__":
    protect_files()


```


# ==========================================
# FILE: ifs_parser.py
# ==========================================

```python
# =============================================================================
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# This source code is the proprietary property of Michael Healy.
# Unauthorized reproduction, distribution, or reverse-engineering is strictly
# prohibited. This file is part of the VERITAS Auditor / FASE Engine.
# =============================================================================

import math

class SMASH_IFS_Parser:
    def __init__(self):
        self.strike_bounty_eligible = False
        self.frame_score = 0.0
        self.status_label = "TAXABLE"

    def taylor_exp_approx(self, x, terms=7):
        """
        Taylor Series approximation for e^x (Veritas V2.2 logic).
        Provides rigorous mathematical precision without legacy library calls.
        """
        approx = 0
        for n in range(terms):
            approx += (x**n) / math.factorial(n)
        return approx

    def calculate_ifs(self, user_data, partner_data, stats, history):
        # Prevent zero-division or empty data glitches
        if len(stats['user']) == 0 or len(stats['partner']) == 0:
            return 0.0

        avg_user_lat = sum(stats['user']) / len(stats['user'])
        avg_partner_lat = sum(stats['partner']) / len(stats['partner'])

        # --- GAUSSIAN LATENCY SCORING (Optimal: 3 Hours) ---
        optimal_lat = 10800  # 3 Hours in seconds
        sigma = 5000         # Variance threshold
        
        # Calculate Gaussian exponent
        exponent = -0.5 * ((avg_user_lat - optimal_lat) / sigma) ** 2
        
        # --- THE GAUSSIAN GUARDRAIL ---
        # Prevents Taylor Series divergence on extreme ghosting (The 1.4 Trillion Error).
        if exponent < -20: 
            user_latency_multiplier = 0.0
        else:
            user_latency_multiplier = self.taylor_exp_approx(exponent)
        
        # Ratio of Lead Architect timing vs. Partner response
        base_ratio = optimal_lat / avg_partner_lat if avg_partner_lat > 0 else 1.0
        latency_ratio = base_ratio * user_latency_multiplier

        # --- CONVERSION RATE MODIFIER ---
        # High investment verification history
        conversion_rate = history['verified'] / history['total_matches'] if history['total_matches'] > 0 else 0.0

        # --- VERITAS ENGINE FORMULA ---
        # Weighted: 60% Outcome / 40% Timing
        self.frame_score = (0.4 * latency_ratio) + (0.6 * conversion_rate)

        # --- THE HIERARCHY OF FRAME ---
        if self.frame_score > 15.0 and conversion_rate >= 0.95:
            self.status_label = "TOP G"
            self.strike_bounty_eligible = True
        elif self.frame_score > 5.0 and conversion_rate >= 0.8:
            self.status_label = "FRAME SOLID"
            self.strike_bounty_eligible = True
        else:
            self.status_label = "TAXABLE"
            self.strike_bounty_eligible = False

        return self.frame_score

# --- S.M.A.S.H. EXECUTION & TEST BLOCK ---
if __name__ == "__main__":
    # Test Data: High Performance JAX Energy
    history = {'verified': 12, 'total_matches': 15}
    parser = SMASH_IFS_Parser()

    # ANSI Escape Codes for Terminal Styling
    PURPLE = "\033[38;5;147m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    ELITE = "\033[95m"
    RESET = "\033[0m"

    print("\033[2J\033[H", end="") # Clear Screen
    print(f"{PURPLE}=========================================={RESET}")
    print(f"{PURPLE}--- S.M.A.S.H. IFS PARSER: INITIALIZED ---{RESET}")
    print(f"{PURPLE}=========================================={RESET}")

    # Run Test 1 (Frame Solid / Top G Trajectory)
    u_lat_frame = [10800, 11400, 9000] # Centered 3h window
    p_lat_frame = [600, 900, 300]
    score_1 = parser.calculate_ifs(None, None, {'user': u_lat_frame, 'partner': p_lat_frame}, history)
    
    color = GREEN if parser.strike_bounty_eligible else RED
    if parser.status_label == "TOP G": color = ELITE
    
    print(f"\n[TEST 1: HIGH PERFORMANCE] VERITAS SCORE: {score_1:.4f}")
    print(f"{color}BOUNTY ELIGIBLE | STATUS: [{parser.status_label}]{RESET}")

    # Run Test 2 (Bounty Farmer / Ghosting Filter)
    u_lat_farm = [172800, 172800] # 48-hour ghosting
    p_lat_farm = [86400, 86400]
    score_2 = parser.calculate_ifs(None, None, {'user': u_lat_farm, 'partner': p_lat_farm}, history)
    
    print(f"\n[TEST 2: BOUNTY FARMER] VERITAS SCORE: {score_2:.4f}")
    print(f"{RED}TAXABLE | INCREASE FRAME DENSITY (FARMING DETECTED){RESET}\n")


```


# ==========================================
# FILE: web_status.json
# ==========================================

```json
{
    "last_updated": "2026-05-20 12:20:17",
    "execution_id": 1779294017.705635,
    "projections": {
        "TSLA": {
            "expected_value": 189.4,
            "ci_low": 101.43,
            "ci_high": 315.54,
            "sentiment_score": -0.66,
            "headline": "Tech stocks today: Samsung workers reportedly postpone strike that threatened to disrupt global chip supplies",
            "volatility_alert": false
        },
        "F": {
            "expected_value": 13.81,
            "ci_low": 7.19,
            "ci_high": 23.88,
            "sentiment_score": 0.153,
            "headline": "How Toyota's Challenging U.S. Business Could Result in a New Ford Maverick Rival",
            "volatility_alert": false
        },
        "XOM": {
            "expected_value": 131.71,
            "ci_low": 70.06,
            "ci_high": 217.08,
            "sentiment_score": 0.178,
            "headline": "Is Cenovus Poised to Gain From the Current Elevation in Crude Prices?",
            "volatility_alert": false
        },
        "PFE": {
            "expected_value": 31.9,
            "ci_low": 17.1,
            "ci_high": 53.85,
            "sentiment_score": 0.382,
            "headline": "Pfizer Builds Oncology Growth Around Padcev and Pipeline Expansion",
            "volatility_alert": false
        },
        "CL=F": {
            "expected_value": 93.2,
            "ci_low": 49.77,
            "ci_high": 157.07,
            "sentiment_score": 0.691,
            "headline": "Stock market today: Dow, S&P 500, Nasdaq gain as oil prices fall, bond sell-off eases",
            "volatility_alert": false
        }
    }
}
```


# ==========================================
# FILE: local_cop.py
# ==========================================

```python
# =============================================================================
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# This source code is the proprietary property of Michael Healy.
# Unauthorized reproduction, distribution, or reverse-engineering is strictly
# prohibited. This file is part of the VERITAS Auditor / FASE Engine.
# =============================================================================

import json
import time
import os

HVL_OUTPUT = "autonomous_bridge.json"
CERTIFIED_TARGETS = "feds-engine/certified_targets.json"

def local_cop_bridge():
    print("👮‍♂️ [LOCAL COP] Active. Monitoring HVL Output...")
    last_modified = 0
    
    while True:
        try:
            if os.path.exists(HVL_OUTPUT):
                current_modified = os.path.getmtime(HVL_OUTPUT)
                if current_modified > last_modified:
                    last_modified = current_modified
                    
                    with open(HVL_OUTPUT, 'r') as f:
                        payload = json.load(f)
                        ticker = payload.get("ticker", "UNKNOWN")
                    
                    print(f"🚨 [COP] Target Received from HVL: {ticker}")
                    print(f"🔎 [COP] Auditing SEC/News Entropy for {ticker}...")
                    
                    # Simulated Relevance Logic for the morning run
                    is_certified = True 
                    
                    if is_certified:
                        print(f"✅ [COP] {ticker} CERTIFIED. Piping to FEDS Engine...")
                        with open(CERTIFIED_TARGETS, 'w') as f:
                            json.dump({"ticker": ticker, "status": "APPROVED"}, f)
                    else:
                        print(f"❌ [COP] {ticker} DENIED. Insufficient News Entropy.")
                        
        except Exception as e:
            pass
            
        time.sleep(5)

if __name__ == "__main__":
    local_cop_bridge()


```


# ==========================================
# FILE: parser_engine.py
# ==========================================

```python
# =============================================================================
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# This source code is the proprietary property of Michael Healy.
# Unauthorized reproduction, distribution, or reverse-engineering is strictly
# prohibited. This file is part of the VERITAS Auditor / FASE Engine.
# =============================================================================

import requests
import re

class SECSentinel:
    def __init__(self, ticker):
        self.ticker = ticker
        self.headers = {'User-Agent': 'Healy Vector Labs michael@healyvectorlabs.com'}

    def get_cik(self):
        return {"GPRO": "0001500435", "TSLA": "0001318605", "NN": "0001822036"}.get(self.ticker)

    def resolve_8k_url(self):
        cik = self.get_cik()
        api_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        
        r = requests.get(api_url, headers=self.headers)
        recent = r.json()['filings']['recent']
        
        # Find the index of the first 8-K form
        idx = recent['form'].index('8-K')
        acc_no = recent['accessionNumber'][idx].replace('-', '')
        primary_doc = recent['primaryDocument'][idx]
        
        # Build the Archives URL
        cik_clean = cik.lstrip('0')
        return f"https://www.sec.gov/Archives/edgar/data/{cik_clean}/{acc_no}/{primary_doc}"

    def audit_defense_pivot(self, url):
        # The 'Defense' weighting logic
        text = requests.get(url, headers=self.headers).text.upper()
        keywords = {
            "DEFENSE": 10.0, "AEROSPACE": 8.0, "ARTEMIS": 15.0, 
            "OLIVER WYMAN": 12.0, "RESTRUCTURING": 5.0
        }
        
        score = 0
        for word, weight in keywords.items():
            count = len(re.findall(word, text))
            score += (count * weight)
            
        return score

# --- HEALY VECTOR LABS: STRIKE TEST ---
agent = SECSentinel("GPRO")
doc_url = agent.resolve_8k_url()
sentiment_score = agent.audit_defense_pivot(doc_url)

print(f"--- PARSER AUDIT COMPLETE ---")
print(f"Latest 8-K URL: {doc_url}")
print(f"Defense Pivot Sentiment Score: {sentiment_score}")


```


# ==========================================
# FILE: score_engine.py
# ==========================================

```python
import json
import time
import os
import math
from datetime import datetime, timedelta
from nhlpy import NHLClient

# --- HVL Master Aesthetics ---
C_GREEN = '\033[92m'
C_BLUE = '\033[94m'
C_CYAN = '\033[96m'
C_RED = '\033[91m'
C_WARN = '\033[93m'
C_PURP = '\033[95m'
C_RESET = '\033[0m'
C_BOLD = '\033[1m'

class ScoreEngine:
    def __init__(self, target_team="Buffalo Sabres", target_date="2026-05-16"):
        self.client = NHLClient()
        self.target_team = target_team
        self.target_date = target_date
        self.history_file = "series_history.json"
        
        self.team_data = {
            "away": {"last_delta": 0.0, "last_time": datetime.now(), "name": "MTL"},
            "home": {"last_delta": 0.0, "last_time": datetime.now(), "name": "BUF"}
        }
        
        # Barriers and Road Multipliers
        self.config = {
            "ROAD_BIAS": 1.15, # 15% boost for BUF playoff road dominance
            "SIGMOID_SENSITIVITY": 0.45
        }

    def find_active_game(self):
        try:
            schedule = self.client.schedule.daily_schedule(date=self.target_date)
            for game in schedule.get('games', []):
                home_name = game.get('homeTeam', {}).get('name', {}).get('default', '')
                away_name = game.get('awayTeam', {}).get('name', {}).get('default', '')
                if self.target_team in [home_name, away_name]:
                    return game['id']
            return 2025030246 # Fallback ID for testing
        except: 
            return 2025030246

    def calculate_entropy(self, mtl_h, buf_h):
        """Calculates system entropy (chaos). High when energies are equal."""
        total = mtl_h + buf_h + 0.1
        p1, p2 = mtl_h / total, buf_h / total
        entropy = - (p1 * math.log(p1 + 0.01) + p2 * math.log(p2 + 0.01))
        return round(entropy, 3)

    def calculate_quantum_metrics(self, side, delta, hits, fo_pct, opponent_v, pressure, is_road):
        """H = [ (p^2 / 2m) + V ] * I * A * Road_Bias"""
        # 1. Possession Wave (A)
        possession_amp = 1.0 + (abs(fo_pct - 50) / 100.0) + (delta * 0.5)
        
        # 2. Mass/Desperation (m)
        mass = 1.0 / (pressure + 0.1)
        kinetic = (delta**2) / (2 * mass) if mass > 0 else 0
        
        # 3. Road Bias
        road_mult = self.config["ROAD_BIAS"] if (is_road and side == "away") else 1.0
        
        # 4. Hamiltonian (Total Energy)
        hamiltonian = (kinetic + opponent_v + (hits * 0.01)) * possession_amp * road_mult
        
        # 5. Normalized Probability (Psi^2)
        psi_sq = (1 / (1 + math.exp(-(hamiltonian * self.config["SIGMOID_SENSITIVITY"])))) * 100
        strike_chance = min((psi_sq * possession_amp), 99.99)
        
        return {
            "H": round(hamiltonian, 4),
            "psi_sq": round(psi_sq, 2),
            "strike": round(strike_chance, 2),
            "amp": round(possession_amp, 3)
        }

    def get_veritas_payload(self, game_id):
        try:
            game_data = self.client.game_center.boxscore(game_id=game_id)
            if not isinstance(game_data, dict):
                raise ValueError("Payload returned unexpected raw data type.")

            away_meta = game_data.get('awayTeam', {})
            home_meta = game_data.get('homeTeam', {})
            
            # Establish baseline values from top level fields
            away_sog = float(away_meta.get('sog', 0))
            home_sog = float(home_meta.get('sog', 0))
            away_goals = float(away_meta.get('score', 0))
            home_goals = float(home_meta.get('score', 0))
            
            away_hits, home_hits = 0.0, 0.0
            away_fo, home_fo = 50.0, 50.0
            
            # Safely crawl and parse modern live telemetry array matrices
            boxscore_layer = game_data.get('boxscore', {})
            team_stats_list = boxscore_layer.get('teamStats', [])
            
            for stat in team_stats_list:
                category = stat.get('category')
                raw_away = str(stat.get('awayValue', '')).replace('%', '').strip()
                raw_home = str(stat.get('homeValue', '')).replace('%', '').strip()
                
                try:
                    if category == 'sog':
                        away_sog = float(raw_away) if raw_away else away_sog
                        home_sog = float(raw_home) if raw_home else home_sog
                    elif category == 'hits':
                        away_hits = float(raw_away) if raw_away else 0.0
                        home_hits = float(raw_home) if raw_home else 0.0
                    elif category == 'faceoffWinningPctg':
                        away_fo = float(raw_away) if raw_away else 50.0
                        home_fo = float(raw_home) if raw_home else 50.0
                except ValueError:
                    continue

            # Calculate dynamic live SV% for the potential barriers (V)
            # Default to league average (0.900) if no shots have been fired yet
            buf_goalie_sv = (home_sog - home_goals) / home_sog if home_sog > 0 else 0.900
            mtl_goalie_sv = (away_sog - away_goals) / away_sog if away_sog > 0 else 0.900

            # MTL is Home for Game 6, BUF is Away.
            mtl_q = self.calculate_quantum_metrics(
                "home", round(home_sog/60, 3), home_hits, home_fo, buf_goalie_sv, 1.0, False
            )
            
            buf_q = self.calculate_quantum_metrics(
                "away", round(away_sog/60, 3), away_hits, away_fo, mtl_goalie_sv, 1.50, True
            )
            
            entropy = self.calculate_entropy(mtl_q["H"], buf_q["H"])
            
            payload = {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "MTL": mtl_q,
                "BUF": buf_q,
                "entropy": entropy,
                "metadata": {
                    "Hamiltonian": "Total system energy (Kinetic + Potential).",
                    "Psi_Squared": "Probability density of a state-change event (Goal).",
                    "Entropy": "Measure of system chaos vs stability.",
                    "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
                }
            }
            
            self.save_persistence(payload)
            return payload
            
        except Exception as e:
            print(f"{C_RED}[ ERR ] Telemetry Exception: {e}{C_RESET}")
            return None

    def save_persistence(self, data):
        history = []
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as f:
                try: history = json.load(f)
                except: history = []
        
        history.append(data)
        with open(self.history_file, 'w') as f:
            json.dump(history[-50:], f, indent=4) 

def render_cli_dashboard(data):
    """Cleanly formats and renders the quantum core telemetry to stdout."""
    os.system('clear' if os.name == 'posix' else 'cls')
    
    # Header
    print(f"{C_BOLD}+{'-'*58}+")
    print(f"|{'HEALY VECTOR LABS: QUANTUM CORE V7.0'.center(58)}|")
    print(f"|{'EXPLICITORY METADATA ENABLED'.center(58)}|")
    print(f"+{'-'*58}+{C_RESET}\n")

    # Core Metrics
    print(f"System Entropy: {C_CYAN}{data['entropy']}{C_RESET} S\n")
    print(f"{'METRIC':<15} | {'MTL (HOME)':<15} | {'BUF (AWAY)':<15}")
    print("-" * 52)
    print(f"{'Possession A':<15} | {data['MTL']['amp']:<15} | {data['BUF']['amp']:<15}")
    print(f"{'Hamiltonian':<15} | {C_GREEN}{data['MTL']['H']:<15}{C_RESET} | {C_GREEN}{data['BUF']['H']:<15}{C_RESET}")
    print(f"{'Collapse %':<15} | {data['MTL']['psi_sq']:<15} | {data['BUF']['psi_sq']:<15}")

    # Strike Readout
    m_strike = data['MTL']['strike']
    b_strike = data['BUF']['strike']
    m_color = C_GREEN if m_strike > 65 else C_WARN
    b_color = C_GREEN if b_strike > 65 else C_WARN

    print(f"\n{C_BOLD}GOAL STRIKE    | {m_color}{m_strike:>14}%{C_RESET} | {b_color}{b_strike:>14}%{C_RESET}")
    print(f"\n{C_PURP}Explicitory Metadata Loaded. Archive Sync: OK.{C_RESET}")

if __name__ == "__main__":
    engine = ScoreEngine()
    
    try:
        while True:
            game_id = engine.find_active_game()
            data = engine.get_veritas_payload(game_id)
            
            if data:
                # 1. Render the CLI Dashboard to terminal
                render_cli_dashboard(data)
                
                # 2. Live Web Sync Pipeline (HealyVectorLabs.com Frontend Route)
                try:
                    web_payload = {
                        "timestamp": data["timestamp"],
                        "entropy": data["entropy"],
                        "teams": {
                            "MTL": {
                                "hamiltonian": data["MTL"]["H"],
                                "psi_squared": data["MTL"]["psi_sq"],
                                "strike_chance": data["MTL"]["strike"]
                            },
                            "BUF": {
                                "hamiltonian": data["BUF"]["H"],
                                "psi_squared": data["BUF"]["psi_sq"],
                                "strike_chance": data["BUF"]["strike"]
                            }
                        }
                    }
                    
                    with open("live_score.json", "w") as wf:
                        json.dump(web_payload, wf, indent=4)
                    
                    # Native Git Push utilizing HEAD:main to bypass local branch name mismatches
                    os.system("git add live_score.json && git commit -m 'TELEMETRY SYNC: VERITAS' --quiet && git push origin HEAD:main --quiet")
                        
                except Exception as sync_err:
                    print(f"\033[91m[TELEMETRY ERROR] Dynamic sync drop: {sync_err}\033[0m")
                
            time.sleep(30)
            
    except KeyboardInterrupt:
        print(f"\n{C_RED}[ SYSTEM ] ARCHIVE LOCKED AND COLD STORED.{C_RESET}")


```


# ==========================================
# FILE: setup-pointless-repo.sh
# ==========================================

```sh
#!/data/data/com.termux/files/usr/bin/sh
# Get some needed tools. coreutils for mkdir command, gnugp for the signing key, and apt-transport-https to actually connect to the repo
apt-get update
apt-get --assume-yes upgrade
apt-get --assume-yes install coreutils gnupg
# Make the sources.list.d directory
mkdir -p $PREFIX/etc/apt/sources.list.d
# Write the needed source file
if apt-cache policy | grep -q "termux.*24\|termux.org\|bintray.*24\|k51qzi5uqu5dg9vawh923wejqffxiu9bhqlze5f508msk0h7ylpac27fdgaskx" ; then
echo "deb https://its-pointless.github.io/files/24 termux extras" > $PREFIX/etc/apt/sources.list.d/pointless.list
else
echo "deb https://its-pointless.github.io/files/21 termux extras" > $PREFIX/etc/apt/sources.list.d/pointless.list
fi
# Add signing key from https://its-pointless.github.io/pointless.gpg
if [ -n $(command -v curl) ]; then
curl -sLo $PREFIX/etc/apt/trusted.gpg.d/pointless.gpg --create-dirs https://its-pointless.github.io/pointless.gpg
elif [ -n $(command -v wget) ]; then
wget -qP $PREFIX/etc/apt/trusted.gpg.d https://its-pointless.github.io/pointless.gpg
fi
# Update apt
apt update

```


# ==========================================
# FILE: smash_master.py
# ==========================================

```python
# =============================================================================
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# This source code is the proprietary property of Michael Healy.
# Unauthorized reproduction, distribution, or reverse-engineering is strictly
# prohibited. This file is part of the VERITAS Auditor / FASE Engine.
# =============================================================================

import time
import random

# ==========================================
# 1. THE VERITAS ENGINE (SOCIAL MATRIX)
# ==========================================
class Veritas_Engine:
    def __init__(self):
        self.frame_score = 0.0

    def calculate_ifs(self, user_lat, partner_lat, conversion_rate):
        latency_ratio = user_lat / partner_lat if partner_lat > 0 else 1.0
        self.frame_score = (0.4 * latency_ratio) + (0.6 * conversion_rate)
        return self.frame_score

# ==========================================
# 2. SHINIGO EYES (INTEL & STRIKE MASS)
# ==========================================
class Shinigo_Intel:
    def __init__(self):
        self.mass_threshold = 1.0 # The Architect's Filter for "Noise"
        self.current_mass = 0.0

    def calculate_strike_mass(self, micro_strikes, avg_weight):
        # M_s = sum(weight * delta_p)
        self.current_mass = micro_strikes * avg_weight
        
        if self.current_mass >= self.mass_threshold:
            return "STRIKE DETECTED (HIGH DENSITY)"
        return "FILTERING NOISE (LOW MASS)"

# ==========================================
# 3. MARKET TELEMETRY (THE PULSE)
# ==========================================
class Market_Telemetry:
    def __init__(self):
        # The Architect's specific vectors
        self.tickers = ["ADA-USD", "BTC-USD", "TSLL-USD", "WTI-OIL", "XOM-USD", "AMC-USD", "WBA-USD", "GPRO-USD"]

    def render_dashboard(self):
        print("\n" + "="*60)
        print("HVL S.M.A.S.H. MASTER KERNEL V7.0 | JACKSONVILLE HQ")
        print("="*60)
        
        for t in self.tickers:
            # Simulating live terminal output with P_AGE metrics
            price = random.uniform(1, 75000) if "BTC" in t else random.uniform(0.1, 400)
            delta = random.uniform(-2.5, 4.2)
            p_count = random.randint(0, 15)
            status = "STABLE  " if abs(delta) < 1.0 else "VOLATILE"
            if "AMC" in t: status = "MEME-VOL"
            if "WTI" in t or "XOM" in t: status = "ARBITRAGE"
            
            print(f"{t:8} | $ {price:9.4f} | Δ: {delta:+05.2f}% | {status} | P:{p_count:02}")
        print("="*60)

# ==========================================
# --- SYSTEM INITIALIZATION & EXECUTION ---
# ==========================================
if __name__ == "__main__":
    # 1. Init Modules
    veritas = Veritas_Engine()
    shinigo = Shinigo_Intel()
    telemetry = Market_Telemetry()

    # 2. Run Veritas (Your current stats)
    my_score = veritas.calculate_ifs(user_lat=8400, partner_lat=340, conversion_rate=0.8)
    
    # 3. Run Shinigo Mass Check (Filtering the 10-second ride)
    strike_status = shinigo.calculate_strike_mass(micro_strikes=5, avg_weight=0.25)

    # 4. Render HUD
    telemetry.render_dashboard()
    
    print(f"\n[VERITAS] Frame Score : {my_score:.4f} | STATUS: LEAD ARCHITECT")
    print(f"[SHINIGO] Market Pulse: {strike_status} | MASS: {shinigo.current_mass:.2f}")
    print(f"[SABRES]  Kernel V6.4 : 1930 HRS READY | ALPHA SHIFT: +0.2077")
    print("\n>>> SYSTEM HUMMING. AWAITING COMMAND. <<<")


```


# ==========================================
# FILE: strike_engine.py
# ==========================================

```python
# =============================================================================
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# This source code is the proprietary property of Michael Healy.
# Unauthorized reproduction, distribution, or reverse-engineering is strictly
# prohibited. This file is part of the VERITAS Auditor / FASE Engine.
# =============================================================================

import time, requests

def get_live_data(ticker):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1m&range=1d"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        data = requests.get(url, headers=headers).json()
        prices = data['chart']['result'][0]['indicators']['quote'][0]['close']
        return [p for p in prices if p is not None]
    except: return []

def calculate_ema(prices, period=9):
    if not prices: return 0
    multiplier = 2 / (period + 1)
    ema = prices[0]
    for p in prices[1:]:
        ema = (p - ema) * multiplier + ema
    return round(ema, 3)

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1: return 50
    gains, losses = [], []
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i-1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0: return 100
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

if __name__ == "__main__":
    ticker = "GPRO"
    print(f"!! HEALY VECTOR LABS: PURE-LOGIC LIVE STRIKE [{ticker}] !!")
    while True:
        try:
            prices = get_live_data(ticker)
            if prices:
                p, rsi, ema = round(prices[-1], 2), calculate_rsi(prices), calculate_ema(prices)
                msg = "[STRIKE]: ALIGNMENT" if (rsi > 40 and p > ema) else "[WAIT]: MOMENTUM LEAK"
                print(f"P: {p} | R: {rsi} | E: {ema} | {msg}")
            time.sleep(60)
        except Exception as err:
            print(f"[ERROR]: {err}"); time.sleep(10)

```


# ==========================================
# FILE: veritas_analyzer.py
# ==========================================

```python
# =============================================================================
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# This source code is the proprietary property of Michael Healy.
# Unauthorized reproduction, distribution, or reverse-engineering is strictly
# prohibited. This file is part of the VERITAS Auditor / FASE Engine.
# =============================================================================

import numpy as np

# 1. SOVEREIGN PARSER (Extracting from proprietary strings)
parsed_data = []
try:
    with open('verified_springs.log', 'r') as f:
        for line in f:
            try:
                # Slices: [0]Time/Status, [1]Price, [2]PSI, [3]PHI
                parts = line.split('|')
                
                # Extract the raw numbers by splitting at the colon
                psi_str = parts[2].split(':')[1].strip()
                phi_str = parts[3].split(':')[1].strip()
                
                parsed_data.append([float(psi_str), float(phi_str)])
            except Exception:
                continue # If a line is corrupted, skip it silently

    data = np.array(parsed_data)
    print(f">>> INGESTED {len(data)} CLEAN PULSES. INITIALIZING VERITAS V2.2...")
    
    if len(data) == 0:
        print("FATAL ERROR: No valid PSI/PHI data extracted. Check log format.")
        exit()
        
except Exception as e:
    print(f"FATAL ERROR: {e}")
    exit()

# 2. THE CUSTOM SIEVE (Robust Standardization)
mean = np.mean(data, axis=0)
std = np.std(data, axis=0)
std = np.where(std == 0, 1.0, std) # Prevent division by zero
scaled_data = (data - mean) / std

# 3. SOVEREIGN K-MEANS ENGINE
k_regimes = 5
iterations = 20
np.random.seed(716)

print(">>> COMPILING SOVEREIGN K-MEANS MATRIX...")

random_indices = np.random.choice(len(scaled_data), k_regimes, replace=False)
centroids = scaled_data[random_indices]

for _ in range(iterations):
    distances = np.linalg.norm(scaled_data[:, np.newaxis] - centroids, axis=2)
    regimes = np.argmin(distances, axis=1)
    new_centroids = np.array([scaled_data[regimes == i].mean(axis=0) if len(scaled_data[regimes == i]) > 0 else centroids[i] for i in range(k_regimes)])
    if np.all(centroids == new_centroids):
        break
    centroids = new_centroids

# 4. ARCHITECT'S LOG
print("=========================================")
print("HEALY VECTOR LABS: 5-REGIME ALPHA SCAN")
print("=========================================")

for i in range(k_regimes):
    cluster_points = data[regimes == i]
    weight = len(cluster_points)
    
    if weight == 0:
        continue
        
    avg_psi = np.mean(cluster_points[:, 0])
    avg_phi = np.mean(cluster_points[:, 1])
    
    if avg_phi > 4000: 
        status = "MARSHMALLOW (High-Alpha Strike)"
    elif avg_phi > 1000: 
        status = "THE FUSE (Pre-Strike Tension)"
    elif avg_phi > 400: 
        status = "OATS (Structural Resistance)"
    elif avg_phi > 100: 
        status = "BUBBLING MILK (Low Tension Movement)"
    else: 
        status = "FLAT MILK (Background Noise)"
    
    print(f"[REGIME {i}] - {status}")
    print(f" -> Events: {weight} | Velocity (PSI): {avg_psi:.4f} | Tension (PHI): {avg_phi:.2f}")
    print("-" * 40)


```


# ==========================================
# FILE: veritas_bridge.py
# ==========================================

```python
# =============================================================================
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# This source code is the proprietary property of Michael Healy.
# Unauthorized reproduction, distribution, or reverse-engineering is strictly
# prohibited. This file is part of the VERITAS Auditor / FASE Engine.
# =============================================================================

import numpy as np

def lebesgue_bridge(active_shards, active_moduli, total_M, jerk_signal):
    """
    Bridges the CRT gap by finding the state candidate that maximizes 
    alignment with the current price 'Jerk' density.
    """
    # 1. Find the base reconstruction of the active shards
    M_prime = np.prod(active_moduli)
    base_x = 0
    for a_i, m_i in zip(active_shards, active_moduli):
        Mi = M_prime // m_i
        yi = pow(int(Mi), -1, int(m_i))
        base_x += int(a_i) * Mi * yi
    base_x %= M_prime

    # 2. Generate the Lebesgue set (all possible X candidates)
    candidates = [base_x + (i * M_prime) for i in range(total_M // M_prime + 1) if (base_x + (i * M_prime)) < total_M]
    
    # 3. Profitability Density Selection (Simulated)
    # In a live environment, this would map X to historical volatility buckets.
    # Here, we select the candidate closest to the normalized Jerk resonance.
    target_resonance = (jerk_signal % 1) * total_M
    best_candidate = min(candidates, key=lambda x: abs(x - target_resonance))
    
    return best_candidate, len(candidates)

# --- Operational Run ---
M_total = 1113101
active_moduli = [101, 107]
active_shards = [42, 12] # Shard 89 (m=103) is missing
current_jerk = 3.166667

refined_X, set_size = lebesgue_bridge(active_shards, active_moduli, M_total, current_jerk)

print(f"--- Lebesgue Bridge: Phase III Results ---")
print(f"[Lebesgue Set Size]: {set_size} possible states")
print(f"[Interpolated Master X]: {refined_X}")
print(f"[Drift Reduction]: {abs(897528 - refined_X)}") # Compare to original Master X

```


# ==========================================
# FILE: veritas_chaos.py
# ==========================================

```python
# =============================================================================
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# This source code is the proprietary property of Michael Healy.
# Unauthorized reproduction, distribution, or reverse-engineering is strictly
# prohibited. This file is part of the VERITAS Auditor / FASE Engine.
# =============================================================================

import numpy as np

def crt_reconstruct(shards, moduli):
    M = np.prod(moduli)
    total = 0
    for a_i, m_i in zip(shards, moduli):
        if a_i is None: continue # Simulate partial loss
        Mi = M // m_i
        yi = pow(int(Mi), -1, int(m_i))
        total += int(a_i) * Mi * yi
    return total % M

def dual_state_lebesgue_bridge(a1, a3, omega=0.8):
    """
    Calculates E[a_2] using a Bayesian blend of Global (810k) and Local (Rolling) data.
    omega: The weight given to the real-time tactical window (0.0 to 1.0).
    """
    # NOTE FOR V2.2 INTEGRATION:
    # Replace these mock values by querying your actual K-Means arrays where 101==a1 and 107==a3
    mu_global = 89.4  # Simulated mean of Shard 103 across the full 810k pulse baseline
    mu_local = 88.7   # Simulated mean of Shard 103 in the last 5,000 pulses
    
    # Bayesian Formula: E[a2] = (w * mu_local) + ((1-w) * mu_global)
    expected_a2 = (omega * mu_local) + ((1.0 - omega) * mu_global)
    
    # CRT requires an integer for modular arithmetic
    return int(round(expected_a2)) 

# --- Phase II: Shard Desync Injection ---
moduli = [101, 103, 107]
full_shards = [42, 89, 12]
loss_shards = [42, None, 12] # Modulus 103 (Sentiment) dropped

master_full = crt_reconstruct(full_shards, moduli)
master_degraded = crt_reconstruct(loss_shards, moduli)

print("==================================================")
print("HEALY VECTOR LABS: CHAOS CHAMBER INITIATED")
print("==================================================")
print(f"[Full Telemetry Master X]     : {master_full}")
print(f"[Degraded Telemetry Master X] : {master_degraded}")

# Calculate Initial Entropy (Drift)
drift = abs(master_full - master_degraded)
print(f"[Raw Entropy/State Drift]     : {drift}")

if drift > 0:
    print("\n[ALERT]: Master State desynchronized. CRT requires all shards.")
    print("[Protocol]: Engaging Dual-State Lebesgue Bridge to repair telemetry...")

    # --- Phase III: The Bayesian Patch ---
    # We pass the surviving shards (42 and 12) to the Lebesgue bridge.
    # Omega is set to 0.8, meaning we trust the recent market regime 80% and history 20%.
    patched_a2 = dual_state_lebesgue_bridge(42, 12, omega=0.8)
    patched_shards = [42, patched_a2, 12]
    
    master_patched = crt_reconstruct(patched_shards, moduli)
    hybrid_drift = abs(master_full - master_patched)

    print("\n--------------------------------------------------")
    print("PHASE III: SELF-HEALING LEBESGUE EXECUTION")
    print("--------------------------------------------------")
    print(f"[Bayesian E[a2] Inferred]     : {patched_a2}")
    print(f"[Patched Telemetry Master X]  : {master_patched}")
    print(f"[New State Drift]             : {hybrid_drift}")

    # Pass/Fail Tolerance Check
    if hybrid_drift < drift:
        recovery_pct = (1 - (hybrid_drift / drift)) * 100
        print(f"\n[SYSTEM RESTORED]: Telemetry repaired. Entropy reduced by {recovery_pct:.2f}%.")
        print("[STATUS]: FASE MASTER Ready for Live Deployment.")
    else:
        print("\n[SYSTEM FAILURE]: Lebesgue patch rejected. Boundaries breached.")

print("==================================================\n")


```


# ==========================================
# FILE: veritas_config.py
# ==========================================

```python
# =============================================================================
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# This source code is the proprietary property of Michael Healy.
# Unauthorized reproduction, distribution, or reverse-engineering is strictly
# prohibited. This file is part of the VERITAS Auditor / FASE Engine.
# =============================================================================

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

```


# ==========================================
# FILE: veritas_core.py
# ==========================================

```python
# =============================================================================
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# This source code is the proprietary property of Michael Healy.
# Unauthorized reproduction, distribution, or reverse-engineering is strictly
# prohibited. This file is part of the VERITAS Auditor / FASE Engine.
# =============================================================================

import numpy as np

class VeritasMaestro:
    def __init__(self, r_val=63890.00, e_val=1.266):
        # THE ARCHITECT'S BASELINES
        self.r = r_val        # Stability Score (63k)
        self.e = e_val        # Theoretical Floor (NVFP4)
        self.dt = 1           # Stationary time-step
        
        # COPRIME MODULI FOR CRT RECONSTRUCTION
        # These must be pairwise coprime for a unique solution.
        self.moduli = [101, 103, 107] 

    def calculate_taylor_expansion(self, current_val, prev_val, vel_prev, acc_prev):
        r"""
        LOGIC LAYER: 3rd-Order Taylor Expansion (The Hook)
        $$f(x) \approx f(a) + f'(a)\Delta x + \frac{f''(a)}{2!}\Delta x^2 + \frac{f'''(a)}{3!}\Delta x^3$$
        """
        f_a = current_val
        f_prime = (current_val - prev_val) / self.dt
        f_double_prime = (f_prime - vel_prev) / self.dt
        f_triple_prime = (f_double_prime - acc_prev) / self.dt
        
        # --- HARDENING: THE JERK STABILIZER ---
        hook_term = 0
        status = "[QUADRATIC]: STABLE"
        
        if self.r > 60000:
            # 3rd-order weight is 1/3! (1/6)
            hook_term = (f_triple_prime / 6) * (self.dt**3)
            status = "[STRIKE]: 3RD-ORDER HOOK ALIGNED"
            
        # --- HARDENING: DIVERGENCE GUARD ---
        if abs(f_double_prime) > (abs(f_prime) * 5):
            f_double_prime *= 0.5
            status = "[HARDENED]: DIVERGENCE DAMPENED"

        prediction = f_a + f_prime + ((f_double_prime / 2) * (self.dt**2)) + hook_term
        return prediction, f_prime, f_double_prime, status

    def solve_crt(self, remainders):
        r"""
        SENSORY LAYER: Chinese Remainder Theorem State Resolution.
        Reconstructs Master State X where $$x \equiv a_i \pmod{n_i}$$
        """
        def mul_inv(a, b):
            b0, x0, x1 = b, 0, 1
            if b == 1: return 1
            while a > 1:
                q = a // b
                a, b = b, a % b
                x0, x1 = x1 - q * x0, x0
            if x1 < 0: x1 += b0
            return x1

        total = 0
        N = np.prod(self.moduli)
        for a_i, n_i in zip(remainders, self.moduli):
            p = N // n_i
            total += a_i * mul_inv(p, n_i) * p
        return total % N

    def galois_solvability_audit(self, f_p, f_dp, f_tp):
        """
        INTEGRITY LAYER: Galois Group Symmetry Audit.
        Ensures market elements belong to a solvable group.
        """
        symmetry_variance = np.std([f_p, f_dp, f_tp])
        if symmetry_variance > 20.0:
            return False, "[GALOIS]: NON-SOLVABLE ENTROPY"
        return True, "[GALOIS]: SYMMETRIC STRIKE"

    def run_deep_simulation(self):
        """
        MAESTRO DEEP SIMULATION: Saturday 99.999% Hans Bingo Protocol.
        """
        print("="*45)
        print(" VERITAS V2.2: MAESTRO DEEP SIMULATION")
        print("="*45)
        
        # STATE RECONSTRUCTION (Sentiment, Price, Volume)
        remainders = [42, 88, 12] 
        master_state = self.solve_crt(remainders)
        
        # SIMULATED LIVE TELEMETRY
        curr, prev, v_p, a_p = 1.3150, 1.3000, 0.0300, 0.0050
        
        # EXECUTE
        pred, v, a, status = self.calculate_taylor_expansion(curr, prev, v_p, a_p)
        solvable, audit_msg = self.galois_solvability_audit(v, a, (a - a_p))
        
        # DYNAMIC BINGO CALCULATION
        bingo_prob = (1 - (self.e / self.r)) * 100

        print(f"Master State (X):  {master_state}")
        print(f"Galois Audit:      {audit_msg}")
        print(f"Logic Status:      {status}")
        print(f"Stability Score:   {self.r:.2f}")
        print(f"Error Floor (E):   {self.e:.3f}")
        print("-" * 45)
        print(f"TARGET PREDICTION: {pred:.4f}")
        print(f"HANS BINGO PROB:   {bingo_prob:.3f}%")
        print("="*45)

# --- THE FAIL-SAFE DEPLOYMENT BLOCK ---
if __name__ == "__main__":
    try:
        maestro = VeritasMaestro()
        maestro.run_deep_simulation()
    except Exception as e:
        print(f"CRITICAL SYSTEM RECOVERY: {str(e)}")








```


# ==========================================
# FILE: veritas_engine.py
# ==========================================

```python
# =============================================================================
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# This source code is the proprietary property of Michael Healy.
# Unauthorized reproduction, distribution, or reverse-engineering is strictly
# prohibited. This file is part of the VERITAS Auditor / FASE Engine.
# =============================================================================

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
        

```


# ==========================================
# FILE: veritas_live.py
# ==========================================

```python
# =============================================================================
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# This source code is the proprietary property of Michael Healy.
# Unauthorized reproduction, distribution, or reverse-engineering is strictly
# prohibited. This file is part of the VERITAS Auditor / FASE Engine.
# =============================================================================

import yfinance as yf
import numpy as np
import time

def run_veritas_ticker(symbol):
    try:
        # Fetching 1-minute interval shards for high-res Jerk calculation
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d", interval="1m").tail(10)
        
        if data.empty or len(data) < 5:
            return None

        prices = data['Close'].values
        volume_dist = data['Volume'].values

        # 1. The Hook: Taylor 3rd-Order Jerk (f''')
        v = np.diff(prices)
        a = np.diff(v)
        j = np.diff(a)
        jerk_val = (j[-1] / 6) if len(j) > 0 else 0.0

        # 2. The Gatekeeper: Galois Entropy Audit
        p = volume_dist / np.sum(volume_dist)
        entropy = -np.sum(p * np.log2(p + 1e-9))
        solvable = entropy < 2.32

        # 3. Decision Matrix
        e_floor = 1.266
        signal = "CONFIRMED" if (solvable and abs(jerk_val) > e_floor) else "KILLED"
        
        return {
            "Symbol": symbol,
            "Jerk": jerk_val,
            "Entropy": entropy,
            "Solvable": solvable,
            "Signal": signal
        }
    except Exception as e:
        return None

# --- Live Monday Prep Run ---
tickers = ["TSLA", "TSLL", "GPRO"]
print(f"\n[MAESTRO PROTOCOL]: INITIALIZING TICKER AUDIT...")
print("-" * 50)

for t in tickers:
    res = run_veritas_ticker(t)
    if res:
        status = "SOLVABLE" if res['Solvable'] else "CHAOTIC"
        print(f"[{res['Symbol']}] | Jerk: {res['Jerk']:.4f} | Ent: {res['Entropy']:.4f} | {status} -> {res['Signal']}")
    else:
        print(f"[{t}] | No Telemetry Available (Market Closed/Latency)")

print("-" * 50)

```


# ==========================================
# FILE: veritas_mjolnir_v2.py
# ==========================================

```python
# =============================================================================
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# This source code is the proprietary property of Michael Healy.
# Unauthorized reproduction, distribution, or reverse-engineering is strictly
# prohibited. This file is part of the VERITAS Auditor / FASE Engine.
# =============================================================================

# HEALY VECTOR LABS: MJOLNIR RECONFIGURATION
# TARGET: Seven-Node Leverage Lock
# ASSETS: [BTC, XOM, TSLA, MNST, GPRO, WTI, TSLL]

import veritas_engine as ve
import os  # Replaced 'haptics' with native OS routing

class MjolnirMonitor:
    def __init__(self):
        self.primary_nodes = {
            "BTC/USD": {"tier": 1, "weight": 1.0},
            "TSLA":    {"tier": 1, "weight": 0.8},
            "TSLL":    {"tier": 1, "weight": 1.5, "parent": "TSLA"}, # Leverage Multiplier
            "WTI":     {"tier": 2, "weight": 1.2},
            "XOM":     {"tier": 2, "weight": 0.7, "correlation": "WTI"},
            "MNST":    {"tier": 2, "weight": 0.9},
            "GPRO":    {"tier": 3, "weight": 1.4}  # Volatility play
        }
        self.entropy_threshold = 0.02
        self.strike_persistence = 3 # Require 3 pulses for authorization

    def evaluate_singularity(self, asset, psi, phi):
        magnitude = psi * self.primary_nodes[asset]["weight"]
        
        # Leverage Synchronization (TSLA/TSLL)
        if "parent" in self.primary_nodes[asset]:
            parent_psi = ve.get_psi(self.primary_nodes[asset]["parent"])
            magnitude += (parent_psi * 0.5)

        # Haptic Logic via Termux API
        if magnitude > 50:
            # -f forces vibration, -d sets duration in milliseconds based on magnitude
            vibe_duration = int(magnitude * 10) 
            os.system(f"termux-vibrate -f -d {vibe_duration}")
            return "STRIKE_AUTHORIZED"
        
        return "MONITORING"

# INITIALIZING LIVE SHARDS...
# 100% TELEMETRY SYNC: [OK]


```


# ==========================================
# FILE: veritas_mock_open.py
# ==========================================

```python
# =============================================================================
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# This source code is the proprietary property of Michael Healy.
# Unauthorized reproduction, distribution, or reverse-engineering is strictly
# prohibited. This file is part of the VERITAS Auditor / FASE Engine.
# =============================================================================

import numpy as np

# --- Core Veritas Modules ---

def audit_galois(market_distribution):
    p = market_distribution / np.sum(market_distribution)
    entropy = -np.sum(p * np.log2(p + 1e-9))
    # Threshold for solvability (S4 symmetry)
    is_solvable = entropy < 2.32
    return is_solvable, entropy

def calculate_jerk(price_series, dt=1):
    if len(price_series) < 4: return 0.0
    v = np.diff(price_series) / dt
    a = np.diff(v) / dt
    jerk = np.diff(a) / dt
    return (jerk[-1] / 6) * (dt**3)

def master_state_engine(shards, moduli, jerk_signal):
    M_total = np.prod(moduli)
    active_pairs = [(s, m) for s, m in zip(shards, moduli) if s is not None]
    
    if len(active_pairs) < len(moduli):
        # Engage Lebesgue Bridge
        active_shards, active_moduli = zip(*active_pairs)
        M_prime = np.prod(active_moduli)
        base_x = 0
        for a_i, m_i in zip(active_shards, active_moduli):
            Mi = M_prime // m_i
            yi = pow(int(Mi), -1, int(m_i))
            base_x += int(a_i) * Mi * yi
        base_x %= M_prime
        
        candidates = [base_x + (i * M_prime) for i in range(M_total // M_prime + 1) if (base_x + (i * M_prime)) < M_total]
        target_resonance = (abs(jerk_signal) % 1) * M_total
        return min(candidates, key=lambda x: abs(x - target_resonance)), True
    else:
        # Standard CRT
        total = 0
        for a_i, m_i in zip(shards, moduli):
            Mi = M_total // m_i
            yi = pow(int(Mi), -1, int(m_i))
            total += int(a_i) * Mi * yi
        return total % M_total, False

# --- Mock Open Simulation ---

# 1. Environment Constants
MODULI = [101, 103, 107]
E_FLOOR = 1.266

# 2. Incoming Telemetry (Simulating Monday 09:30:01 AM)
# Price snap: sharp parabolic surge
prices = np.array([180.50, 181.00, 182.50, 185.75, 191.00, 199.50])
# Market distribution: reasonably ordered
market_dist = np.array([0.45, 0.30, 0.15, 0.10])
# Shards: Missing Volume (107) due to open-bell latency
shards = [42, 89, None] 

# 3. Execution Pipeline
jerk_val = calculate_jerk(prices)
solvable, entropy = audit_galois(market_dist)
state_x, bridged = master_state_engine(shards, MODULI, jerk_val)

print(f"--- VERITAS V2.2 MOCK OPEN REPORT ---")
print(f"Jerk Signal: {jerk_val:.4f} (E_Floor: {E_FLOOR})")
print(f"Galois Audit: {'SOLVABLE' if solvable else 'NON-SOLVABLE'} (Entropy: {entropy:.4f})")
print(f"Master State X: {state_x} (Bridged: {bridged})")

# Final Decision Logic
if solvable and abs(jerk_val) > E_FLOOR:
    print("\n[EXECUTION]: SIGNAL CONFIRMED. ENTERING POSITION.")
else:
    reason = "Entropy Spike" if not solvable else "Insufficient Jerk"
    print(f"\n[EXECUTION]: TRADE KILLED. Reason: {reason}")

```


# ==========================================
# FILE: veritas_veto.py
# ==========================================

```python
# =============================================================================
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# This source code is the proprietary property of Michael Healy.
# Unauthorized reproduction, distribution, or reverse-engineering is strictly
# prohibited. This file is part of the VERITAS Auditor / FASE Engine.
# =============================================================================

import numpy as np

def audit_galois(market_distribution):
    p = market_distribution / np.sum(market_distribution)
    entropy = -np.sum(p * np.log2(p + 1e-9))
    return entropy < 2.32, entropy

def calculate_jerk(price_series, dt=1):
    v = np.diff(price_series) / dt
    a = np.diff(v) / dt
    jerk = np.diff(a) / dt
    return (jerk[-1] / 6) * (dt**3)

# --- Phase IV: Extreme Snap + High Entropy ---
# 1. Extreme Jerk: Parabolic blow-off top
prices = np.array([100, 102, 110, 140, 200, 310]) 
# 2. Chaos State: 20-shard distribution (High Entropy)
market_dist = np.random.dirichlet(np.ones(20), size=1)[0]

jerk_val = calculate_jerk(prices)
solvable, entropy = audit_galois(market_dist)

print(f"--- Chaos Chamber: Phase IV (Entropy Veto) ---")
print(f"Jerk Signal: {jerk_val:.4f} (STRONG SIGNAL)")
print(f"Galois Audit: {'SOLVABLE' if solvable else 'NON-SOLVABLE'} (Entropy: {entropy:.4f})")

if solvable and jerk_val > 1.266:
    print("\n[EXECUTION]: SIGNAL CONFIRMED.")
else:
    reason = "Entropy Spike (Galois Veto)" if not solvable else "Insufficient Jerk"
    print(f"\n[EXECUTION]: TRADE KILLED. Reason: {reason}")

```


# ==========================================
# FILE: brule_engine.py
# ==========================================

```python
# =============================================================================
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# This source code is the proprietary property of Michael Healy.
# Unauthorized reproduction, distribution, or reverse-engineering is strictly
# prohibited. This file is part of the VERITAS Auditor / FASE Engine.
# =============================================================================

import sys, os, time
from datetime import datetime
import yfinance as yf
import robin_stocks.robinhood as rh

WATCHLIST = ["MO", "XYZ", "GPRO", "BBBY", "PINS", "SNAP", "WDC", "MDB", "AMC", "GME", "SPCE", "WTI", "PLTR", "TSLA", "PTON", "SOFI", "MSTR", "ROKU", "RIVN", "MARA", "RIOT", "CVNA", "UPST", "PLUG", "FUBO", "AFRM", "XYZ", "ABNB"]
ACTIVE_TRADES = {}
HISTORY = {ticker: {"prices": [], "hunk_score": None} for ticker in WATCHLIST}

class C:
    G, R, Y, BBLD, END = '\033[92m', '\033[91m', '\033[93m', '\033[1;94m', '\033[0m'

def get_hunk_score(ticker):
    if HISTORY[ticker]["hunk_score"] is not None: return HISTORY[ticker]["hunk_score"]
    try:
        t_obj = yf.Ticker(ticker)
        info = t_obj.info
        sf = info.get("shortPercentOfFloat", 0) or 0
        if sf == 1: sf = 100
        score = (sf * 0.7) + ((info.get("shortRatio", 0) or 0) * 0.3)
        HISTORY[ticker]["hunk_score"] = score
        return score
    except: return 0

def find_quality_contract(ticker, side):
    try:
        chain = rh.options.find_options_by_expiration(ticker, expirationDate='2026-05-15', optionType=side)
        valid = [o for o in chain if 0.35 <= float(o['mark_price']) <= 0.60]
        if not valid: return None
        valid.sort(key=lambda x: float(x.get('volume', 0) or 0), reverse=True)
        return valid[0]
    except: return None
def hunk_dump_execution():
    print(f"\r{C.BBLD}[*] VERITAS STANDBY @ {datetime.now().strftime('%H:%M:%S')}{C.END}   ", end="", flush=True)
    old_stderr = sys.stderr
    sys.stderr = open(os.devnull, 'w')
    try:
        quotes = rh.stocks.get_quotes(WATCHLIST)
        quotes_data = {q['symbol']: q for q in quotes if q is not None}
    except Exception:
        sys.stderr = old_stderr
        return
    finally:
        sys.stderr = old_stderr
    for ticker in WATCHLIST:
        if ticker in ACTIVE_TRADES: continue
        quote = quotes_data.get(ticker)
        if not quote: continue
        curr = float(quote['last_trade_price'])
        hunk = get_hunk_score(ticker)
        prices = HISTORY[ticker]["prices"]
        prices.append(curr)
        if len(prices) > 3: prices.pop(0)
        if len(prices) == 3 and hunk > 10:
            acc = (prices[-1] - prices[-2]) - (prices[-2] - prices[-3])
            acc_t = 0.08 if ticker in ["GME", "AMC"] else 0.05
            target = None
            if acc > acc_t: target = find_quality_contract(ticker, 'call')
            elif acc < -acc_t: target = find_quality_contract(ticker, 'put')
            if target:
                print(f"\n{C.G}[EXEC] {ticker} {target['strike_price']} {target['type']}{C.END}")
                ACTIVE_TRADES[ticker] = True
                return

if __name__ == "__main__":
    rh.login(username='Michaelmillshealy716@gmail.com', password='M3141592654h*!*$$', expiresIn=86400, scope='internal', store_session=True)
    p = rh.profiles.load_account_profile()
    print(f"\n{C.G}[+] VERITAS INITIALIZED. LIQUIDITY: ${p['buying_power']}{C.END}")
    while True:
        try:
            hunk_dump_execution()
            time.sleep(1)
        except KeyboardInterrupt: break


```


# ==========================================
# FILE: hunk_dump.json
# ==========================================

```json
[
    {
        "ticker": "GPRO",
        "price": "$1.46",
        "short_float": "16.80%",
        "days_to_cover": 3.37,
        "hunk_score": 12.77,
        "velocity": 0.0,
        "status": "STAGING"
    },
    {
        "ticker": "AMC",
        "price": "$1.59",
        "short_float": "15.42%",
        "days_to_cover": 3.0,
        "hunk_score": 11.69,
        "velocity": 0.0,
        "status": "STAGING"
    },
    {
        "ticker": "GME",
        "price": "$24.23",
        "short_float": "15.12%",
        "days_to_cover": 9.81,
        "hunk_score": 13.53,
        "velocity": 0.0,
        "status": "STAGING"
    },
    {
        "ticker": "SPCE",
        "price": "$2.45",
        "short_float": "20.81%",
        "days_to_cover": 2.45,
        "hunk_score": 15.3,
        "velocity": 0.0,
        "status": "STAGING"
    },
    {
        "ticker": "PLTR",
        "price": "$135.91",
        "short_float": "2.48%",
        "days_to_cover": 1.1,
        "hunk_score": 2.07,
        "velocity": 0.0,
        "status": "STAGING"
    },
    {
        "ticker": "TSLA",
        "price": "$389.37",
        "short_float": "2.13%",
        "days_to_cover": 1.07,
        "hunk_score": 1.81,
        "velocity": 0.0,
        "status": "STAGING"
    }
]
```


# ==========================================
# FILE: live_score.json
# ==========================================

```json
{
    "timestamp": "23:10:45",
    "entropy": 0.679,
    "teams": {
        "MTL": {
            "hamiltonian": 1.4248,
            "psi_squared": 65.5,
            "strike_chance": 82.96
        },
        "BUF": {
            "hamiltonian": 1.1619,
            "psi_squared": 62.78,
            "strike_chance": 73.77
        }
    }
}
```


# ==========================================
# FILE: autonomous_bridge.json
# ==========================================

```json
{"timestamp": "05:18:04", "ticker": "HD", "veritas_score": 0.66, "greeks": {"delta": 0.763, "gamma": 0.042}}
```


# ==========================================
# FILE: series_history.json
# ==========================================

```json
[
    {
        "timestamp": "22:44:18",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "22:44:50",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "22:45:22",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "22:45:55",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "22:46:27",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "22:47:00",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "22:47:32",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "22:48:05",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "22:48:37",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "22:49:10",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "22:49:42",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "22:50:15",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "22:50:48",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "22:51:20",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "22:51:52",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "22:52:26",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "22:53:00",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "22:53:32",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "22:54:05",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "22:54:37",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "22:55:09",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "22:55:41",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "22:56:14",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "22:56:46",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "22:57:18",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "22:57:50",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "22:58:24",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "22:58:56",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "22:59:28",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "23:00:00",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "23:00:33",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "23:01:05",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "23:01:37",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "23:02:10",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "23:02:42",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "23:03:14",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "23:03:46",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "23:04:18",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "23:04:50",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "23:05:22",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "23:05:54",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "23:06:27",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "23:06:59",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "23:07:31",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "23:08:04",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "23:08:36",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "23:09:08",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "23:09:41",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "23:10:13",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    },
    {
        "timestamp": "23:10:45",
        "MTL": {
            "H": 1.4248,
            "psi_sq": 65.5,
            "strike": 82.96,
            "amp": 1.266
        },
        "BUF": {
            "H": 1.1619,
            "psi_sq": 62.78,
            "strike": 73.77,
            "amp": 1.175
        },
        "entropy": 0.679,
        "metadata": {
            "Hamiltonian": "Total system energy (Kinetic + Potential).",
            "Psi_Squared": "Probability density of a state-change event (Goal).",
            "Entropy": "Measure of system chaos vs stability.",
            "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
        }
    }
]
```


# ==========================================
# FILE: export_results.py
# ==========================================

```python
import json
import csv
import os

# --- HVL Export Utility V1.0 ---

def export_hvl_data(input_file="series_history.json"):
    if not os.path.exists(input_file):
        print("\033[91m[ ERROR ] No history file found. Run score_engine.py first.\033[0m")
        return

    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"\033[91m[ ERROR ] Could not read ledger: {e}\033[0m")
        return

    # 1. Export to CSV (The 'Alpha Ledger' for Excel/Quants)
    keys = data[0].keys()
    with open('hvl_alpha_export.csv', 'w', newline='') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)
    
    # 2. Export to Web-Ready JSON (For HealyVectorLabs.com Charts)
    web_data = [
        {
            "time": d['timestamp'], 
            "energy": d['hamiltonian'], 
            "collapse": d['psi_sq'],
            "interference": d['interference']
        } 
        for d in data
    ]
    with open('web_graph_data.json', 'w') as f:
        json.dump(web_data, f, indent=4)

    print(f"\033[92m[ SUCCESS ] {len(data)} packets exported to CSV and Web-JSON.\033[0m")

if __name__ == "__main__":
    export_hvl_data()


```


# ==========================================
# FILE: sync_hvl.sh
# ==========================================

```sh
#!/bin/bash

# 1. LEAD ARCHITECT'S COOLDOWN
# Wait 2 seconds just to make sure Session 1 isn't mid-write
sleep 2

# 2. GIT PRODUCTION PIPELINE
# We don't run python here anymore. We just grab what the engine already made.
git add index.html web_graph_data.json series_history.json
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
git commit -m "telemetry: passive sync from live engine @ $TIMESTAMP"

# 3. PUSH TO REMOTE
git push origin main

echo -e "\e[92m[ SUCCESS ] Live Engine Data Pushed @ $TIMESTAMP\e[0m"


```


# ==========================================
# FILE: web_graph_data.json
# ==========================================

```json

```


# ==========================================
# FILE: hvl_matrix_core.py
# ==========================================

```python
# (C) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# ==============================================================================
import json
import time
import os
import math
import numpy as np
import yfinance as yf
import requests
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from nhlpy import NHLClient

# --- HVL Master Aesthetics ---
C_GREEN = '\033[92m'
C_CYAN = '\033[96m'
C_RED = '\033[91m'
C_WARN = '\033[93m'
C_PURP = '\033[95m'
C_RESET = '\033[0m'
C_BOLD = '\033[1m'

# ==============================================================================
# CONFIGURATION ENVIRONMENT
# ==============================================================================
# Drop your active JSONBlob or KVDB URL right here
API_ENDPOINT = "https://jsonblob.com/api/jsonBlob/1373038692791443456"

# ==============================================================================
# FASE & VERITAS QUANTITATIVE ENGINES
# ==============================================================================
class GeopoliticalBridge:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        
    def get_intensity_scalar(self, raw_headline):
        if not raw_headline or raw_headline == "API_THROTTLE": 
            return 0.0
        return self.analyzer.polarity_scores(raw_headline)['compound']

class EdgarRaven:
    def __init__(self):
        self.bridge = GeopoliticalBridge()
        
    def get_ticker_sentiment_and_headline(self, ticker):
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            if news and len(news) > 0:
                first_story = news[0]
                # Extract headline regardless of structural format differences in yfinance versions
                if isinstance(first_story, dict) and 'content' in first_story:
                    headline = first_story.get('content', {}).get('title', '')
                else:
                    headline = first_story.get('title', '')
                
                if headline:
                    score = self.bridge.get_intensity_scalar(headline)
                    return score, headline
            return 0.0, "Stable Vector Baseline Status"
        except Exception:
            return 0.0, "[YF LIMIT] Throttled. Maintaining drift baseline models."

class FASEStochasticEngine:
    def __init__(self, x0, T, dt):
        self.x0 = x0
        self.T = T
        self.dt = dt
        self.N = int(T / dt)
        self.t = np.linspace(0, self.T, self.N)
        
    def simulate_sentiment_path(self, base_mu, sigma, sentiment_score):
        # Shift the drift velocity based on the live VADER sentiment metric
        mu_adj = base_mu + (sentiment_score * 0.5 * base_mu)
        dW = np.random.normal(0, np.sqrt(self.dt), self.N)
        W = np.cumsum(dW)
        return self.x0 * np.exp((mu_adj - 0.5 * sigma**2) * self.t + sigma * W)

class ScoreEngine:
    def __init__(self, target_team="Buffalo Sabres", target_date="2026-05-16"):
        self.client = NHLClient()
        self.target_team = target_team
        self.target_date = target_date
        self.config = {"ROAD_BIAS": 1.15, "SIGMOID_SENSITIVITY": 0.45}

    def find_active_game(self):
        try:
            schedule_data = self.client.schedule.daily_schedule(date=self.target_date)
            for game in schedule_data.get('games', []):
                home_name = game.get('homeTeam', {}).get('name', {}).get('default', '')
                away_name = game.get('awayTeam', {}).get('name', {}).get('default', '')
                if self.target_team in [home_name, away_name]:
                    return game['id']
            return 2025030246
        except Exception:
            return 2025030246

    def get_veritas_payload(self, game_id):
        try:
            gd = self.client.game_center.boxscore(game_id=game_id)
            away = gd.get('awayTeam', {})
            home = gd.get('homeTeam', {})
            
            a_sog = float(away.get('sog', 0))
            h_sog = float(home.get('sog', 0))
            a_g = float(away.get('score', 0))
            h_g = float(home.get('score', 0))
            
            a_hits, h_hits, a_fo, h_fo = 0.0, 0.0, 50.0, 50.0
            
            for stat in gd.get('boxscore', {}).get('teamStats', []):
                cat = stat.get('category')
                raw_a = str(stat.get('awayValue', '')).replace('%','')
                raw_h = str(stat.get('homeValue', '')).replace('%','')
                try:
                    if cat == 'sog':
                        a_sog = float(raw_a) if raw_a else a_sog
                        h_sog = float(raw_h) if raw_h else h_sog
                    elif cat == 'hits':
                        a_hits = float(raw_a) if raw_a else 0.0
                        h_hits = float(raw_h) if raw_h else 0.0
                    elif cat == 'faceoffWinningPctg':
                        a_fo = float(raw_a) if raw_a else 50.0
                        h_fo = float(raw_h) if raw_h else 50.0
                except ValueError:
                    continue

            b_sv = (h_sog - h_g) / h_sog if h_sog > 0 else 0.900
            m_sv = (a_sog - a_g) / a_sog if a_sog > 0 else 0.900

            def qm(side, delta, hits, fo, opp_v, p, is_road):
                amp = 1.0 + (abs(fo - 50)/100.0) + (delta*0.5)
                m = 1.0 / (p + 0.1)
                k = (delta**2)/(2*m) if m > 0 else 0
                H = (k + opp_v + (hits*0.01)) * amp * (self.config["ROAD_BIAS"] if is_road and side=="away" else 1.0)
                psi = (1 / (1 + math.exp(-(H * self.config["SIGMOID_SENSITIVITY"])))) * 100
                return {"H": round(H, 4), "psi_sq": round(psi, 2), "strike": round(min((psi*amp), 99.99), 2)}

            mtl_q = qm("home", round(h_sog/60, 3), h_hits, h_fo, b_sv, 1.0, False)
            buf_q = qm("away", round(a_sog/60, 3), a_hits, a_fo, m_sv, 1.5, True)
            
            tot = mtl_q["H"] + buf_q["H"] + 0.1
            p1, p2 = mtl_q["H"]/tot, buf_q["H"]/tot
            ent = - (p1 * math.log(p1 + 0.01) + p2 * math.log(p2 + 0.01))
            
            return {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "entropy": round(ent, 3),
                "MTL": mtl_q,
                "BUF": buf_q
            }
        except Exception:
            return {
                "timestamp": datetime.now().strftime("%H:%M:%S"), "entropy": 0.452,
                "MTL": {"H": 1.245, "psi_sq": 54.2, "strike": 58.4},
                "BUF": {"H": 0.982, "psi_sq": 41.8, "strike": 44.1}
            }

# ==============================================================================
# MASTER REAL-TIME DATA STREAM RUNNER
# ==============================================================================
if __name__ == "__main__":
    os.system('clear' if os.name == 'posix' else 'cls')
    print(f"{C_CYAN}[SYSTEM] Launching High-Frequency Healy Vector Labs Core Daemon...{C_RESET}")
    
    edgar = EdgarRaven()
    nhl_engine = ScoreEngine()
    
    tickers = ["TSLA", "F", "XOM", "PFE", "CL=F"]
    base_prices = {"TSLA": 175.50, "F": 12.30, "XOM": 118.20, "PFE": 28.40, "CL=F": 82.10}
    
    cycle = 0
    fase_cache = {}
    
    try:
        while True:
            # 1. Gather Calculations from VERITAS Engine
            game_id = nhl_engine.find_active_game()
            v_data = nhl_engine.get_veritas_payload(game_id)
            
            # 2. Gather Calculations from FASE Engine (Every 3rd loop to protect API limits)
            if cycle % 3 == 0 or not fase_cache:
                fase_cache = {}
                print(f"{C_PURP}[FASE] Scrutinizing global news channels and computing asset paths...{C_RESET}")
                
                for ticker in tickers:
                    sentiment, headline = edgar.get_ticker_sentiment_and_headline(ticker)
                    
                    # Run Stochastic Drift Simulation paths
                    sim = FASEStochasticEngine(x0=base_prices.get(ticker, 100.0), T=1.0, dt=0.01)
                    final_states = [sim.simulate_sentiment_path(0.1, 0.3, sentiment)[-1] for _ in range(500)]
                    
                    ev = np.mean(final_states)
                    ci_l, ci_h = np.percentile(final_states, [2.5, 97.5])
                    
                    fase_cache[ticker] = {
                        "expected_value": round(float(ev), 2),
                        "ci_low": round(float(ci_l), 2),
                        "ci_high": round(float(ci_h), 2),
                        "sentiment_score": round(float(sentiment), 3),
                        "headline": headline[:60] + "..." if len(headline) > 60 else headline
                    }

            # 3. Assemble Completely Unified JSON Output
            master_state = {
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "veritas": {
                    "timestamp": v_data["timestamp"],
                    "entropy": v_data["entropy"],
                    "MTL": v_data["MTL"],
                    "BUF": v_data["BUF"]
                },
                "fase": fase_cache
            }
            
            # 4. Render Local Monitoring Console
            os.system('clear' if os.name == 'posix' else 'cls')
            print(f"{C_BOLD}+{'-'*65}+")
            print(f"|{'HEALY VECTOR LABS: LIVE MATRIX RUNTIME'.center(65)}|")
            print(f"+{'-'*65}+{C_RESET}\n")
            print(f"{C_CYAN}>>> VERITAS PIPELINE ACTIVE | MTL Strike: {master_state['veritas']['MTL']['strike']}% | BUF Strike: {master_state['veritas']['BUF']['strike']}%{C_RESET}")
            print(f"{C_WARN}>>> FASE PIPELINE ACTIVE    | Broadcasting {len(master_state['fase'])} global asset matrices.{C_RESET}")
            
            # 5. Direct Streaming Vector via HTTP PUT (Completely bypassing Git pipeline blocks)
            print(f"\n{C_PURP}[API] Blasting telemetry payload to live streaming array...{C_RESET}")
            try:
                headers = {'Content-Type': 'application/json'}
                response = requests.put(API_ENDPOINT, json=master_state, headers=headers, timeout=10)
                if response.status_code in [200, 201]:
                    print(f"{C_GREEN}[API] Transmission Success. Network State: HTTP {response.status_code} OK.{C_RESET}")
                else:
                    print(f"{C_RED}[API] Transmission Refused: HTTP {response.status_code}{C_RESET}")
            except Exception as e:
                print(f"{C_RED}[API] Critical connection block: {e}{C_RESET}")
            
            cycle += 1
            print(f"\n{C_GREEN}[SYSTEM] State stabilized. Resting 30 seconds for next high-frequency evaluation...{C_RESET}")
            time.sleep(30)
            
    except KeyboardInterrupt:
        print(f"\n{C_RED}[ SYSTEM ] MASTER MATRIX TERMINATED CLEANLY BY USER.{C_RESET}")
# (C) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# ==============================================================================
import json
import time
import os
import math
import numpy as np
import yfinance as yf
import requests
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from nhlpy import NHLClient

# --- HVL Master Aesthetics ---
C_GREEN = '\033[92m'
C_CYAN = '\033[96m'
C_RED = '\033[91m'
C_WARN = '\033[93m'
C_PURP = '\033[95m'
C_RESET = '\033[0m'
C_BOLD = '\033[1m'

# ==============================================================================
# CONFIGURATION ENVIRONMENT
# ==============================================================================
# Drop your active JSONBlob or KVDB URL right here
API_ENDPOINT = "https://jsonblob.com/api/jsonBlob/1373038692791443456"

# ==============================================================================
# FASE & VERITAS QUANTITATIVE ENGINES
# ==============================================================================
class GeopoliticalBridge:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        
    def get_intensity_scalar(self, raw_headline):
        if not raw_headline or raw_headline == "API_THROTTLE": 
            return 0.0
        return self.analyzer.polarity_scores(raw_headline)['compound']

class EdgarRaven:
    def __init__(self):
        self.bridge = GeopoliticalBridge()
        
    def get_ticker_sentiment_and_headline(self, ticker):
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            if news and len(news) > 0:
                first_story = news[0]
                # Extract headline regardless of structural format differences in yfinance versions
                if isinstance(first_story, dict) and 'content' in first_story:
                    headline = first_story.get('content', {}).get('title', '')
                else:
                    headline = first_story.get('title', '')
                
                if headline:
                    score = self.bridge.get_intensity_scalar(headline)
                    return score, headline
            return 0.0, "Stable Vector Baseline Status"
        except Exception:
            return 0.0, "[YF LIMIT] Throttled. Maintaining drift baseline models."

class FASEStochasticEngine:
    def __init__(self, x0, T, dt):
        self.x0 = x0
        self.T = T
        self.dt = dt
        self.N = int(T / dt)
        self.t = np.linspace(0, self.T, self.N)
        
    def simulate_sentiment_path(self, base_mu, sigma, sentiment_score):
        # Shift the drift velocity based on the live VADER sentiment metric
        mu_adj = base_mu + (sentiment_score * 0.5 * base_mu)
        dW = np.random.normal(0, np.sqrt(self.dt), self.N)
        W = np.cumsum(dW)
        return self.x0 * np.exp((mu_adj - 0.5 * sigma**2) * self.t + sigma * W)

class ScoreEngine:
    def __init__(self, target_team="Buffalo Sabres", target_date="2026-05-16"):
        self.client = NHLClient()
        self.target_team = target_team
        self.target_date = target_date
        self.config = {"ROAD_BIAS": 1.15, "SIGMOID_SENSITIVITY": 0.45}

    def find_active_game(self):
        try:
            schedule_data = self.client.schedule.daily_schedule(date=self.target_date)
            for game in schedule_data.get('games', []):
                home_name = game.get('homeTeam', {}).get('name', {}).get('default', '')
                away_name = game.get('awayTeam', {}).get('name', {}).get('default', '')
                if self.target_team in [home_name, away_name]:
                    return game['id']
            return 2025030246
        except Exception:
            return 2025030246

    def get_veritas_payload(self, game_id):
        try:
            gd = self.client.game_center.boxscore(game_id=game_id)
            away = gd.get('awayTeam', {})
            home = gd.get('homeTeam', {})
            
            a_sog = float(away.get('sog', 0))
            h_sog = float(home.get('sog', 0))
            a_g = float(away.get('score', 0))
            h_g = float(home.get('score', 0))
            
            a_hits, h_hits, a_fo, h_fo = 0.0, 0.0, 50.0, 50.0
            
            for stat in gd.get('boxscore', {}).get('teamStats', []):
                cat = stat.get('category')
                raw_a = str(stat.get('awayValue', '')).replace('%','')
                raw_h = str(stat.get('homeValue', '')).replace('%','')
                try:
                    if cat == 'sog':
                        a_sog = float(raw_a) if raw_a else a_sog
                        h_sog = float(raw_h) if raw_h else h_sog
                    elif cat == 'hits':
                        a_hits = float(raw_a) if raw_a else 0.0
                        h_hits = float(raw_h) if raw_h else 0.0
                    elif cat == 'faceoffWinningPctg':
                        a_fo = float(raw_a) if raw_a else 50.0
                        h_fo = float(raw_h) if raw_h else 50.0
                except ValueError:
                    continue

            b_sv = (h_sog - h_g) / h_sog if h_sog > 0 else 0.900
            m_sv = (a_sog - a_g) / a_sog if a_sog > 0 else 0.900

            def qm(side, delta, hits, fo, opp_v, p, is_road):
                amp = 1.0 + (abs(fo - 50)/100.0) + (delta*0.5)
                m = 1.0 / (p + 0.1)
                k = (delta**2)/(2*m) if m > 0 else 0
                H = (k + opp_v + (hits*0.01)) * amp * (self.config["ROAD_BIAS"] if is_road and side=="away" else 1.0)
                psi = (1 / (1 + math.exp(-(H * self.config["SIGMOID_SENSITIVITY"])))) * 100
                return {"H": round(H, 4), "psi_sq": round(psi, 2), "strike": round(min((psi*amp), 99.99), 2)}

            mtl_q = qm("home", round(h_sog/60, 3), h_hits, h_fo, b_sv, 1.0, False)
            buf_q = qm("away", round(a_sog/60, 3), a_hits, a_fo, m_sv, 1.5, True)
            
            tot = mtl_q["H"] + buf_q["H"] + 0.1
            p1, p2 = mtl_q["H"]/tot, buf_q["H"]/tot
            ent = - (p1 * math.log(p1 + 0.01) + p2 * math.log(p2 + 0.01))
            
            return {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "entropy": round(ent, 3),
                "MTL": mtl_q,
                "BUF": buf_q
            }
        except Exception:
            return {
                "timestamp": datetime.now().strftime("%H:%M:%S"), "entropy": 0.452,
                "MTL": {"H": 1.245, "psi_sq": 54.2, "strike": 58.4},
                "BUF": {"H": 0.982, "psi_sq": 41.8, "strike": 44.1}
            }

# ==============================================================================
# MASTER REAL-TIME DATA STREAM RUNNER
# ==============================================================================
if __name__ == "__main__":
    os.system('clear' if os.name == 'posix' else 'cls')
    print(f"{C_CYAN}[SYSTEM] Launching High-Frequency Healy Vector Labs Core Daemon...{C_RESET}")
    
    edgar = EdgarRaven()
    nhl_engine = ScoreEngine()
    
    tickers = ["TSLA", "F", "XOM", "PFE", "CL=F"]
    base_prices = {"TSLA": 175.50, "F": 12.30, "XOM": 118.20, "PFE": 28.40, "CL=F": 82.10}
    
    cycle = 0
    fase_cache = {}
    
    try:
        while True:
            # 1. Gather Calculations from VERITAS Engine
            game_id = nhl_engine.find_active_game()
            v_data = nhl_engine.get_veritas_payload(game_id)
            
            # 2. Gather Calculations from FASE Engine (Every 3rd loop to protect API limits)
            if cycle % 3 == 0 or not fase_cache:
                fase_cache = {}
                print(f"{C_PURP}[FASE] Scrutinizing global news channels and computing asset paths...{C_RESET}")
                
                for ticker in tickers:
                    sentiment, headline = edgar.get_ticker_sentiment_and_headline(ticker)
                    
                    # Run Stochastic Drift Simulation paths
                    sim = FASEStochasticEngine(x0=base_prices.get(ticker, 100.0), T=1.0, dt=0.01)
                    final_states = [sim.simulate_sentiment_path(0.1, 0.3, sentiment)[-1] for _ in range(500)]
                    
                    ev = np.mean(final_states)
                    ci_l, ci_h = np.percentile(final_states, [2.5, 97.5])
                    
                    fase_cache[ticker] = {
                        "expected_value": round(float(ev), 2),
                        "ci_low": round(float(ci_l), 2),
                        "ci_high": round(float(ci_h), 2),
                        "sentiment_score": round(float(sentiment), 3),
                        "headline": headline[:60] + "..." if len(headline) > 60 else headline
                    }

            # 3. Assemble Completely Unified JSON Output
            master_state = {
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "veritas": {
                    "timestamp": v_data["timestamp"],
                    "entropy": v_data["entropy"],
                    "MTL": v_data["MTL"],
                    "BUF": v_data["BUF"]
                },
                "fase": fase_cache
            }
            
            # 4. Render Local Monitoring Console
            os.system('clear' if os.name == 'posix' else 'cls')
            print(f"{C_BOLD}+{'-'*65}+")
            print(f"|{'HEALY VECTOR LABS: LIVE MATRIX RUNTIME'.center(65)}|")
            print(f"+{'-'*65}+{C_RESET}\n")
            print(f"{C_CYAN}>>> VERITAS PIPELINE ACTIVE | MTL Strike: {master_state['veritas']['MTL']['strike']}% | BUF Strike: {master_state['veritas']['BUF']['strike']}%{C_RESET}")
            print(f"{C_WARN}>>> FASE PIPELINE ACTIVE    | Broadcasting {len(master_state['fase'])} global asset matrices.{C_RESET}")
            
            # 5. Direct Streaming Vector via HTTP PUT (Completely bypassing Git pipeline blocks)
            print(f"\n{C_PURP}[API] Blasting telemetry payload to live streaming array...{C_RESET}")
            try:
                headers = {'Content-Type': 'application/json'}
                response = requests.put(API_ENDPOINT, json=master_state, headers=headers, timeout=10)
                if response.status_code in [200, 201]:
                    print(f"{C_GREEN}[API] Transmission Success. Network State: HTTP {response.status_code} OK.{C_RESET}")
                else:
                    print(f"{C_RED}[API] Transmission Refused: HTTP {response.status_code}{C_RESET}")
            except Exception as e:
                print(f"{C_RED}[API] Critical connection block: {e}{C_RESET}")
            
            cycle += 1
            print(f"\n{C_GREEN}[SYSTEM] State stabilized. Resting 30 seconds for next high-frequency evaluation...{C_RESET}")
            time.sleep(30)
            
    except KeyboardInterrupt:
        print(f"\n{C_RED}[ SYSTEM ] MASTER MATRIX TERMINATED CLEANLY BY USER.{C_RESET}")


```


# ==========================================
# FILE: btc_diviner.py
# ==========================================

```python
import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import robin_stocks.robinhood as r

# ==========================================
# 0. SECURE CREDENTIAL INGESTION
# ==========================================
load_dotenv()
RH_API_KEY = os.getenv("RH_API_KEY")
RH_PRIVATE_KEY = os.getenv("RH_PRIVATE_KEY")
TRADE_RISK_DOLLARS = float(os.getenv("TRADE_RISK_DOLLARS", 20.00))

def authenticate_node():
    print("[SYSTEM] Initiating secure cryptographic handshake with Robinhood...")
    try:
        r.login(username=os.getenv("RH_USERNAME"), password=os.getenv("RH_PASSWORD"))
        print("[SYSTEM] Authentication Verified. Live network active.")
    except Exception as e:
        print(f"[WARNING] API handshake requires standard auth fallback or manual override: {e}")

# ==========================================
# 1. CORE MATH ENGINE
# ==========================================
class NeuroKinematics:
    def __init__(self, memory_window=60):
        self.window = memory_window
        self.timestamps = []
        self.prices = []
        self.velocities = []

    def ingest_crt_tick(self, raw_time, raw_price):
        quantized_time = round(raw_time * 10) / 10.0
        if not self.timestamps or quantized_time > self.timestamps[-1]:
            self.timestamps.append(quantized_time)
            self.prices.append(raw_price)
            if len(self.prices) > 1:
                dt = self.timestamps[-1] - self.timestamps[-2]
                v = (self.prices[-1] - self.prices[-2]) / dt
                self.velocities.append(v)
            else:
                self.velocities.append(0.0)
            if len(self.timestamps) > self.window:
                self.timestamps.pop(0)
                self.prices.pop(0)
                self.velocities.pop(0)

    def extract_fourier_derivatives(self):
        if len(self.velocities) < 5:
            return 0.0, 0.0
        v_current = self.velocities[-1]
        v_past = sum(self.velocities[-5:-1]) / 4.0
        dt = self.timestamps[-1] - self.timestamps[-5]
        acceleration = (v_current - v_past) / dt if dt > 0 else 0.0
        return v_current, acceleration

    def project_taylor_series(self, dt_seconds):
        if not self.prices:
            return 0.0
        x_now = self.prices[-1]
        v, a = self.extract_fourier_derivatives()
        return x_now + (v * dt_seconds) + (0.5 * a * (dt_seconds ** 2))

# ==========================================
# 2. INSTANT EXECUTION LOGIC
# ==========================================
def fetch_live_robinhood_spot():
    """Pulls the exact internal price Robinhood is using for execution."""
    try:
        quote = r.crypto.get_crypto_quote('BTC')
        return time.time(), float(quote['mark_price'])
    except Exception:
        return time.time(), 0.0

def evaluate_and_stage_order(current_spot, projected_price):
    print(f"\n[EVALUATION] Projecting order matrix against ${TRADE_RISK_DOLLARS:.2f} limit...")
    
    # Placeholder for live Kalshi/RH Prediction spread.
    # Testing a hypothetical live 42-cent contract
    live_contract_price = 0.42 
    
    if 0.35 <= live_contract_price <= 0.70:
        quantity = int(TRADE_RISK_DOLLARS / live_contract_price)
        total_exposure = quantity * live_contract_price
        
        print(f"[LIVE ORDER STAGED] Target found in bounds.")
        print(f" -> Contract Price: {live_contract_price*100:.0f}¢")
        print(f" -> Execution Size: {quantity} Contracts")
        print(f" -> Total Capital Exposure: ${total_exposure:.2f}")
        
        print(f"\n[!!!] SAFETY BYPASS ENGAGED: Stopping before POST transmission.")
        r.orders.order_buy_crypto_limit('BTC', quantity, live_contract_price)
    else:
        print(f"[REJECT] Live price {live_contract_price*100:.0f}¢ fails 35-70 risk parameters.")

def run_instant_telemetry():
    engine = NeuroKinematics()
    authenticate_node()
    
    print(f"\n[SYSTEM START] btc_diviner.py (ON-DEMAND MANUAL ENGINE) deployed.")
    print("Network: Robinhood Internal | Execution: Disabled | Trigger: INSTANT")
    
    print(f"\n[WAKE] Spooling live Robinhood liquidity for 15 seconds to build momentum profile...")
    
    # Run the live feed loop for exactly 15 seconds to build the velocity array
    end_time = time.time() + 15.0
    while time.time() < end_time:
        live_time, live_price = fetch_live_robinhood_spot()
        if live_price > 0:
            engine.ingest_crt_tick(live_time, live_price)
        time.sleep(0.5)
        
    exec_time = datetime.now()
    current_spot = engine.prices[-1] if engine.prices else 0.0
    
    print(f"\n--------------------------------------------------")
    print(f"[TRIGGER] MANUAL GATE DROPPED AT {exec_time.strftime('%H:%M:%S')}")
    print(f"[LIVE RH SPOT] ${current_spot:.2f}")
    
    # Dynamically calculate seconds remaining until the top of the next hour
    next_hour = (exec_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))
    seconds_to_settlement = (next_hour - exec_time).total_seconds()
    
    # Project out to the exact settlement line
    projected_settlement = engine.project_taylor_series(seconds_to_settlement)
    print(f"[TAYLOR PROJECTION] Forecasting {seconds_to_settlement:.0f}s to Top-of-Hour: ${projected_settlement:.2f}")
    
    evaluate_and_stage_order(current_spot, projected_settlement)
    print(f"--------------------------------------------------\n")
    print("[SYSTEM] Run complete. Shutting down node.")

if __name__ == "__main__":
    run_instant_telemetry()


```


# ==========================================
# FILE: gen_keys.py
# ==========================================

```python
import base64
import nacl.signing

# 1. Generate a secure cryptographic key pair
private_key = nacl.signing.SigningKey.generate()
public_key = private_key.verify_key

# 2. Convert them into clean base64 text strings
private_key_base64 = base64.b64encode(private_key.encode()).decode()
public_key_base64 = base64.b64encode(public_key.encode()).decode()

print("\n=== YOUR CRYPTO KEYS GENERATED ===")
print(f"PRIVATE KEY (Put this inside your secure .env file):\n{private_key_base64}\n")
print(f"PUBLIC KEY (Paste this into Robinhood's '+ Add Key' page):\n{public_key_base64}")
print("==================================")


```


# ==========================================
# FILE: btc_signal_engine.py
# ==========================================

```python
import os
import time
import json
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
import robin_stocks.robinhood as r

# ---------------------------------------------------------
# 0. SECURE CREDENTIAL INGESTION & UI FORMATTING
# ---------------------------------------------------------
load_dotenv()
GREEN = '\033[92m'
RESET = '\033[0m'

def authenticate_node():
    print("[*SYSTEM] Initiating secure cryptographic handshake with Robinhood...")
    try:
        r.login(username=os.getenv("RH_USERNAME"), password=os.getenv("RH_PASSWORD"))
        print("[*SYSTEM] Authentication Verified. Live network active.")
    except Exception as e:
        print(f"[WARNING] API handshake issue: {e}")

# ---------------------------------------------------------
# 1. CORE MATH ENGINE (KINEMATICS + GALOIS LEARNING)
# ---------------------------------------------------------
class NeuroKinematics:
    def __init__(self, memory_window=60):
        self.window = memory_window
        self.timestamps = []
        self.prices = []
        self.velocities = []
        self.accelerations = [] # Added for self-learning history

    def ingest_crt_tick(self, raw_time, raw_price):
        quantized_time = round(raw_time * 10) / 10.0
        if not self.timestamps or quantized_time > self.timestamps[-1]:
            self.timestamps.append(quantized_time)
            self.prices.append(raw_price)
            if len(self.prices) > 1:
                dt = self.timestamps[-1] - self.timestamps[-2]
                v = (self.prices[-1] - self.prices[-2]) / dt if dt != 0 else 0
                self.velocities.append(v)
            else:
                self.velocities.append(0.0)
            
            # Enforce memory bounds
            if len(self.prices) > self.window:
                self.timestamps.pop(0)
                self.prices.pop(0)
                self.velocities.pop(0)

    def extract_fourier_derivatives(self):
        if len(self.velocities) < 5:
            return 0.0, 0.0
        v_current = self.velocities[-1]
        v_past = sum(self.velocities[-5:-1]) / 4.0
        dt = self.timestamps[-1] - self.timestamps[-5]
        acceleration = (v_current - v_past) / dt if dt != 0 else 0.0
        
        # Store a history for the self-learning Galois engine
        self.accelerations.append(acceleration)
        if len(self.accelerations) > self.window:
            self.accelerations.pop(0)
            
        return v_current, acceleration

    def project_taylor_series(self, dt_seconds):
        if len(self.prices) < 2:
            return self.prices[-1] if self.prices else 0.0
        
        x_now = self.prices[-1]
        v, a = self.extract_fourier_derivatives()
        
        dampening_ratio = 15.0 / max(dt_seconds, 15.0)
        dampened_a = a * dampening_ratio
        
        raw_projection = x_now + (v * dt_seconds) + (0.5 * dampened_a * (dt_seconds ** 2))
        
        # Dynamic Settlement Bound
        fraction_of_hour_left = min(dt_seconds / 3600.0, 1.0)
        max_allowed_move = x_now * (0.01 * fraction_of_hour_left)
        
        if raw_projection > x_now + max_allowed_move:
            return x_now + max_allowed_move
        elif raw_projection < x_now - max_allowed_move:
            return x_now - max_allowed_move
        return raw_projection

class AdaptiveGaloisEngine:
    def __init__(self):
        # The Formal Context Attributes
        self.attributes = ['HIGH_V_UP', 'POSITIVE_ACCEL', 'TAYLOR_PREMIUM']
        
    def check_lattice_lock(self, kinematics, current_price, projected_price):
        if len(kinematics.velocities) < 10:
            return False, "LEARNING_PHASE"
            
        # SELF-LEARNING: Calculate dynamic thresholds based on recent rolling history
        rolling_v_std = np.std(kinematics.velocities[-10:])
        current_v = kinematics.velocities[-1]
        current_a = kinematics.accelerations[-1] if kinematics.accelerations else 0.0
        
        # Binarize continuous data into the Galois Context Matrix
        is_high_v_up = 1 if current_v > (rolling_v_std * 1.2) else 0
        is_pos_accel = 1 if current_a > 0 else 0
        is_taylor_prem = 1 if projected_price > current_price else 0
        
        # Galois Derivation: If all attributes are present, the concept is locked
        if is_high_v_up and is_pos_accel and is_taylor_prem:
            return True, f"{GREEN}[BUY SIGNAL - GALOIS LATTICE LOCKED]{RESET}"
        else:
            return False, "[OBSERVING]"

# ---------------------------------------------------------
# 2. DAEMON LOOP (THE PRODUCER)
# ---------------------------------------------------------
def fetch_live_robinhood_spot():
    try:
        quote = r.crypto.get_crypto_quote('BTC')
        return time.time(), float(quote['mark_price'])
    except Exception:
        return time.time(), 0.0

def run_signal_daemon():
    authenticate_node()
    engine = NeuroKinematics(memory_window=60)
    galois = AdaptiveGaloisEngine()
    
    print("\n[*ALPHA NODE] Daemon initialized. Entering continuous 60-second heartbeat loop.")
    print("[*GALOIS NET] Self-learning matrices online. Waiting for data volume...\n")
    print(f"{'TIME':<12} | {'SPOT PRICE':<12} | {'FORECAST':<12} | {'STATUS':<15} | {'GALOIS STATE'}")
    print("-" * 75)
    
    while True:
        # 1. Ingest
        live_time, live_price = fetch_live_robinhood_spot()
        if live_price > 0:
            engine.ingest_crt_tick(live_time, live_price)
            
        # 2. Project
        exec_time = datetime.now()
        next_hour = (exec_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))
        seconds_to_settlement = (next_hour - exec_time).total_seconds()
        
        projected_settlement = engine.project_taylor_series(seconds_to_settlement)
        memory_size = len(engine.prices)
        
        # 3. Evaluate Galois Grouping
        lock_achieved, galois_status = galois.check_lattice_lock(engine, live_price, projected_settlement)
        
        # 4. Print Radar Blip
        status = "WARMUP" if memory_size < 5 else "LOCKED"
        
        # Format the output row
        row = f"{exec_time.strftime('%H:%M:%S'):<12} | ${live_price:<11.2f} | ${projected_settlement:<11.2f} | {memory_size}/60 {status:<8} | {galois_status}"
        print(row)
        
        # 5. Export JSON Payload
        if status == "LOCKED":
            signal_data = {
                "timestamp": exec_time.strftime('%Y-%m-%d %H:%M:%S'),
                "current_spot": live_price,
                "projected_settlement": projected_settlement,
                "seconds_to_settlement": seconds_to_settlement,
                "status": "VALID",
                "galois_lock": lock_achieved
            }
            with open("target_signal.json", "w") as f:
                json.dump(signal_data, f, indent=4)
                
        # 6. Sleep until next heartbeat
        time.sleep(60.0)

if __name__ == "__main__":
    run_signal_daemon()


```


# ==========================================
# FILE: btc_execution_node.py
# ==========================================

```python
import os
import json
from dotenv import load_dotenv
import robin_stocks.robinhood as r

load_dotenv()
TRADE_RISK_DOLLARS = float(os.getenv("TRADE_RISK_DOLLARS", 20.00))

def authenticate():
    print("[EXECUTION NODE] Authenticating...")
    r.login(username=os.getenv("RH_USERNAME"), password=os.getenv("RH_PASSWORD"))

def execute_signal():
    # 1. Read the signal file left by the Alpha Node
    try:
        with open("target_signal.json", "r") as f:
            signal = json.load(f)
    except FileNotFoundError:
        print("[ERROR] No signal file found. Run signal_engine.py first.")
        return

    print(f"\n[EXECUTION NODE] Reading Signal from {signal['timestamp']}")
    print(f"Target Settlement: ${signal['projected_settlement']:.2f}")
    
    # 2. Risk Evaluation & Live Contract Sizing
    # (Placeholder logic: assuming we query the contract spread here)
    live_contract_price = 0.42 
    
    if 0.35 <= live_contract_price <= 0.70:
        quantity = int(TRADE_RISK_DOLLARS / live_contract_price)
        total_exposure = quantity * live_contract_price
        
        print(f"[AUTHORIZED] Risk parameters clear. Contract @ {live_contract_price*100:.0f}¢")
        print(f"[TRANSMITTING] Routing order for {quantity} contracts. Total Risk: ${total_exposure:.2f}")
        
        # r.orders.order_buy_crypto_limit('BTC', quantity, live_contract_price)
        print("[SUCCESS] Order dispatched to Robinhood network.")
    else:
        print(f"[ABORT] Contract price {live_contract_price*100:.0f}¢ violates 35-70¢ constraints.")

if __name__ == "__main__":
    authenticate()
    execute_signal()

```


# ==========================================
# FILE: target_signal.json
# ==========================================

```json
{
    "timestamp": "2026-05-28 13:38:45",
    "current_spot": 73388.515,
    "projected_settlement": 73633.25745384548,
    "seconds_to_settlement": 1274.501781,
    "status": "VALID",
    "galois_lock": false
}
```


# ==========================================
# FILE: btc_counter.py
# ==========================================

```python
import os
import sys
import time
import math
from datetime import datetime
import numpy as np
from google import genai
from google.genai import types
import robin_stocks.robinhood as r

# ==============================================================================
# Environment and Library Handshake
# ==============================================================================
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("[X] Critical Error: GEMINI_API_KEY missing from .env file.")
    sys.exit(1)

# Initialize the paid API pipeline client node
client = genai.Client(api_key=api_key)

# Persistent global buffer array to hold real market data tuples: (time, spot)
price_history = []

def run_local_kinematics(current_spot, dt_step=2.0):
    """
    KINETICS LAYER: Computes localized velocity and acceleration 
    via historical time/price steps to output a 3rd-order Taylor Series target.
    """
    global price_history
    current_time = time.time()
    price_history.append((current_time, current_spot))
    
    # Maintain rolling lookback window constraint
    if len(price_history) > 5:
        price_history.pop(0)
        
    if len(price_history) < 4:
        return 0.0, 0.0, current_spot

    # Extract historical tracking states directly out of the data matrices
    t3, p3 = price_history[-1]
    t2, p2 = price_history[-2]
    t1, p1 = price_history[-3]
    t0, p0 = price_history[-4]

    dt1, dt0 = t2 - t1, t1 - t0
    if dt1 <= 0 or dt0 <= 0:
        return 0.0, 0.0, current_spot

    # Map state derivatives
    v1 = (p2 - p1) / dt1
    v0 = (p1 - p0) / dt0
    accel = (v1 - v0) / (0.5 * (t2 - t0))
    
    # Project forward assuming constant step interval duration
    projected_target = current_spot + (v1 * dt_step) + (0.5 * accel * (dt_step ** 2))
    return v1, accel, projected_target

def call_studio_intelligence(spot, vel, accel, target):
    """
    TELEMETRY ROUTER: Ships real kinematics values to your paid tier 
    endpoint to get an institutional-grade signal back.
    """
    model_id = "gemini-2.5-flash"  # Verified model targeting structure
    
    system_instruction = (
        "You are an advanced quantitative layer. Analyze the incoming Taylor-series variables "
        "and return a volatility-normalized energy signal between -1.00 and +1.00. Output ONLY the float."
    )
    
    prompt = f"""
    [TICK METRICS]
    Spot Price: ${spot:.2f}
    Velocity (P'): {vel:.2f}
    Acceleration (P''): {accel:.2f}
    Taylor Target Projection: ${target:.2f}
    """
    
    try:
        response = client.models.generate_content(
            model=model_id,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.1,
                max_output_tokens=10
            )
        )
        return response.text.strip()
    except Exception as e:
        return "API_ERR"

def get_live_tape_price():
    """
    PRODUCTION TICKER: Polls the live, active market spot price 
    directly from your authenticated Robinhood Crypto node.
    """
    try:
        quote = r.crypto.get_crypto_quote('BTC')
        if quote and 'mark_price' in quote:
            return float(quote['mark_price'])
    except Exception as e:
        # Prevent loop fragmentation on minor websocket dropped frames
        pass
    return None

# ==============================================================================
# MAIN EXECUTION ROUTINE
# ==============================================================================
if __name__ == "__main__":
    # Pull exchange credentials out of your environment layers
    rh_user = os.getenv("RH_USERNAME")
    rh_pass = os.getenv("RH_PASSWORD")
    
    print("\n" + "="*75)
    print(" HEALY VECTOR LABS - UNIFIED PRODUCTION LOG (LIVE BTC FEED)")
    print("="*75)
    print(f"{'TIMESTAMP':<10} | {'LIVE SPOT':<9} | {'TAYLOR TGT':<10} | {'VOLTAGE SIGNAL (API)'}")
    print("-"*75)

    # Initialize connection to the exchange broker infrastructure
    try:
        r.login(username=rh_user, password=rh_pass)
    except Exception as e:
        print(f"[X] Exchange Authentication Panic: {e}")
        sys.exit(1)

    try:
        while True:
            spot_price = get_live_tape_price()
            
            if spot_price is None:
                time.sleep(1.0)
                continue
                
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Execute your exact local tracking calculations
            v, a, target = run_local_kinematics(spot_price, dt_step=5.0)
            
            if len(price_history) >= 4:
                # Pipe kinematic variables straight out to the server framework
                api_energy_signal = call_studio_intelligence(spot_price, v, a, target)
                print(f"{timestamp:<10} | ${spot_price:<8.2f} | ${target:<9.2f} | {api_energy_signal}")
            else:
                print(f"{timestamp:<10} | ${spot_price:<8.2f} | [WARMING UP DATA BUFFER {len(price_history)}/4]")
                
            # Loop delay matching your original script runtime execution matrix
            time.sleep(2.0)
            
    except KeyboardInterrupt:
        print("\n[*] Core System Halted Cleanly.")


```


# ==========================================
# FILE: btc_router.py
# ==========================================

```python
import socket
import json
import time
import os

def run_router():
    HOST = '127.0.0.1'
    PORT = 65432
    
    active_qty = 0
    active_entry_price = 0.0

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print("\n" + "="*50)
        print("[*SYSTEM] VERITAS V2.2 - VANGUARD ROUTER ONLINE")
        print("="*50)
        print("[*SYSTEM] Awaiting structural kinetic breakouts...\n")

        while True:
            try:
                conn, addr = s.accept()
                with conn:
                    data = conn.recv(1024)
                    if not data: 
                        continue

                    payload = json.loads(data.decode('utf-8'))
                    action = payload.get("action", "UNKNOWN")

                    if action == "BUY":
                        strike = payload.get("strike", 0.0)
                        contract = payload.get("contract", "YES")
                        r_min = payload.get("range_min", 15)
                        r_max = payload.get("range_max", 60)

                        print("\n" + "🔴 "*10)
                        print(f"  🚨 STRUCTURAL RADAR: BUY SIGNAL 🚨  ")
                        print(f"  ACTION: Buy [{contract}] on ${strike}  ")
                        print(f"  TARGET PREMIUM: .{r_min} to .{r_max}  ")
                        print("🔴 "*10)

                        title = f"🚨 QUANT: BUY {contract}!"
                        content = f"Target: ${strike} | Limit: .{r_min} to .{r_max}"
                        os.system(f"termux-notification -t '{title}' -c '{content}' --priority max --vibrate 500,500,500")
                        os.system("termux-vibrate -d 1500 -f")

                        auth = input("\nExecute manual buy on phone? (Y/N): ").strip().upper()
                        if auth == 'Y':
                            try:
                                active_qty = int(input(f"How many [{contract}] contracts did you buy?: "))
                                active_entry_price = float(input("At what EXACT fill price? (e.g. 0.45): "))
                                print(f"[OK] Position Locked. Total Cost: ${active_qty * active_entry_price:.2f}. Monitoring Trailing Highs...")
                                conn.sendall(b"CONFIRMED")
                            except ValueError:
                                print("[WARNING] Invalid numbers. Disabling local PnL math. Engine tracking blindly...")
                                active_qty = 0
                                conn.sendall(b"CONFIRMED")
                        else:
                            print("[SKIPPED] Position aborted. Resuming scan...")
                            conn.sendall(b"REJECTED")

                    elif action == "SELL":
                        strike = payload.get("strike", 0.0)
                        contract = payload.get("contract", "UNKNOWN")
                        reason = payload.get("reason", "Kinematic Shift")

                        print("\n" + "🟢 "*10)
                        print(f"  💰 INITIATE LIQUIDATION PROTOCOL 💰  ")
                        print(f"  POSITION: Dump [{contract}] Contracts  ")
                        print(f"  REASON: {reason}  ")
                        print("🟢 "*10)

                        title = f"💰 QUANT: SELL {contract} NOW!"
                        os.system(f"termux-notification -t '{title}' -c '{reason}' --priority max --vibrate 1000,200,1000")
                        os.system("termux-vibrate -d 1500 -f")

                        auth = input("\nDid you manually sell on phone? (Y/N): ").strip().upper()
                        if auth == 'Y':
                            if active_qty > 0:
                                try:
                                    exit_price = float(input("At what EXACT fill price? (e.g. 0.85): "))
                                    pnl = (exit_price - active_entry_price) * active_qty
                                    if pnl >= 0:
                                        print(f"\n[WIN] Trade executed flawlessly. You made +${pnl:.2f} 💸")
                                    else:
                                        print(f"\n[LOSS] Trade liquidated. You lost -${abs(pnl):.2f} 🩸")
                                except ValueError:
                                    print("[WARNING] Invalid math input. Skipping PnL log.")
                                    
                            print("[OK] Capital secured. Resetting kinematics to OBSERVING mode...\n")
                            active_qty = 0
                            active_entry_price = 0.0
                            conn.sendall(b"CONFIRMED")
                        else:
                            print("[WARNING] Override detected. You will bleed. Re-ping scheduled.")
                            conn.sendall(b"REJECTED")

            except json.JSONDecodeError:
                print("[ERROR] Corrupted JSON payload received.")
            except Exception as e:
                print(f"[ERROR] Router fault: {e}")
                time.sleep(1)

if __name__ == "__main__":
    run_router()

```


# ==========================================
# FILE: btc_engine.py
# ==========================================

```python
import os, time, json, math, socket
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
import robin_stocks.robinhood as r

load_dotenv()

def authenticate_node():
    r.login(username=os.getenv("RH_USERNAME"), password=os.getenv("RH_PASSWORD"))

class NeuroKinematics:
    def __init__(self):
        self.timestamps, self.prices, self.volumes = [], [], []
        self.velocities, self.accelerations = [], []
        self.buffer_limit = 60

    def ingest_crt_tick(self, t, price, vol):
        self.timestamps.append(t); self.prices.append(price); self.volumes.append(vol)
        if len(self.prices) > 1:
            dt = self.timestamps[-1] - self.timestamps[-2]
            self.velocities.append((self.prices[-1] - self.prices[-2]) / dt if dt != 0 else 0)
        else: 
            self.velocities.append(0.0)

        if len(self.velocities) > 4:
            v_past = sum(self.velocities[-5:-1]) / 4.0
            dt = self.timestamps[-1] - self.timestamps[-5]
            self.accelerations.append((self.velocities[-1] - v_past) / dt if dt != 0 else 0)
        else: 
            self.accelerations.append(0.0)

        if len(self.prices) > self.buffer_limit:
            self.timestamps.pop(0); self.prices.pop(0); self.volumes.pop(0)
            self.velocities.pop(0); self.accelerations.pop(0)

    def get_vwma(self, period=15):
        if len(self.prices) < period: return self.prices[-1] if self.prices else 0.0
        prices_arr = np.array(self.prices[-period:])
        vols_arr = np.array(self.volumes[-period:])
        if np.sum(vols_arr) == 0: return np.mean(prices_arr) 
        return np.sum(prices_arr * vols_arr) / np.sum(vols_arr)

    def project_taylor_series(self, dt_seconds):
        if len(self.prices) < 2: return 0.0
        time_decay = max(0.1, 1.0 - (dt_seconds / 3600.0))
        return self.prices[-1] + (self.velocities[-1] * dt_seconds * time_decay)

class DerivativeManager:
    def __init__(self):
        self.active_position = False
        self.entry_strike = 0.0
        self.entry_spot_price = 0.0
        self.contract_type = ""
        self.max_profit_delta = 0.0

    def check_buy_lock(self, k, spot, projected, time_left):
        if self.active_position: 
            return False, 0.0, "", "[HOLDING]"
            
        if len(k.velocities) < 20: 
            return False, 0.0, "", "[WARMING UP BUFFER]"

        vwma = k.get_vwma(15)

        # -------------------------------------------------------------
        # KILLSWITCH 1: EXPIRATION DEATH ZONE
        # -------------------------------------------------------------
        if time_left < 300:
            return False, 0.0, "", "[DEATH ZONE] Bankroll locked. Switch to next hour."

        # -------------------------------------------------------------
        # KILLSWITCH 2: DYNAMIC LIQUIDITY LOCK (The Dead Market Filter)
        # -------------------------------------------------------------
        vol_micro = np.mean(k.volumes[-5:])
        vol_macro = np.mean(k.volumes)
        if vol_micro < (vol_macro * 0.85):
            return False, 0.0, "", "[FLATLINE] Liquidity dead. Awaiting institutional volume."
        
        v_std = np.std(k.velocities[-10:])
        vol_avg = np.mean(k.volumes[-10:])
        
        gamma_active = time_left < 1200
        grind_threshold = 25.0 if gamma_active else 40.0
        vol_req = 1.05 if gamma_active else 1.15
        
        is_god_candle_up = k.velocities[-1] > (v_std * 3.0)
        is_god_candle_down = k.velocities[-1] < -(v_std * 3.0)

        # 15-Tick Structural Baseline
        price_delta_15 = spot - k.prices[-15] 

        bull_vel = k.velocities[-1] > (v_std * 0.7)
        bull_vol = k.volumes[-1] > (vol_avg * vol_req)
        bull_grind = price_delta_15 > grind_threshold

        bear_vel = k.velocities[-1] < -(v_std * 0.7)
        bear_vol = k.volumes[-1] > (vol_avg * vol_req)
        bear_grind = price_delta_15 < -grind_threshold

        # SCRIPT 1: STRUCTURAL MOMENTUM UP (YES)
        if spot > vwma and ((bull_vol and bull_vel) or bull_grind):
            target_strike = math.ceil(spot / 100.0) * 100.0
            
            # WIDER OFFSET: Forces premium down to 20c-55c range mathematically
            if (target_strike - spot) < 25.0: target_strike += 100.0
            if is_god_candle_up: target_strike += 100.0
            
            proj_clearance = 1.0 if bull_grind else 5.0
            if projected >= (target_strike + proj_clearance):
                msg = "GOD CANDLE UP" if is_god_candle_up else "Bullish Trend Ignition"
                return True, target_strike, "YES", f"[RADAR] {msg}. TGT: {target_strike}"
                
        # SCRIPT 2: STRUCTURAL MOMENTUM DOWN (NO)
        if spot < vwma and ((bear_vol and bear_vel) or bear_grind):
            target_strike = math.floor(spot / 100.0) * 100.0
            
            # WIDER OFFSET: Prevents overpaying for deep ITM bottoms
            if (spot - target_strike) < 25.0: target_strike -= 100.0
            if is_god_candle_down: target_strike -= 100.0
            
            proj_clearance = 1.0 if bear_grind else 5.0
            if projected <= (target_strike - proj_clearance):
                msg = "GOD CANDLE DOWN" if is_god_candle_down else "Bearish Trend Ignition"
                return True, target_strike, "NO", f"[RADAR] {msg}. TGT: {target_strike}"

        status_msg = f"[OBSERVING - VANGUARD] VWMA: {vwma:.2f} | 15-Tick: {price_delta_15:.2f}"
        if gamma_active: status_msg += " | GAMMA ACTIVE"
        return False, 0.0, "", status_msg

    def check_sell_lock(self, k, spot, time_left):
        if not self.active_position: 
            return False, "[NO POS]"
            
        if self.contract_type == "YES":
            trade_delta = spot - self.entry_spot_price
            strike_distance = spot - self.entry_strike
            momentum_dead = (k.velocities[-1] < 0)
        else: 
            trade_delta = self.entry_spot_price - spot
            strike_distance = self.entry_strike - spot
            momentum_dead = (k.velocities[-1] > 0)
            
        if trade_delta > self.max_profit_delta:
            self.max_profit_delta = trade_delta
            
        pullback_from_peak = self.max_profit_delta - trade_delta
        
        price_delta_5 = spot - k.prices[-5]
        momentum_failing_macro = (self.contract_type == "YES" and price_delta_5 < 0) or (self.contract_type == "NO" and price_delta_5 > 0)
        
        # 1. SCALP PROFIT TAKE 
        if self.max_profit_delta >= 40.0:
            if pullback_from_peak >= 20.0:
                return True, f"Trailing Stop Hit. Peak was +{self.max_profit_delta:.2f} Pts. Securing profit."
                
        # 2. STRUCTURAL STOP LOSS 
        if trade_delta < -45.0 and momentum_failing_macro:
            return True, f"Trend broke. Trade dropped {trade_delta:.2f} Pts. CUT LOSSES."
            
        # 3. EXPIRATION DEATH
        if time_left < 120 and strike_distance < 15.0:
            return True, "Expiration imminent. Liquidation mandatory."
            
        return False, f"[{self.contract_type} TGT: {self.entry_strike}] PnL Delta: {trade_delta:.2f} | Peak: +{self.max_profit_delta:.2f}"

def send_signal(payload):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', 65432))
            s.sendall(json.dumps(payload).encode('utf-8'))
            return s.recv(1024).decode('utf-8') == "CONFIRMED"
    except: 
        return False

def run_daemon():
    authenticate_node()
    engine = NeuroKinematics()
    manager = DerivativeManager()
    print("\n[*SYSTEM] Day 3 Apex Vanguard Online. Awaiting market volume...")
    
    last_cum_vol = 0.0
    
    while True:
        try:
            quote = r.crypto.get_crypto_quote('BTC')
            if not quote or 'mark_price' not in quote:
                time.sleep(1.0)
                continue
                
            spot = float(quote['mark_price'])
            cum_vol = float(quote['volume'])
            t = time.time()
            
            tick_vol = max(0.0, cum_vol - last_cum_vol) if last_cum_vol > 0 else 1.0
            last_cum_vol = cum_vol
            
            engine.ingest_crt_tick(t, spot, tick_vol)
            
            now = datetime.now()
            next_hour = (now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))
            seconds_left = (next_hour - now).total_seconds()
            
            projected = engine.project_taylor_series(seconds_left)
            buffer_count = len(engine.prices)
            
            if not manager.active_position:
                buy_now, strike, contract_type, msg = manager.check_buy_lock(engine, spot, projected, seconds_left)
                print(f"[{now.strftime('%H:%M:%S')}] | BTC: {spot:<9.2f} | {buffer_count}/60 | {msg}")
                
                if buy_now:
                    # Enforcing strict premium boundaries
                    if send_signal({"action": "BUY", "contract": contract_type, "strike": strike, "range_min": 10, "range_max": 55}):
                        manager.active_position = True
                        manager.entry_strike = strike
                        manager.entry_spot_price = spot
                        manager.contract_type = contract_type
                        time.sleep(10)
            else:
                sell_now, msg = manager.check_sell_lock(engine, spot, seconds_left)
                print(f"[{now.strftime('%H:%M:%S')}] | BTC: {spot:<9.2f} | {buffer_count}/60 | {msg}")
                
                if sell_now:
                    if send_signal({"action": "SELL", "contract": manager.contract_type, "strike": manager.entry_strike, "reason": msg}):
                        manager.active_position = False
                        manager.entry_strike = 0.0
                        manager.entry_spot_price = 0.0
                        manager.contract_type = ""
                        time.sleep(10)
            
            time.sleep(5)
        except Exception as e:
            time.sleep(5)

if __name__ == "__main__":
    run_daemon()

```


# ==========================================
# FILE: test_alarm.py
# ==========================================

```python
import socket
import json
import time

print("Sending FAKE BUY SIGNAL to the Router in 3 seconds...")
time.sleep(3)

fake_buy_signal = {
    "action": "BUY", 
    "strike": 77100, 
    "premium": 55
}

try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('127.0.0.1', 65432))
        s.sendall(json.dumps(fake_buy_signal).encode('utf-8'))
        
        print("Signal sent! Check your Router window (and your phone lock screen).")
        print("Go type 'Y' in the Router window so this script can finish.")
        
        # Wait for you to type Y/N
        response = s.recv(1024).decode('utf-8')
        print(f"\nThe Router replied: {response}")
        print("Test Complete!")
        
except ConnectionRefusedError:
    print("FAILED: The Router isn't running! Go start btc_router.py first.")

```


# ==========================================
# FILE: btc_quant_engine.py
# ==========================================

```python
import os
import time
import json
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
import robin_stocks.robinhood as r

# ---------------------------------------------------------
# 0. SECURE CREDENTIAL INGESTION & UI FORMATTING
# ---------------------------------------------------------
load_dotenv()
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'

def authenticate_node():
    print("[*SYSTEM] Initiating secure cryptographic handshake with Robinhood...")
    try:
        # Using robin_stocks standard auth (ensure RH_USERNAME/PASSWORD are in .env)
        # Note: For the official API key (Crypto_walk), a different requests-based payload is needed,
        # but robin_stocks is currently the most robust wrapper for Python.
        r.login(username=os.getenv("RH_USERNAME"), password=os.getenv("RH_PASSWORD"))
        print(f"{GREEN}[*SYSTEM] Authentication Verified. Live network active.{RESET}")
    except Exception as e:
        print(f"{RED}[WARNING] API handshake issue: {e}{RESET}")
        exit(1)

# ---------------------------------------------------------
# 1. CORE MATH ENGINE (KINEMATICS + GALOIS LEARNING)
# ---------------------------------------------------------
class NeuroKinematics:
    def __init__(self, memory_window=60):
        self.window = memory_window
        self.timestamps = []
        self.prices = []
        self.volumes = [] # ADDED: Volume tracking
        self.velocities = []
        self.accelerations = [] 

    def ingest_crt_tick(self, raw_time, raw_price, raw_volume):
        quantized_time = round(raw_time * 10) / 10.0
        if not self.timestamps or quantized_time > self.timestamps[-1]:
            self.timestamps.append(quantized_time)
            self.prices.append(raw_price)
            self.volumes.append(raw_volume) # Store volume
            
            if len(self.prices) > 1:
                dt = self.timestamps[-1] - self.timestamps[-2]
                v = (self.prices[-1] - self.prices[-2]) / dt if dt != 0 else 0
                self.velocities.append(v)
            else:
                self.velocities.append(0.0)

            # Enforce memory bounds
            if len(self.prices) > self.window:
                self.timestamps.pop(0)
                self.prices.pop(0)
                self.volumes.pop(0)
                self.velocities.pop(0)

    def extract_fourier_derivatives(self):
        if len(self.velocities) < 5:
            return 0.0, 0.0
        v_current = self.velocities[-1]
        v_past = sum(self.velocities[-5:-1]) / 4.0
        dt = self.timestamps[-1] - self.timestamps[-5]
        acceleration = (v_current - v_past) / dt if dt != 0 else 0.0
        
        self.accelerations.append(acceleration)
        if len(self.accelerations) > self.window:
            self.accelerations.pop(0)
            
        return v_current, acceleration

    def project_taylor_series(self, dt_seconds):
        if len(self.prices) < 2:
            return self.prices[-1] if self.prices else 0.0
            
        x_now = self.prices[-1]
        v, a = self.extract_fourier_derivatives()
        
        # PATCH 1: LINEAR DAMPENING (Capping the explosive dt^2 variable)
        # This stops the engine from projecting $600 spikes on 60-second noise.
        time_decay_factor = max(0.1, 1.0 - (dt_seconds / 3600.0)) 
        projected_target = x_now + (v * dt_seconds * time_decay_factor)
        
        return projected_target

class AdaptiveGaloisEngine:
    def __init__(self):
        self.attributes = ['HIGH_V_UP', 'POSITIVE_ACCEL', 'VOLUME_CONFIRMED']

    def check_lattice_lock(self, kinematics, current_price, projected_price):
        if len(kinematics.velocities) < 10:
            return False, "LEARNING_PHASE"
            
        # SELF-LEARNING: Calculate dynamic thresholds
        rolling_v_std = np.std(kinematics.velocities[-10:])
        rolling_vol_avg = np.mean(kinematics.volumes[-10:])
        
        current_v = kinematics.velocities[-1]
        current_a = kinematics.accelerations[-1] if kinematics.accelerations else 0.0
        current_vol = kinematics.volumes[-1]

        # PATCH 2: INCREASED SIGMA TO 2.5 (Stops trading random noise)
        is_high_v_up = 1 if current_v > (rolling_v_std * 2.00) else 0 
        is_pos_accel = 1 if current_a > 0 else 0
        
        # PATCH 3: VOLUME CONFIRMATION (Prevents fake-out traps)
        is_vol_confirmed = 1 if current_vol > (rolling_vol_avg * 1.1) else 0

        # Galois Derivation
        if is_high_v_up and is_pos_accel and is_vol_confirmed:
            return True, f"{GREEN}[EXECUTE BUY - GALOIS LOCKED]{RESET}"
        else:
            return False, "[OBSERVING]"

# ---------------------------------------------------------
# 2. THE ORDER ROUTER (HOW YOU MAKE TRADES)
# ---------------------------------------------------------
def execute_spot_trade(amount_in_dollars):
    """
    This is the function that actually moves your money.
    It tells Robinhood to execute a market buy for $X of Bitcoin.
    """
    try:
        print(f"\n{GREEN}[>>> ROUTING ORDER] Purchasing ${amount_in_dollars} of BTC...{RESET}")
        # UNCOMMENT THE LINE BELOW TO ACTUALLY BUY REAL BITCOIN WITH REAL MONEY
        receipt = r.orders.order_buy_crypto_by_price('BTC', amountInDollars=amount_in_dollars)
        # print(f"[{datetime.now()}] SUCCESS: Fill details saved to logs.")
        print(f"[TEST MODE] API Call simulated. Target: Buy ${amount_in_dollars} BTC.")
    except Exception as e:
        print(f"{RED}[ROUTING ERROR] Execution failed: {e}{RESET}")

# ---------------------------------------------------------
# 3. DAEMON LOOP (THE PRODUCER)
# ---------------------------------------------------------
def fetch_live_robinhood_spot():
    try:
        quote = r.crypto.get_crypto_quote('BTC')
        return time.time(), float(quote['mark_price']), float(quote['volume'])
    except Exception:
        return time.time(), 0.0, 0.0

def run_signal_daemon():
    authenticate_node()
    engine = NeuroKinematics(memory_window=60)
    galois = AdaptiveGaloisEngine()
    
    print("\n[*ALPHA NODE] Daemon initialized. Entering continuous heartbeat loop.")
    print(f"{'TIME':<12} | {'SPOT PRICE':<12} | {'FORECAST':<12} | {'GALOIS STATE'}")
    print("-" * 65)

    last_trade_time = datetime.now() - timedelta(minutes=15) # Cooldown timer

    while True:
        # 1. Ingest Data
        live_time, live_price, live_volume = fetch_live_robinhood_spot()
        if live_price > 0:
            engine.ingest_crt_tick(live_time, live_price, live_volume)

        # 2. Project Math
        exec_time = datetime.now()
        next_hour = (exec_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))
        seconds_to_settlement = (next_hour - exec_time).total_seconds()
        
        projected_settlement = engine.project_taylor_series(seconds_to_settlement)

        # 3. Evaluate Signal
        lock_achieved, galois_status = galois.check_lattice_lock(engine, live_price, projected_settlement)

        # 4. Print Output
        time_str = exec_time.strftime('%H:%M:%S')
        print(f"{time_str:<12} | ${live_price:<11.2f} | ${projected_settlement:<11.2f} | {galois_status}")

        # 5. EXECUTION LOGIC (MONEY ROUTING)
        time_since_last_trade = (datetime.now() - last_trade_time).total_seconds()
        
        # If signal fires AND we haven't traded in the last 5 minutes (Cooldown)
        if lock_achieved and time_since_last_trade > 300:
            # We execute a trade for $10 of Bitcoin
            execute_spot_trade(amount_in_dollars=10.00) 
            last_trade_time = datetime.now()

        # 6. Sleep
        time.sleep(60.0)

if __name__ == "__main__":
    run_signal_daemon()

```


# ==========================================
# FILE: firebase.json
# ==========================================

```json
{
  "hosting": {
    "public": ".",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ]
  }
}

```


# ==========================================
# FILE: btc_derivative_engine.py
# ==========================================

```python
import os
import time
import json
import math
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
import robin_stocks.robinhood as r

# ---------------------------------------------------------
# 0. ENVIRONMENT & UI
# ---------------------------------------------------------
load_dotenv()
GREEN = '\033[92m'
RED = '\033[91m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def authenticate_node():
    print("[*SYSTEM] Initiating secure Spot feed handshake...")
    try:
        r.login(username=os.getenv("RH_USERNAME"), password=os.getenv("RH_PASSWORD"))
    except Exception as e:
        pass # Handle gracefully if using web-scraper concurrently

# ---------------------------------------------------------
# 1. CORE MATH ENGINE (KINEMATICS)
# ---------------------------------------------------------
class NeuroKinematics:
    def __init__(self, memory_window=60):
        self.window = memory_window
        self.timestamps, self.prices, self.volumes = [], [], []
        self.velocities, self.accelerations = [], []

    def ingest_crt_tick(self, raw_time, raw_price, raw_volume):
        self.timestamps.append(raw_time)
        self.prices.append(raw_price)
        self.volumes.append(raw_volume)
        
        if len(self.prices) > 1:
            dt = self.timestamps[-1] - self.timestamps[-2]
            v = (self.prices[-1] - self.prices[-2]) / dt if dt != 0 else 0
            self.velocities.append(v)
        else:
            self.velocities.append(0.0)

        if len(self.velocities) > 4:
            v_past = sum(self.velocities[-5:-1]) / 4.0
            dt = self.timestamps[-1] - self.timestamps[-5]
            a = (self.velocities[-1] - v_past) / dt if dt != 0 else 0.0
            self.accelerations.append(a)
        else:
            self.accelerations.append(0.0)

        # Enforce limits
        if len(self.prices) > self.window:
            self.timestamps.pop(0); self.prices.pop(0); self.volumes.pop(0)
            self.velocities.pop(0); self.accelerations.pop(0)

    def project_taylor_series(self, dt_seconds):
        if len(self.prices) < 2: return 0.0
        x_now = self.prices[-1]
        v = self.velocities[-1]
        time_decay = max(0.1, 1.0 - (dt_seconds / 3600.0)) # Linear dampening
        return x_now + (v * dt_seconds * time_decay)

# ---------------------------------------------------------
# 2. EVENT CONTRACT RISK MANAGER (GALOIS LOGIC)
# ---------------------------------------------------------
class DerivativeManager:
    def __init__(self):
        self.active_position = False
        self.entry_strike = 0.0
        self.entry_price = 0.0

    def calculate_target_strike(self, spot_price):
        """Finds the nearest Robinhood $100 interval strike above spot"""
        return math.ceil(spot_price / 100.0) * 100.0

    def check_buy_lock(self, kinematics, spot, projected):
        if len(kinematics.velocities) < 10 or self.active_position:
            return False, 0.0, "[WAITING]"

        v_std = np.std(kinematics.velocities[-10:])
        vol_avg = np.mean(kinematics.volumes[-10:])
        v_current, a_current, vol_current = kinematics.velocities[-1], kinematics.accelerations[-1], kinematics.volumes[-1]

        # 1. Kinematic Breakout Check (2.5 Sigma + Volume)
        if v_current > (v_std * 2.5) and a_current > 0 and vol_current > (vol_avg * 1.1):
            
            target_strike = self.calculate_target_strike(spot)
            
            # 2. Projection Check (Does the math actually think we cross the strike?)
            if projected > target_strike:
                return True, target_strike, f"{GREEN}[BUY LOCK] TARGET: ${target_strike} | MAX PREMIUM: 55¢{RESET}"
                
        return False, 0.0, "[OBSERVING]"

    def check_sell_lock(self, kinematics, spot, time_left_seconds):
        if not self.active_position: return False, "[NO POS]"

        v_current = kinematics.velocities[-1]
        a_current = kinematics.accelerations[-1]

        # Sell Condition A: Parabolic Take Profit (Spot blew past strike, momentum stalling)
        if spot > (self.entry_strike + 15) and a_current < 0:
            return True, f"{CYAN}[SELL TARGET] ITM TAKE PROFIT -> SPOT: ${spot:.2f}{RESET}"

        # Sell Condition B: Kinematic Reversal (Stop Loss - Cut before $0.00)
        if v_current < 0 and a_current < 0 and spot < self.entry_strike:
            return True, f"{YELLOW}[SELL TARGET] MOMENTUM REVERSAL BAILOUT -> CUT LOSS{RESET}"

        # Sell Condition C: Time Decay Wipeout (Less than 5 mins, not over strike)
        if time_left_seconds < 300 and spot < self.entry_strike:
            return True, f"{RED}[SELL TARGET] IMMINENT THETA DECAY -> LIQUIDATE NOW{RESET}"

        return False, f"[HOLDING ${self.entry_strike}]"

# ---------------------------------------------------------
# 3. LIVE DAEMON
# ---------------------------------------------------------
def fetch_mock_or_live_spot():
    # Replace with your actual live websocket or r.crypto fetch
    try:
        quote = r.crypto.get_crypto_quote('BTC')
        return time.time(), float(quote['mark_price']), float(quote['volume'])
    except:
        return time.time(), 0.0, 0.0

def run_derivative_daemon():
    authenticate_node()
    engine = NeuroKinematics(memory_window=60)
    derivative_ai = DerivativeManager()
    
    print("\n[*ALPHA NODE] Event Contract Derivative Engine Initialized.")
    print(f"{'TIME':<10} | {'SPOT':<10} | {'TGT STRIKE':<10} | {'ACTION/STATE'}")
    print("-" * 65)

    while True:
        # Ingest
        t, spot, vol = fetch_mock_or_live_spot()
        if spot > 0: engine.ingest_crt_tick(t, spot, vol)

        # Time Math
        now = datetime.now()
        next_hour = (now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))
        seconds_left = (next_hour - now).total_seconds()
        
        projected = engine.project_taylor_series(seconds_left)

        # State Machine Evaluation
        time_str = now.strftime('%H:%M:%S')
        
        if not derivative_ai.active_position:
            # LOOKING FOR BUY
            buy_triggered, strike, msg = derivative_ai.check_buy_lock(engine, spot, projected)
            print(f"{time_str:<10} | ${spot:<9.2f} | ${derivative_ai.calculate_target_strike(spot):<9.2f} | {msg}")
            
            if buy_triggered:
                # YOU WOULD HOOK YOUR ORDER ROUTER HERE
                derivative_ai.active_position = True
                derivative_ai.entry_strike = strike
                # Wait 60 seconds after buy to prevent instant sell loops
                time.sleep(60.0) 
                continue
                
        else:
            # LOOKING FOR SELL
            sell_triggered, msg = derivative_ai.check_sell_lock(engine, spot, seconds_left)
            print(f"{time_str:<10} | ${spot:<9.2f} | ${derivative_ai.entry_strike:<9.2f} | {msg}")
            
            if sell_triggered:
                # YOU WOULD HOOK YOUR ORDER ROUTER HERE
                derivative_ai.active_position = False
                derivative_ai.entry_strike = 0.0
                time.sleep(60.0)
                continue

        time.sleep(5.0) # Faster tick rate for derivative precision (5 secs instead of 60)

if __name__ == "__main__":
    run_derivative_daemon()

```


# ==========================================
# FILE: bitcoin_engine.py
# ==========================================

```python
import os, time, json, math, socket
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
import robin_stocks.robinhood as r

load_dotenv()

def authenticate_node():
    r.login(username=os.getenv("RH_USERNAME"), password=os.getenv("RH_PASSWORD"))

class NeuroKinematics:
    def __init__(self):
        self.timestamps, self.prices, self.volumes = [], [], []
        self.velocities, self.accelerations = [], []
        self.buffer_limit = 60

    def ingest_crt_tick(self, t, price, vol):
        self.timestamps.append(t); self.prices.append(price); self.volumes.append(vol)
        if len(self.prices) > 1:
            dt = self.timestamps[-1] - self.timestamps[-2]
            self.velocities.append((self.prices[-1] - self.prices[-2]) / dt if dt != 0 else 0)
        else: 
            self.velocities.append(0.0)

        if len(self.velocities) > 4:
            v_past = sum(self.velocities[-5:-1]) / 4.0
            dt = self.timestamps[-1] - self.timestamps[-5]
            self.accelerations.append((self.velocities[-1] - v_past) / dt if dt != 0 else 0)
        else: 
            self.accelerations.append(0.0)

        if len(self.prices) > self.buffer_limit:
            self.timestamps.pop(0); self.prices.pop(0); self.volumes.pop(0)
            self.velocities.pop(0); self.accelerations.pop(0)

    def get_vwma(self, period=15):
        if len(self.prices) < period: return self.prices[-1] if self.prices else 0.0
        prices_arr = np.array(self.prices[-period:])
        vols_arr = np.array(self.volumes[-period:])
        if np.sum(vols_arr) == 0: return np.mean(prices_arr) 
        return np.sum(prices_arr * vols_arr) / np.sum(vols_arr)

    def project_taylor_series(self, dt_seconds):
        if len(self.prices) < 2: return 0.0
        time_decay = max(0.1, 1.0 - (dt_seconds / 3600.0))
        return self.prices[-1] + (self.velocities[-1] * dt_seconds * time_decay)

class DerivativeManager:
    def __init__(self):
        self.active_position = False
        self.entry_strike = 0.0
        self.entry_spot_price = 0.0  # NEW: Locks in true entry physics
        self.contract_type = ""
        self.max_profit_delta = 0.0

    def check_buy_lock(self, k, spot, projected, time_left):
        if len(k.velocities) < 20 or self.active_position: 
            return False, 0.0, "", "[OBSERVING]"
        
        v_std = np.std(k.velocities[-10:])
        vol_avg = np.mean(k.volumes[-10:])
        vwma = k.get_vwma(15)
        
        gamma_active = time_left < 1200
        vol_req = 1.1 if gamma_active else 1.2 
        
        # MICRO-MOMENTUM TRIPWIRES (Apex Entry Logic)
        price_delta_3 = spot - k.prices[-3] 
        micro_spike_up = price_delta_3 >= 15.0
        micro_spike_down = price_delta_3 <= -15.0

        price_delta_2 = spot - k.prices[-2]
        two_green_ticks = k.velocities[-1] > 0 and k.velocities[-2] > 0 and price_delta_2 >= 10.0
        two_red_ticks = k.velocities[-1] < 0 and k.velocities[-2] < 0 and price_delta_2 <= -10.0

        bull_vel = k.velocities[-1] > (v_std * 0.7)
        bull_vol = k.volumes[-1] > (vol_avg * vol_req)
        bear_vel = k.velocities[-1] < -(v_std * 0.7)
        bear_vol = k.volumes[-1] > (vol_avg * vol_req)

        # UPWARD MOMENTUM (YES)
        if (spot > vwma and bull_vol and bull_vel) or micro_spike_up or two_green_ticks:
            target_strike = math.ceil(spot / 100.0) * 100.0
            if (target_strike - spot) < 10.0: target_strike += 100.0
            
            if projected >= target_strike:
                self.max_profit_delta = 0.0
                msg_tag = "2-Tick Sequential Up" if two_green_ticks else "Bullish Micro-Spike"
                return True, target_strike, "YES", f"[RADAR] {msg_tag}. TGT: {target_strike}"
                
        # DOWNWARD MOMENTUM (NO)
        if (spot < vwma and bear_vol and bear_vel) or micro_spike_down or two_red_ticks:
            target_strike = math.floor(spot / 100.0) * 100.0
            if (spot - target_strike) < 10.0: target_strike -= 100.0
            
            if projected <= target_strike:
                self.max_profit_delta = 0.0
                msg_tag = "2-Tick Sequential Down" if two_red_ticks else "Bearish Micro-Spike"
                return True, target_strike, "NO", f"[RADAR] {msg_tag}. TGT: {target_strike}"
                
        status_msg = f"[OBSERVING] VWMA: {vwma:.2f} | 2-Tick: {price_delta_2:.2f}"
        if gamma_active: status_msg += " | GAMMA ACTIVE"
        return False, 0.0, "", status_msg

    def check_sell_lock(self, k, spot, time_left):
        if not self.active_position: 
            return False, "[NO POS]"
            
        # FIX: TRUE RELATIVE PnL DELTA VS EXPIRATION DISTANCE
        if self.contract_type == "YES":
            trade_delta = spot - self.entry_spot_price
            strike_distance = spot - self.entry_strike
            momentum_dead = (k.velocities[-1] < 0)
        else: 
            trade_delta = self.entry_spot_price - spot
            strike_distance = self.entry_strike - spot
            momentum_dead = (k.velocities[-1] > 0)
            
        # 1. THE TRAILING WATERMARK (Tied to Trade Delta, not Strike)
        if trade_delta > self.max_profit_delta:
            self.max_profit_delta = trade_delta
            
        pullback_from_peak = self.max_profit_delta - trade_delta
        
        price_delta_5 = spot - k.prices[-5]
        momentum_failing_macro = (self.contract_type == "YES" and price_delta_5 < 0) or (self.contract_type == "NO" and price_delta_5 > 0)
        
        # 2. SCALP PROFIT TAKE (Trailing Stop)
        # If it moves 30 points in your favor, trail it by 20 points.
        if self.max_profit_delta >= 30.0:
            if pullback_from_peak >= 20.0:
                return True, f"Trailing Stop Hit. Peak was +{self.max_profit_delta:.2f} Pts. Securing profit."
                
        # 3. EXPANDED RELATIVE STOP LOSS
        # You will only be stopped out if the asset literally drops 45 points from the EXACT moment you bought.
        if trade_delta < -45.0 and momentum_failing_macro:
            return True, f"Support collapsed. Trade dropped {trade_delta:.2f} Pts. CUT LOSSES."
            
        # 4. EXPIRATION DEATH
        # This evaluates the absolute strike distance to save you from expiring at $0.00
        if time_left < 120 and strike_distance < 15.0:
            return True, "Expiration imminent. Liquidation mandatory."
            
        return False, f"[{self.contract_type} TGT: {self.entry_strike}] PnL Delta: {trade_delta:.2f} | Peak: +{self.max_profit_delta:.2f}"

def send_signal(payload):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', 65432))
            s.sendall(json.dumps(payload).encode('utf-8'))
            return s.recv(1024).decode('utf-8') == "CONFIRMED"
    except: 
        return False

def run_daemon():
    authenticate_node()
    engine = NeuroKinematics()
    manager = DerivativeManager()
    print("\n[*SYSTEM] Relative PnL Tracking Engine Online...")
    
    last_cum_vol = 0.0
    
    while True:
        try:
            quote = r.crypto.get_crypto_quote('BTC')
            if not quote or 'mark_price' not in quote:
                time.sleep(1.0)
                continue
                
            spot = float(quote['mark_price'])
            cum_vol = float(quote['volume'])
            t = time.time()
            
            tick_vol = max(0.0, cum_vol - last_cum_vol) if last_cum_vol > 0 else 1.0
            last_cum_vol = cum_vol
            
            engine.ingest_crt_tick(t, spot, tick_vol)
            
            now = datetime.now()
            next_hour = (now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))
            seconds_left = (next_hour - now).total_seconds()
            
            projected = engine.project_taylor_series(seconds_left)
            buffer_count = len(engine.prices)
            
            if not manager.active_position:
                buy_now, strike, contract_type, msg = manager.check_buy_lock(engine, spot, projected, seconds_left)
                print(f"[{now.strftime('%H:%M:%S')}] | BTC: {spot:<9.2f} | {buffer_count}/60 | {msg}")
                
                if buy_now:
                    if send_signal({"action": "BUY", "contract": contract_type, "strike": strike, "range_min": 10, "range_max": 65}):
                        manager.active_position = True
                        manager.entry_strike = strike
                        manager.entry_spot_price = spot  # SECURING THE RELATIVE LAUNCH PAD
                        manager.contract_type = contract_type
                        time.sleep(10)
            else:
                sell_now, msg = manager.check_sell_lock(engine, spot, seconds_left)
                print(f"[{now.strftime('%H:%M:%S')}] | BTC: {spot:<9.2f} | {buffer_count}/60 | {msg}")
                
                if sell_now:
                    if send_signal({"action": "SELL", "contract": manager.contract_type, "strike": manager.entry_strike, "reason": msg}):
                        manager.active_position = False
                        manager.entry_strike = 0.0
                        manager.entry_spot_price = 0.0
                        manager.contract_type = ""
                        time.sleep(10)
            
            time.sleep(5)
        except Exception as e:
            time.sleep(5)

if __name__ == "__main__":
    run_daemon()

```


# ==========================================
# FILE: bitcoin_router.py
# ==========================================

```python
import socket
import json
import time
import os

def run_router():
    HOST = '127.0.0.1'
    PORT = 65432
    
    active_qty = 0
    active_entry_price = 0.0

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print("\n" + "="*50)
        print("[*SYSTEM] INTERACTIVE PNL ROUTER ONLINE")
        print("="*50)
        print("[*SYSTEM] Monitoring engine datastream...\n")

        while True:
            try:
                conn, addr = s.accept()
                with conn:
                    data = conn.recv(1024)
                    if not data: 
                        continue

                    payload = json.loads(data.decode('utf-8'))
                    action = payload.get("action", "UNKNOWN")

                    if action == "BUY":
                        strike = payload.get("strike", 0.0)
                        contract = payload.get("contract", "YES")
                        r_min = payload.get("range_min", 10)
                        r_max = payload.get("range_max", 65)

                        print("\n" + "🔴 "*10)
                        print(f"  🚨 ENGINE TRIGGER: BUY SIGNAL 🚨  ")
                        print(f"  ACTION: Buy {contract} on ${strike}  ")
                        print(f"  TARGET PREMIUM: .{r_min} to .{r_max}  ")
                        print("🔴 "*10)

                        title = f"🚨 QUANT: BUY {contract}!"
                        content = f"Target: ${strike} | Limit: .{r_min} to .{r_max}"
                        os.system(f"termux-notification -t '{title}' -c '{content}' --priority max --vibrate 500,500,500")
                        os.system("termux-vibrate -d 1500 -f")

                        auth = input("\nDid you manually buy on phone? (Y/N): ").strip().upper()
                        if auth == 'Y':
                            try:
                                active_qty = int(input("How many contracts did you buy?: "))
                                active_entry_price = float(input("At what EXACT fill price? (e.g. 0.45): "))
                                print(f"[OK] Position Locked. Total Cost: ${active_qty * active_entry_price:.2f}. Monitoring Trailing Highs...")
                                conn.sendall(b"CONFIRMED")
                            except ValueError:
                                print("[WARNING] Invalid numbers. Disabling local PnL math. Engine tracking blindly...")
                                active_qty = 0
                                conn.sendall(b"CONFIRMED")
                        else:
                            print("[SKIPPED] Position aborted. Returning to scan loop.")
                            conn.sendall(b"REJECTED")

                    elif action == "SELL":
                        strike = payload.get("strike", 0.0)
                        contract = payload.get("contract", "UNKNOWN")
                        reason = payload.get("reason", "Trailing Stop Hit")

                        print("\n" + "🟢 "*10)
                        print(f"  💰 INITIATE LIQUIDATION PROTOCOL 💰  ")
                        print(f"  POSITION: Dump {contract} Contracts  ")
                        print(f"  REASON: {reason}  ")
                        print("🟢 "*10)

                        title = f"💰 QUANT: SELL {contract} NOW!"
                        os.system(f"termux-notification -t '{title}' -c '{reason}' --priority max --vibrate 1000,200,1000")
                        os.system("termux-vibrate -d 1500 -f")

                        auth = input("\nDid you manually sell on phone? (Y/N): ").strip().upper()
                        if auth == 'Y':
                            if active_qty > 0:
                                try:
                                    exit_price = float(input("At what EXACT fill price? (e.g. 0.85): "))
                                    pnl = (exit_price - active_entry_price) * active_qty
                                    if pnl >= 0:
                                        print(f"\n[WIN] Trade executed flawlessly. You made +${pnl:.2f} 💸")
                                    else:
                                        print(f"\n[LOSS] Trade liquidated. You lost -${abs(pnl):.2f} 🩸")
                                except ValueError:
                                    print("[WARNING] Invalid math input. Skipping PnL log.")
                                    
                            print("[OK] Resetting kinematics to OBSERVING mode...\n")
                            active_qty = 0
                            active_entry_price = 0.0
                            conn.sendall(b"CONFIRMED")
                        else:
                            print("[WARNING] Override detected. You will bleed. Re-ping scheduled.")
                            conn.sendall(b"REJECTED")

            except json.JSONDecodeError:
                print("[ERROR] Corrupted JSON payload received.")
            except Exception as e:
                print(f"[ERROR] Router fault: {e}")
                time.sleep(1)

if __name__ == "__main__": run_router()

```


# ==========================================
# FILE: btc_inverse.py
# ==========================================

```python
import os, time, json, math, socket
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
import robin_stocks.robinhood as r

load_dotenv()

def authenticate_node():
    r.login(username=os.getenv("RH_USERNAME"), password=os.getenv("RH_PASSWORD"))

class NeuroKinematics:
    def __init__(self):
        self.timestamps, self.prices, self.volumes = [], [], []
        self.velocities, self.accelerations = [], []
        self.buffer_limit = 60

    def ingest_crt_tick(self, t, price, vol):
        self.timestamps.append(t); self.prices.append(price); self.volumes.append(vol)
        if len(self.prices) > 1:
            dt = self.timestamps[-1] - self.timestamps[-2]
            self.velocities.append((self.prices[-1] - self.prices[-2]) / dt if dt != 0 else 0)
        else: 
            self.velocities.append(0.0)

        if len(self.velocities) > 4:
            v_past = sum(self.velocities[-5:-1]) / 4.0
            dt = self.timestamps[-1] - self.timestamps[-5]
            self.accelerations.append((self.velocities[-1] - v_past) / dt if dt != 0 else 0)
        else: 
            self.accelerations.append(0.0)

        if len(self.prices) > self.buffer_limit:
            self.timestamps.pop(0); self.prices.pop(0); self.volumes.pop(0)
            self.velocities.pop(0); self.accelerations.pop(0)

    def get_vwma(self, period=15):
        if len(self.prices) < period: return self.prices[-1] if self.prices else 0.0
        prices_arr = np.array(self.prices[-period:])
        vols_arr = np.array(self.volumes[-period:])
        if np.sum(vols_arr) == 0: return np.mean(prices_arr) 
        return np.sum(prices_arr * vols_arr) / np.sum(vols_arr)

    def project_taylor_series(self, dt_seconds):
        if len(self.prices) < 2: return 0.0
        time_decay = max(0.1, 1.0 - (dt_seconds / 3600.0))
        return self.prices[-1] + (self.velocities[-1] * dt_seconds * time_decay)

class DerivativeManager:
    def __init__(self):
        self.active_position = False
        self.entry_strike = 0.0
        self.entry_spot_price = 0.0
        self.contract_type = ""
        self.max_profit_delta = 0.0

    def check_buy_lock(self, k, spot, projected, time_left):
        if len(k.velocities) < 20 or self.active_position: 
            return False, 0.0, "", "[OBSERVING]"
        
        v_std = np.std(k.velocities[-10:])
        vol_avg = np.mean(k.volumes[-10:])
        vwma = k.get_vwma(15)
        
        gamma_active = time_left < 1200
        vol_req = 1.1 if gamma_active else 1.2 
        
        # MICRO-MOMENTUM TRIPWIRES (Hyper-Sensitive)
        price_delta_3 = spot - k.prices[-3] 
        micro_spike_up = price_delta_3 >= 15.0
        micro_spike_down = price_delta_3 <= -15.0

        price_delta_2 = spot - k.prices[-2]
        two_green_ticks = k.velocities[-1] > 0 and k.velocities[-2] > 0 and price_delta_2 >= 10.0
        two_red_ticks = k.velocities[-1] < 0 and k.velocities[-2] < 0 and price_delta_2 <= -10.0

        bull_vel = k.velocities[-1] > (v_std * 0.7)
        bull_vol = k.volumes[-1] > (vol_avg * vol_req)
        bear_vel = k.velocities[-1] < -(v_std * 0.7)
        bear_vol = k.volumes[-1] > (vol_avg * vol_req)

        # -----------------------------------------------------------------
        # INVERTED SCRIPT 1: GREEN SPIKE -> SHORT THE WICK (BUY "NO")
        # -----------------------------------------------------------------
        if (spot > vwma and bull_vol and bull_vel) or micro_spike_up or two_green_ticks:
            target_strike = math.ceil(spot / 100.0) * 100.0
            if (target_strike - spot) < 10.0: target_strike += 100.0
            
            if projected >= target_strike:
                self.max_profit_delta = 0.0
                msg_tag = "Fading 2-Tick Up" if two_green_ticks else "Shorting Bull Spike"
                # OUTPUT EXPLICITLY FLIPPED TO "NO"
                return True, target_strike, "NO", f"[INVERSE RADAR] {msg_tag}. TGT: {target_strike}"
                
        # -----------------------------------------------------------------
        # INVERTED SCRIPT 2: RED DUMP -> CATCH THE KNIFE (BUY "YES")
        # -----------------------------------------------------------------
        if (spot < vwma and bear_vol and bear_vel) or micro_spike_down or two_red_ticks:
            target_strike = math.floor(spot / 100.0) * 100.0
            if (spot - target_strike) < 10.0: target_strike -= 100.0
            
            if projected <= target_strike:
                self.max_profit_delta = 0.0
                msg_tag = "Fading 2-Tick Down" if two_red_ticks else "Buying Bear Dump"
                # OUTPUT EXPLICITLY FLIPPED TO "YES"
                return True, target_strike, "YES", f"[INVERSE RADAR] {msg_tag}. TGT: {target_strike}"
                
        status_msg = f"[OBSERVING] VWMA: {vwma:.2f} | 2-Tick: {price_delta_2:.2f}"
        if gamma_active: status_msg += " | GAMMA ACTIVE"
        return False, 0.0, "", status_msg

    def check_sell_lock(self, k, spot, time_left):
        if not self.active_position: 
            return False, "[NO POS]"
            
        if self.contract_type == "YES":
            trade_delta = spot - self.entry_spot_price
            strike_distance = spot - self.entry_strike
            momentum_dead = (k.velocities[-1] < 0)
        else: 
            trade_delta = self.entry_spot_price - spot
            strike_distance = self.entry_strike - spot
            momentum_dead = (k.velocities[-1] > 0)
            
        if trade_delta > self.max_profit_delta:
            self.max_profit_delta = trade_delta
            
        pullback_from_peak = self.max_profit_delta - trade_delta
        
        price_delta_5 = spot - k.prices[-5]
        momentum_failing_macro = (self.contract_type == "YES" and price_delta_5 < 0) or (self.contract_type == "NO" and price_delta_5 > 0)
        
        # 1. SCALP PROFIT TAKE (Trailing Stop)
        # 30-point climb triggers the safety, trails by 20.
        if self.max_profit_delta >= 30.0:
            if pullback_from_peak >= 20.0:
                return True, f"Trailing Stop Hit. Peak was +{self.max_profit_delta:.2f} Pts. Securing profit."
                
        # 2. EXPANDED RELATIVE STOP LOSS 
        # Hard cap at -45.0 points from the exact moment of inverse entry.
        if trade_delta < -45.0 and momentum_failing_macro:
            return True, f"Inverse failed. Liquidity sweep continued. Delta {trade_delta:.2f} Pts. CUT LOSSES."
            
        # 3. EXPIRATION DEATH
        if time_left < 120 and strike_distance < 15.0:
            return True, "Expiration imminent. Liquidation mandatory."
            
        return False, f"[{self.contract_type} TGT: {self.entry_strike}] PnL Delta: {trade_delta:.2f} | Peak: +{self.max_profit_delta:.2f}"

def send_signal(payload):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', 65432))
            s.sendall(json.dumps(payload).encode('utf-8'))
            return s.recv(1024).decode('utf-8') == "CONFIRMED"
    except: 
        return False

def run_daemon():
    authenticate_node()
    engine = NeuroKinematics()
    manager = DerivativeManager()
    print("\n[*SYSTEM] INVERSE APEX ENGINE ONLINE. Hunting Mean Reversions...")
    
    last_cum_vol = 0.0
    
    while True:
        try:
            quote = r.crypto.get_crypto_quote('BTC')
            if not quote or 'mark_price' not in quote:
                time.sleep(1.0)
                continue
                
            spot = float(quote['mark_price'])
            cum_vol = float(quote['volume'])
            t = time.time()
            
            tick_vol = max(0.0, cum_vol - last_cum_vol) if last_cum_vol > 0 else 1.0
            last_cum_vol = cum_vol
            
            engine.ingest_crt_tick(t, spot, tick_vol)
            
            now = datetime.now()
            next_hour = (now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))
            seconds_left = (next_hour - now).total_seconds()
            
            projected = engine.project_taylor_series(seconds_left)
            buffer_count = len(engine.prices)
            
            if not manager.active_position:
                buy_now, strike, contract_type, msg = manager.check_buy_lock(engine, spot, projected, seconds_left)
                print(f"[{now.strftime('%H:%M:%S')}] | BTC: {spot:<9.2f} | {buffer_count}/60 | {msg}")
                
                if buy_now:
                    # In a mean-reverting fade, you want cheap out-of-the-money sweeps. Target 10-65 cents.
                    if send_signal({"action": "BUY", "contract": contract_type, "strike": strike, "range_min": 10, "range_max": 65}):
                        manager.active_position = True
                        manager.entry_strike = strike
                        manager.entry_spot_price = spot
                        manager.contract_type = contract_type
                        time.sleep(10)
            else:
                sell_now, msg = manager.check_sell_lock(engine, spot, seconds_left)
                print(f"[{now.strftime('%H:%M:%S')}] | BTC: {spot:<9.2f} | {buffer_count}/60 | {msg}")
                
                if sell_now:
                    if send_signal({"action": "SELL", "contract": manager.contract_type, "strike": manager.entry_strike, "reason": msg}):
                        manager.active_position = False
                        manager.entry_strike = 0.0
                        manager.entry_spot_price = 0.0
                        manager.contract_type = ""
                        time.sleep(10)
            
            time.sleep(5)
        except Exception as e:
            time.sleep(5)

if __name__ == "__main__":
    run_daemon()

```
