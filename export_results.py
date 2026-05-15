import json
import csv
import os

# --- HVL Export Utility V1.0 ---

def export_hvl_data(input_file="series_history.json"):
    if not os.path.exists(input_file):
        print("\033[91m[ ERROR ] No history file found. Run score_engine.py first.\033[0m")
        return

    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"\033[91m[ ERROR ] Could not read ledger: {e}\033[0m")
        return

    # 1. Export to CSV (The 'Alpha Ledger' for Excel/Quants)
    keys = data[0].keys()
    with open('hvl_alpha_export.csv', 'w', newline='') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)
    
    # 2. Export to Web-Ready JSON (For HealyVectorLabs.com Charts)
    web_data = [
        {
            "time": d['timestamp'], 
            "energy": d['hamiltonian'], 
            "collapse": d['psi_sq'],
            "interference": d['interference']
        } 
        for d in data
    ]
    with open('web_graph_data.json', 'w') as f:
        json.dump(web_data, f, indent=4)

    print(f"\033[92m[ SUCCESS ] {len(data)} packets exported to CSV and Web-JSON.\033[0m")

if __name__ == "__main__":
    export_hvl_data()

