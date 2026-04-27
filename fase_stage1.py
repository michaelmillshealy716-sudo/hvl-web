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

