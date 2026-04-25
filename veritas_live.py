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
