import os
import time
import numpy as np
import requests
from datetime import datetime
from dotenv import load_dotenv

# --- CREDENTIALS ---
load_dotenv(override=True)
ALPACA_KEY = os.environ.get("ALPACA_API_KEY", "").strip()
ALPACA_SECRET = os.environ.get("ALPACA_API_SECRET", "").strip()

# --- ANSI COLORS ---
PERI, FUCHSIA, GOLD, ORANGE = "\033[38;5;147m", "\033[38;5;201m", "\033[38;5;220m", "\033[38;5;208m"
GREEN, RED, RESET, FLASH, BOLD = "\033[92m", "\033[91m", "\033[0m", "\033[5m", "\033[1m"

# --- EXPANDED ASSET LOAD ---
CRYPTO = ["ADA/USD", "BTC/USD", "ETH/USD"]
STOCKS = ["TSLA", "NVDA", "AAPL", "META", "AMD", "SOFI", "MSTR", "TSLL", "XOM", "MO", "USO", "AMC", "GPRO"]
ALL_TICKERS = CRYPTO + STOCKS

# --- TRACKERS ---
price_history = {t: [0.0] * 50 for t in ALL_TICKERS}
potential_pos = {t: 0 for t in ALL_TICKERS}
potential_neg = {t: 0 for t in ALL_TICKERS}
compression_cycles = {t: 0 for t in ALL_TICKERS}
post_drop_brew = {t: False for t in ALL_TICKERS}
initialized = set()
pulse_count = 0
integral_reset_counter = 0

def get_quantum_state(prices):
    active_prices = [p for p in prices if p > 0]
    if len(active_prices) < 2: return 0.0, 0.0, 0.0
    prices_arr = np.array(active_prices)
    returns = np.diff(prices_arr) / prices_arr[:-1]
    
    psi = np.mean(np.abs(returns)) * 10000
    delta = ((prices_arr[-1] - prices_arr[0]) / prices_arr[0]) * 100
    phi = psi / max(0.01, abs(delta))
    return psi, delta, phi

def fetch_prices():
    headers = {"APCA-API-KEY-ID": ALPACA_KEY, "APCA-API-SECRET-KEY": ALPACA_SECRET}
    prices = {}
    try:
        c_res = requests.get(f"https://data.alpaca.markets/v1beta3/crypto/us/latest/trades?symbols={','.join(CRYPTO)}", headers=headers, timeout=5)
        if c_res.status_code == 200:
            for t, d in c_res.json().get('trades', {}).items(): prices[t] = d['p']
        s_res = requests.get(f"https://data.alpaca.markets/v2/stocks/trades/latest?symbols={','.join(STOCKS)}&feed=iex", headers=headers, timeout=5)
        if s_res.status_code == 200:
            for t, d in s_res.json().get('trades', {}).items(): prices[t] = d['p']
        return prices
    except: return {}

def veritas_bridge(ticker, price, price_history_array):
    """
    VERITAS TRUTH FILTER: 3rd-Order Taylor Series Expansion
    Projects the t+1 price action using local derivatives.
    """
    if len(price_history_array) < 4:
        return False # Insufficient data for 3rd-order calculation
        
    p = np.array(price_history_array)
    
    # Kinematics of the Price Action
    v = p[-1] - p[-2] # 1st Derivative (Velocity)
    a = (p[-1] - p[-2]) - (p[-2] - p[-3]) # 2nd Derivative (Acceleration)
    j = ((p[-1] - p[-2]) - (p[-2] - p[-3])) - ((p[-2] - p[-3]) - (p[-3] - p[-4])) # 3rd Deriv (Jerk)
    
    # Taylor Series Projection for t+1 (dt = 1)
    p_next = p[-1] + v + (0.5 * a) + (0.1667 * j)
    
    # The Logic Gate
    if p_next > p[-1]:
        return True # Mathematical trajectory is positive. Clear to engage.
    return False # False breakout detected. Hold fire.

