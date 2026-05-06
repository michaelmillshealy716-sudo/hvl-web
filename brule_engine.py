import robin_stocks.robinhood as rh
import yfinance as yf
import time
import sys
import os
import numpy as np
from datetime import datetime, timedelta
import logging

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

# --- BRULE CONFIGURATION ---
WATCHLIST = ["GPRO", "AMC", "GME", "SPCE","WTI", "PLTR", "TSLA"]
MAX_BULLETS = 1 # BP is strictly constrained. 1 bullet maximum.

ACTIVE_TRADES = {}
HISTORY = {ticker: {"prices": [], "hunk_score": None} for ticker in WATCHLIST}

def rh_login():
    try:
        print(f"{C.CYAN}[*] INITIATING BRULE ROBINHOOD HANDSHAKE...{C.END}")
        # ENTER YOUR PASSWORD BELOW
        rh.login("michaelmillshealy716@gmail.com", "YOUR_PASSWORD_HERE", expiresIn=86400)
        profile = rh.account.load_account_profile()
        print(f"{C.G}[+] HANDSHAKE SUCCESSFUL. BP: ${profile.get('buying_power', '0.00')}{C.END}")
    except Exception as e:
        print(f"{C.R}[!] AUTH FAIL: {e}{C.END}")
        sys.exit(1)

def is_hunting_window():
    """The Time Gate: Only hunts during high-probability momentum windows"""
    now = datetime.now()
    current_time = now.hour * 100 + now.minute
    # Morning: 9:35 AM - 10:30 AM | Power Hour: 3:40 PM - 3:55 PM (EST)
    return (935 <= current_time <= 1030) or (1540 <= current_time <= 1555)

def get_hunk_score(ticker):
    """Caches the yfinance data to eliminate rate-limiting"""
    if HISTORY[ticker]["hunk_score"] is not None:
        return HISTORY[ticker]["hunk_score"]
    try:
        info = yf.Ticker(ticker).info
        sf = info.get("shortPercentOfFloat", 0) or 0
        if sf < 1: sf *= 100
        dtc = info.get("shortRatio", 0) or 0
        score = (sf * 0.7) + (dtc * 0.3)
        HISTORY[ticker]["hunk_score"] = score
        return score
    except Exception:
        HISTORY[ticker]["hunk_score"] = 0
        return 0

def find_cheap_call(ticker):
    """The Premium Gate: Searches ONLY for $0.03 - $0.20 CALL contracts. Includes 0DTE Block."""
    try:
        chains = rh.options.get_chains(ticker)
        if not chains or not chains.get('expiration_dates'): return None
        
        # [!!!] 0DTE GUILLOTINE: Filter out expirations less than 2 days away to avoid Theta trap
        valid_expirations = []
        for exp in chains['expiration_dates']:
            exp_date = datetime.strptime(exp, "%Y-%m-%d")
            dte = (exp_date - datetime.now()).days
            if dte >= 2:
                valid_expirations.append(exp)
                
        if not valid_expirations: return None
        front_month = valid_expirations[0]

        valid_options = rh.options.find_options_by_expiration(ticker, expirationDate=front_month, optionType='call')
        
        # DELTA/THETA RATIO: Maintain strict pricing constraints
        valid = [o for o in valid_options if o['ask_price'] and 0.03 <= float(o['ask_price']) <= 0.20]
        
        if not valid: return None
        valid.sort(key=lambda x: float(x['volume'] or 0), reverse=True)
        return valid[0]
    except Exception as e:
        print(f"{C.R}[!] Options Scan Error: {e}{C.END}")
        return None

def manage_positions():
    """PURE TAKE-PROFIT BRACKET FOR OPTIONS (18.5% GAIN)"""
    if not ACTIVE_TRADES: return
    
    # Use list() to avoid dictionary modification runtime errors during iteration
    for ticker, data in list(ACTIVE_TRADES.items()):
        opt = data['option']
        entry_premium = float(data['entry_premium'])
        try:
            market_data = rh.options.get_option_market_data(ticker, opt['expiration_date'], opt['strike_price'], 'call')
            if not market_data: continue
            
            # [!!!] JSON PARSING FIX: Strip the list container before accessing dict keys
            option_info = market_data[0]
            if isinstance(option_info, list):
                option_info = option_info[0]
                
            current_bid = float(option_info.get('bid_price', 0))
            if current_bid == 0: continue
            
            profit_pct = ((current_bid - entry_premium) / entry_premium) * 100
            
            if profit_pct >= 18.5:
                print(f"\n{C.G}[$$$] AUTO-SELL FIRED: +{profit_pct:.2f}% SQUEEZE TARGET SECURED ON {ticker}{C.END}")
                rh.orders.order_sell_option_limit("close", "credit", round(current_bid, 2), ticker, 1, opt['expiration_date'], opt['strike_price'], 'call')
                del ACTIVE_TRADES[ticker]
        except Exception as e:
            print(f"{C.Y}[!] Bracket manager ping failed for {ticker}: {e}{C.END}")
            continue

