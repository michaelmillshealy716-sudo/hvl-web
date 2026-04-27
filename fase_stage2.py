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

