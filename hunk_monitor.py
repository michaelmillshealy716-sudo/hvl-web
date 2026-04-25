import time
import numpy as np
import yfinance as yf
import plotext as plt
import os
import warnings

# Suppress API noise
warnings.filterwarnings("ignore")

# --- HEALY VECTOR LABS: VERITAS V4.3 (FASE MACRO-LINK) ---

def get_euler_intrinsic(p_list):
    """The FASE Engine: Strips high-frequency noise via FFT"""
    if len(p_list) < 10: return p_list[-1]
    f = np.fft.fft(p_list)
    f[len(f)//4:] = 0
    return np.real(np.fft.ifft(f)[-1])

def get_taylor_truth(p_hist):
    """Velocity Engine: 2nd-Order Taylor Acceleration"""
    if len(p_hist) < 3: return 0.0
    v = p_hist[-1] - p_hist[-2]
    a = (p_hist[-1] - 2*p_hist[-2] + p_hist[-3])
    return abs((v * 0.5) + (a * 1.5)) * 10

def detect_markov_regime(t_score):
    """Markov State Identification"""
    if t_score > 4.10: return "BREAKOUT 🚀"
    elif t_score < 1.0: return "NOISE 🛑"
    else: return "STABLE 🏛️"

# THE MACRO FLEET: USO = Commodity Truth | XOM = Equity Lag
tickers = ['NVDA', 'TSLA', 'TSLL', 'XOM', 'USO', 'ERX']

print("Establishing FASE Macro Uplink... Calibrating Energy Correlates.")

try:
    while True:
        # 1. Ingest Live Market Tape
        data = yf.download(tickers, period="1d", interval="1m", progress=False)
        close_data = data['Close'] if 'Close' in data.columns else data['Adj Close']
        
        # 2. Clear Screen for FASE Dashboard
        os.system('clear')
        print(f"--- HEALY VECTOR LABS | FASE V4.3 | {time.strftime('%H:%M:%S')} ---")
        
        # 3. MACRO VISUALIZER: USO (Commodity) vs XOM (Equity)
        try:
            a_ticker, b_ticker = 'USO', 'XOM' 
            a_p = close_data[a_ticker].dropna().values[-35:]
            b_p = close_data[b_ticker].dropna().values[-35:]
            
            if len(a_p) > 20:
                a_z, b_z = [], []
                for i in range(15, len(a_p) + 1):
                    win_a, win_b = a_p[:i], b_p[:i]
                    mu_a, sig_a = get_euler_intrinsic(win_a), np.std(win_a)
                    a_z.append((win_a[-1] - mu_a) / sig_a if sig_a > 0 else 0)
                    mu_b, sig_b = get_euler_intrinsic(win_b), np.std(win_b)
                    b_z.append((win_b[-1] - mu_b) / sig_b if sig_b > 0 else 0)

                plt.clf()
                plt.title(f"FASE Macro Gap: {a_ticker} (Blue) vs {b_ticker} (Red)")
                plt.plot(a_z, label=f"{a_ticker} Z", color="blue")
                plt.plot(b_z, label=f"{b_ticker} Z", color="red")
                plt.hline(0, color="white") 
                plt.plotsize(65, 12)
                plt.show()
                
                delta = a_z[-1] - b_z[-1]
                print(f"\n[FASE ARBITRAGE DELTA]: {delta:.4f} sigma")
        except Exception as e:
            print(f"[!] Syncing FASE Correlates...")

        # 4. THE SOVEREIGN FLEET HUD
        print("\n{:<6} {:<10} {:<10} {:<8} {:<15}".format("TICKER", "PRICE", "Z-SCORE", "TRUTH", "REGIME"))
        print("-" * 65)
        for t in tickers:
            try:
                p_win = close_data[t].dropna().values[-30:]
                if len(p_win) < 5: continue
                
                curr_p = p_win[-1]
                mu = get_euler_intrinsic(p_win)
                sigma = np.std(p_win)
                z = (curr_p - mu) / sigma if sigma > 0 else 0
                truth = get_taylor_truth(p_win)
                regime = detect_markov_regime(truth)
                
                print("{:<6} ${:<9.2f} {:<10.2f} {:<8.4f} {:<15}".format(t, curr_p, z, truth, regime))
            except: pass
                
        time.sleep(60)

except KeyboardInterrupt:
    print("\n[!] Lead Architect terminated FASE Engine. Standing By.")

