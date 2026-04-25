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

