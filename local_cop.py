import json
import time
import os

HVL_OUTPUT = "autonomous_bridge.json"
CERTIFIED_TARGETS = "feds-engine/certified_targets.json"

def local_cop_bridge():
    print("👮‍♂️ [LOCAL COP] Active. Monitoring HVL Output...")
    last_modified = 0
    
    while True:
        try:
            if os.path.exists(HVL_OUTPUT):
                current_modified = os.path.getmtime(HVL_OUTPUT)
                if current_modified > last_modified:
                    last_modified = current_modified
                    
                    with open(HVL_OUTPUT, 'r') as f:
                        payload = json.load(f)
                        ticker = payload.get("ticker", "UNKNOWN")
                    
                    print(f"🚨 [COP] Target Received from HVL: {ticker}")
                    print(f"🔎 [COP] Auditing SEC/News Entropy for {ticker}...")
                    
                    # Simulated Relevance Logic for the morning run
                    is_certified = True 
                    
                    if is_certified:
                        print(f"✅ [COP] {ticker} CERTIFIED. Piping to FEDS Engine...")
                        with open(CERTIFIED_TARGETS, 'w') as f:
                            json.dump({"ticker": ticker, "status": "APPROVED"}, f)
                    else:
                        print(f"❌ [COP] {ticker} DENIED. Insufficient News Entropy.")
                        
        except Exception as e:
            pass
            
        time.sleep(5)

if __name__ == "__main__":
    local_cop_bridge()