def execute_strike(ticker, price):
    """
    THE MUSCLE: Alpaca API Live Order Routing
    """
    print(f"\n{FLASH}{BOLD}{GOLD}>>> EXECUTING VERITAS STRIKE: {ticker} @ ${price} <<<{RESET}")
    
    # Format ticker for Alpaca API (e.g., "BTC/USD" -> "BTCUSD")
    alpaca_sym = ticker.replace("/", "")
    
    url = "https://paper-api.alpaca.markets/v2/orders" # Set to paper for final Sunday prototype
    headers = {
        "APCA-API-KEY-ID": ALPACA_KEY,
        "APCA-API-SECRET-KEY": ALPACA_SECRET,
        "accept": "application/json",
        "content-type": "application/json"
    }
    
    payload = {
        "symbol": alpaca_sym,
        "qty": "0.01", # Adjust position sizing here
        "side": "buy",
        "type": "market",
        "time_in_force": "gtc"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print(f"{GREEN}[+] ALIGNMENT SECURED: Market Order Filled for {ticker}.{RESET}\n")
        else:
            print(f"{RED}[-] STRIKE REJECTED: {response.text}{RESET}\n")
    except Exception as e:
        print(f"{RED}[-] API BRIDGE OFFLINE: {e}{RESET}\n")

if __name__ == "__main__":
    while True:
        data = fetch_prices()
        if not data:
            time.sleep(1)
            continue
            
        pulse_count += 1
        integral_reset_counter += 1
        
        # --- UI Refresh ---
        print(f"\033[2J\033[H", end="")
        print(f"{PERI}FASE MASTER v7.0.0 - VERITAS INJECTED | {datetime.now().strftime('%H:%M:%S')} | PREDATOR MODE | PULSE: {pulse_count}{RESET}")
        print("-" * 110)
        
        if integral_reset_counter > 500:
            print(f"{BOLD}{FUCHSIA}*** SYSTEM RESET: INDEFINITE INTEGRAL BIAS CLEARED ***{RESET}")
            integral_reset_counter = 0
            
        for t in ALL_TICKERS:
            raw_p = data.get(t)
            if not raw_p: continue
            
            if t not in initialized or raw_p != price_history[t][-1]:
                price_history[t].append(raw_p)
                price_history[t].pop(0)
                initialized.add(t)
                
            psi, delta, phi = get_quantum_state(price_history[t])
            
            # --- DUAL-POLARITY HIERARCHY ---
            if psi > 5.0:
                potential_pos[t] += 1; potential_neg[t] = 0
            elif psi < -5.0:
                potential_neg[t] += 1; potential_pos[t] = 0
            else:
                potential_pos[t] = 0; potential_neg[t] = 0
                
            m_pos, m_neg = potential_pos[t], potential_neg[t]
            clean_status = "STABLE"
            status = "STABLE"
            
            if m_neg > 10: post_drop_brew[t] = True
            if m_pos > 10: post_drop_brew[t] = False
            
            if m_pos > m_neg:
                f_t_col = FUCHSIA if m_pos > 25 else GREEN
                status = f"{FLASH}SINGULARITY{RESET}" if m_pos > 25 else "BREWING"
            elif m_neg > m_pos:
                f_t_col = RED
                status = "DROP BREW" if m_neg > 25 else "STABLE"
            else:
                f_t_col = PERI
                status = "STABLE"
                
            # --- COMPRESSION LOGIC (VERITAS RECALIBRATED) ---
            if phi > 15.0 and abs(delta) < 0.55 and psi > 2.0:
                compression_cycles[t] += 1
                status = f"{FLASH}{BOLD}COMPRESS [{compression_cycles[t]}]{RESET}"
                clean_status = "COMPRESSION"
            elif abs(delta) > 1.2 or (m_pos == 50 and delta > 0.7):
                compression_cycles[t] = 0
                status = f"{GOLD}COILED [{compression_cycles[t]}]{RESET}"
                clean_status = "COILED"
            elif compression_cycles[t] > 0:
                status = f"{GOLD}COILED [{compression_cycles[t]}]{RESET}"
                clean_status = "COILED"
                
            # --- STRIKE EXECUTION ---
            if clean_status == "COMPRESSION" and compression_cycles[t] >= 10 and post_drop_brew[t]:
                if veritas_bridge(t, raw_p, price_history[t]):
                    execute_strike(t, raw_p)
                    
            d_sign = GREEN if delta >= 0 else RED
            f_val = m_pos if m_pos > m_neg else -m_neg
            
            print(f"{t:<8} | $ {raw_p:>10.4f} | Psi: {psi:>8.4f} | Delta: {d_sign}{delta:>7.2f}%{RESET} | Phi: {phi:>7.2f} | {f_t_col}{status:<18}{RESET}")
            
        time.sleep(1)

