import json
import subprocess
import time
import sys
import os
import numpy as np
import robin_stocks.robinhood as rh
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

# THE THREE BULLET RULE
MAX_BULLETS = 3
ACTIVE_TRADES = {}

# [!!!] NOTE: Paste your entire "Purged Matrix" of 100+ tickers here. 
# I have added WTI as requested.
STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "AMD", "GME", "AMC", "WTI"
    # <-- PASTE YOUR FULL MATRIX HERE -->
]

def rh_login():
    try:
        print(f"{C.CYAN}[*] INITIATING BRULE ROBINHOOD HANDSHAKE...{C.END}")
        # ENTER YOUR PASSWORD BELOW
        rh.login("michaelmillshealy716@gmail.com", "YOUR_PASSWORD_HERE", expiresIn=86400)
        profile = rh.account.load_account_profile()
        print(f"{C.G}[+] AUTH SUCCESSFUL. WALLET SECURED. BP: ${profile.get('buying_power', '0.00')}{C.END}")
    except Exception as e:
        print(f"{C.R}[!] AUTH FAIL: {e}{C.END}")
        sys.exit(1)

def get_wallet():
    try:
        profile = rh.account.load_account_profile()
        return float(profile['buying_power'])
    except Exception:
        return 0.0

def get_kinematics(prices):
    if len(prices) < 4: return 0.0, 0.0, 0.0
    p = np.array(prices[-4:], dtype=float)
    v = np.gradient(p)
    a = np.gradient(v)
    return v[-1], a[-1], p[-1]

def find_cheap_option(ticker, opt_type):
    try:
        chains = rh.options.get_chains(ticker)
        if not chains or not chains.get('expiration_dates'):
            return None
            
        # --- THE 0DTE GUILLOTINE ---
        # Strip out contracts expiring today or tomorrow to avoid forced liquidations
        valid_expirations = []
        for exp in chains['expiration_dates']:
            exp_date = datetime.strptime(exp, "%Y-%m-%d")
            dte = (exp_date - datetime.now()).days
            if dte >= 2:
                valid_expirations.append(exp)
                
        if not valid_expirations: return None
        front_month = valid_expirations[0]

        valid_options = rh.options.find_options_by_expiration(
            ticker, expirationDate=front_month, optionType=opt_type.lower()
        )
        
        valid = [o for o in valid_options if o['ask_price'] and 0.03 <= float(o['ask_price']) <= 0.20]
        if not valid:
            return None
            
        valid.sort(key=lambda x: float(x['volume'] or 0), reverse=True)
        return valid[0]
    except Exception:
        return None

def manage_positions():
    """FULLY AUTOMATED LIMIT AUTO-SELL (PURE TAKE-PROFIT ONLY)"""
    if not ACTIVE_TRADES: return
    
    for ticker, data in list(ACTIVE_TRADES.items()):
        opt = data['option']
        opt_type = data['type'].lower()
        entry_premium = float(data['entry_premium'])
        try:
            # Pull the live price of the specific option contract
            market_data = rh.options.get_option_market_data(ticker, opt['expiration_date'], opt['strike_price'], opt_type)
            if not market_data: continue
            
            # --- BRACKET JSON PARSING FIX ---
            # Extract dictionary from Robinhood's nested list response
            option_info = market_data[0]
            if isinstance(option_info, list):
                option_info = option_info[0]
                
            current_bid = float(option_info.get('bid_price', 0))
            if current_bid == 0: continue 
            
            profit_pct = ((current_bid - entry_premium) / entry_premium) * 100
            
            # --- THE FRICTIONLESS EXECUTION TRIGGER ---
            if profit_pct >= 18.5:
                print(f"\n{C.G}[$$$] AUTO-SELL FIRED: +{profit_pct:.2f}% PROFIT TARGET SECURED ON {ticker}{C.END}")
                rh.orders.order_sell_option_limit("close", "credit", round(current_bid, 2), ticker, 1, opt['expiration_date'], opt['strike_price'], opt_type)
                del ACTIVE_TRADES[ticker]
        except Exception as e:
            print(f"{C.Y}[!] Bracket manager ping failed for {ticker}: {e}{C.END}")
            continue

