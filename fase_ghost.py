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

