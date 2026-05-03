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