def hunt_best_deal():
    cands = []
    scores = []
    wallet = get_wallet()
    
    old_stderr = sys.stderr
    sys.stderr = open(os.devnull, 'w')
    try:
        print(f"\r{C.B}[*] SCANNING {len(STOCKS)} TICKERS | BP: ${wallet:.2f}{C.END}   ", end="")
        for t in STOCKS:
            t = t.strip().upper()
            if t in ACTIVE_TRADES: continue
            try:
                h = rh.stocks.get_stock_historicals(t, interval='5minute', span='week', bounds='regular')
                if not h: continue
                px = [float(x['close_price']) for x in h]
                v, a, p = get_kinematics(px)
                
                cands.append({'ticker': t, 'score': a, 'v': v, 'price': px[-1]})
                scores.append(a)
            except Exception:
                continue
    finally:
        sys.stderr = old_stderr
        
    if not cands: return None
    
    mu = np.mean(scores)
    sigma = np.std(scores)
    
    for c in cands:
        c['Z'] = (c['score'] - mu) / sigma if sigma > 0 else 0
        
    cands.sort(key=lambda x: abs(x['Z']), reverse=True)
    
    for c in cands:
        # Prevent engine from hunting if wallet cannot afford minimum $0.03 contract
        if wallet < 3.00: 
            return None

        # --- THE VOLATILITY CLAUSE & MEME DAMPENER ---
        high_iv_assets = ["GME", "AMC", "WTI", "TSLA", "SPCE", "MSTR"]
        
        # Require higher acceleration standard deviation for high-noise stocks
        z_threshold = 2.50 if c['ticker'] in high_iv_assets else 1.84
        
        if abs(c['Z']) > z_threshold:
            opt_type = 'call' if c['v'] > 0 else 'put'
            
            # --- FREIGHT TRAIN OVERRIDE ---
            # Never step in front of high-volatility momentum. Disable Put buying on Meme/Energy stocks.
            if opt_type == 'put' and c['ticker'] in high_iv_assets:
                continue
                
            target_opt = find_cheap_option(c['ticker'], opt_type)
            if target_opt:
                print(f"\n{C.G}{C.BBLD}[♛] KING CROWNED: {c['ticker']} | Z: {c['Z']:.2f} | PX: ${c['price']:.2f}{C.END}")
                return {'ticker': c['ticker'], 'type': opt_type, 'price': c['price'], 'option': target_opt}
    return None

def execute_trade(target):
    opt = target['option']
    print(f"\n{C.G}[+] SECURED CONTRACT: {target['ticker']} {target['type'].upper()} | Strike: ${opt['strike_price']} | Premium: ${opt['ask_price']}{C.END}")
    
    # --- LIVE TRIGGER ARMED ---
    try:
        rh.orders.order_buy_option_limit("open", "debit", opt['ask_price'], target['ticker'], 1, opt['expiration_date'], opt['strike_price'], target['type'])
        print(f"{C.G}[$$$] LIVE ORDER EXECUTED ON ROBINHOOD.{C.END}")
    except Exception as e:
        print(f"{C.R}[!] FAILED TO EXECUTE LIVE ORDER: {e}{C.END}")
        return

    # Store all option data for the Auto-Sell Bracket
    ACTIVE_TRADES[target['ticker']] = {
        "entry_price": target['price'],
        "entry_premium": float(opt['ask_price']),
        "option": opt,
        "type": target['type'],
        "timestamp": datetime.now()
    }
    print(f"{C.CYAN}[+] PURE TAKE-PROFIT BRACKET LOCKED (18.5%).{C.END}")

def sync_to_web(target):
    payload = {
        "ticker": target['ticker'], "type": target['type'], "price": target['price'],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    with open("certified_targets.json", "w") as f:
        json.dump(payload, f, indent=4)
    try:
        subprocess.run(["git", "add", "certified_targets.json"], check=True)
        subprocess.run(["git", "commit", "-m", f"web-sync: {target['ticker']}"], capture_output=True)
        subprocess.run(["git", "push"], capture_output=True)
        print(f"{C.G}[*] WEB SYNC UPDATED: {target['ticker']} IS LIVE.{C.END}")
    except Exception as e:
        print(f"{C.Y}[!] WEB SYNC DELAYED: {e}{C.END}")

if __name__ == "__main__":
    rh_login()
    print(f"{C.BBLD}{C.Y}[!] HEALY VECTOR LABS: PURE TAKE-PROFIT ENGINE ENGAGED{C.END}")
    try:
        while True:
            # THE 3 BULLET RULE ENFORCEMENT
            if len(ACTIVE_TRADES) >= MAX_BULLETS:
                print(f"\r{C.Y}[!] MAX BULLETS SECURED ({MAX_BULLETS}/{MAX_BULLETS}). TACTICAL RELOAD: MONITORING BRACKETS ONLY.{C.END}", end="")
            else:
                target = hunt_best_deal()
                if target:
                    execute_trade(target)
                    sync_to_web(target)
            
            manage_positions()
            time.sleep(2)  # Tightened loop for 0-latency bracket monitoring
            
    except KeyboardInterrupt:
        print(f"\n{C.R}[!!!] EMERGENCY BRAKE PULLED. ENGINE SHUTTING DOWN.{C.END}")
        sys.exit(0)