def execute_trade(ticker, price, target_opt):
    print(f"\n{C.G}[+] SECURED SQUEEZE CONTRACT: {ticker} CALL | Strike: ${target_opt['strike_price']} | Premium: ${target_opt['ask_price']}{C.END}")
    try:
        # LIVE EXECUTION BLOCK
        rh.orders.order_buy_option_limit("open", "debit", target_opt['ask_price'], ticker, 1, target_opt['expiration_date'], target_opt['strike_price'], 'call')
        print(f"{C.G}[$$$] LIVE ORDER EXECUTED ON ROBINHOOD.{C.END}")
    except Exception as e:
        print(f"{C.R}[!] FAILED TO EXECUTE LIVE ORDER: {e}{C.END}")
        return
        
    ACTIVE_TRADES[ticker] = {
        "entry_price": price,
        "entry_premium": float(target_opt['ask_price']),
        "option": target_opt,
        "timestamp": datetime.now()
    }
    print(f"{C.CYAN}[+] PURE TAKE-PROFIT BRACKET LOCKED (18.5%).{C.END}")

def hunk_dump_execution():
    print(f"\r{C.B}[*] BRULE KINEMATIC SCAN @ {datetime.now().strftime('%H:%M:%S')}{C.END}      ", end="")
    
    old_stderr = sys.stderr
    sys.stderr = open(os.devnull, 'w')
    try:
        quotes = rh.stocks.get_quotes(WATCHLIST)
        current_prices = {q['symbol']: float(q['last_trade_price']) for q in quotes if q}
    except Exception:
        sys.stderr = old_stderr
        return
    finally:
        sys.stderr = old_stderr
        
    for ticker in WATCHLIST:
        if ticker in ACTIVE_TRADES: continue
        price = current_prices.get(ticker, 0)
        if price == 0: continue
        
        hunk = get_hunk_score(ticker)
        prices = HISTORY[ticker]["prices"]
        prices.append(price)
        if len(prices) > 3: prices.pop(0)
        
        acc = 0.0
        if len(prices) == 3:
            v1 = prices[-1] - prices[-2]
            v2 = prices[-2] - prices[-3]
            acc = v1 - v2
            
        status = f"{C.CYAN}[WAIT]{C.END}" if acc <= 0 else f"{C.G}[LIVE]{C.END}"
        print(f"\n{status} {ticker:4} | Price: ${price:7.2f} | Accel: {acc:6.2f} | Hunk: {hunk:5.2f}")
        
        # [!!!] MEME DAMPENER: Require higher acceleration for high-IV tickers
        acc_threshold = 0.08 if ticker in ["GME", "AMC"] else 0.05
        
        if acc > acc_threshold and hunk > 10 and len(prices) == 3:
            target_opt = find_cheap_call(ticker)
            if target_opt:
                print(f"\n{C.M}{C.BBLD}[!!!] SQUEEZE DETECTED: {ticker} | Accel: {acc:.2f} | Hunk: {hunk:.2f}{C.END}")
                execute_trade(ticker, price, target_opt)
                return # Pause scanning if bullet fired

if __name__ == "__main__":
    rh_login()
    print(f"{C.BBLD}{C.Y}[!] HEALY VECTOR LABS: BRULE OPTIONS ENGINE ENGAGED{C.END}")
    try:
        while True:
            if len(ACTIVE_TRADES) >= MAX_BULLETS:
                print(f"\r{C.Y}[!] BULLET SECURED ({len(ACTIVE_TRADES)}/{MAX_BULLETS}). MONITORING OPTIONS BRACKETS ONLY.{C.END}", end="")
                manage_positions()
                time.sleep(2)
            elif not is_hunting_window():
                print(f"\r{C.Y}[Zzz] OUTSIDE HUNTING WINDOWS. SNIPER RESTING. BRACKET MANAGER ACTIVE.{C.END}", end="")
                manage_positions()
                time.sleep(10)
            else:
                hunk_dump_execution()
                manage_positions()
                time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{C.R}[!!!] EMERGENCY BRAKE PULLED. BRULE ENGINE SHUTTING DOWN.{C.END}")
        sys.exit(0)

