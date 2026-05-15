import json
import time
import os
import math
from datetime import datetime, timedelta
from nhlpy import NHLClient

# --- HVL Master Aesthetics ---
C_GREEN = '\033[92m'
C_BLUE = '\033[94m'
C_CYAN = '\033[96m'  
C_RED = '\033[91m'
C_WARN = '\033[93m'
C_PURP = '\033[95m'
C_RESET = '\033[0m'
C_BOLD = '\033[1m'

class ScoreEngine:
    def __init__(self, target_team="Buffalo Sabres", target_date="2026-05-16"):
        self.client = NHLClient()
        self.target_team = target_team
        self.target_date = target_date
        self.history_file = "series_history.json"
        
        self.team_data = {
            "away": {"last_delta": 0.0, "last_time": datetime.now(), "name": "MTL"},
            "home": {"last_delta": 0.0, "last_time": datetime.now(), "name": "BUF"}
        }
        
        # Barriers and Road Multipliers
        # Buffalo (Away tomorrow) gets a 'Road Warrior' boost
        self.config = {
            "BUF_Goalie_V": 0.82,
            "MTL_Goalie_V": 0.94,
            "ROAD_BIAS": 1.15, # 15% boost for BUF playoff road dominance
            "SIGMOID_SENSITIVITY": 0.45 # Normalization constant
        }

    def find_active_game(self):
        try:
            schedule = self.client.schedule.daily_schedule(date=self.target_date)
            for game in schedule.get('games', []):
                if self.target_team in [game['homeTeam']['name']['default'], game['awayTeam']['name']['default']]:
                    return game['id']
            return 2025030246 
        except: return 2025030246

    def calculate_entropy(self, mtl_h, buf_h):
        """Calculates system entropy (chaos). High when energies are equal."""
        total = mtl_h + buf_h + 0.1
        p1, p2 = mtl_h/total, buf_h/total
        entropy = - (p1 * math.log(p1 + 0.01) + p2 * math.log(p2 + 0.01))
        return round(entropy, 3)

    def calculate_quantum_metrics(self, side, delta, hits, fo_pct, opponent_v, pressure, is_road):
        """H = [ (p^2 / 2m) + V ] * I * A * Road_Bias"""
        # 1. Possession Wave (A)
        possession_amp = 1.0 + (abs(fo_pct - 50) / 100.0) + (delta * 0.5)
        
        # 2. Mass/Desperation (m)
        mass = 1.0 / (pressure + 0.1)
        kinetic = (delta**2) / (2 * mass) if mass > 0 else 0
        
        # 3. Road Bias
        road_mult = self.config["ROAD_BIAS"] if (is_road and side == "home") else 1.0
        
        # 4. Hamiltonian (Total Energy)
        hamiltonian = (kinetic + opponent_v + (hits * 0.01)) * possession_amp * road_mult
        
        # 5. Normalized Probability (Psi^2)
        # Prevents 99.9% pinning unless game is absolutely wild
        psi_sq = (1 / (1 + math.exp(-(hamiltonian * self.config["SIGMOID_SENSITIVITY"])))) * 100
        strike_chance = min((psi_sq * possession_amp), 99.99)
        
        return {
            "H": round(hamiltonian, 4),
            "psi_sq": round(psi_sq, 2),
            "strike": round(strike_chance, 2),
            "amp": round(possession_amp, 3)
        }

    def get_veritas_payload(self, game_id):
        try:
            game_data = self.client.game_center.boxscore(game_id=game_id)
            away = game_data.get('awayTeam', {})
            home = game_data.get('homeTeam', {})
            
            # BUF is Away for G6, MTL is Home. 
            # We apply 1.50 pressure to BUF (facing elimination)
            mtl_q = self.calculate_quantum_metrics(
                "home", round(home.get('sog', 0)/60, 3), home.get('hits', 0),
                home.get('faceoffWinningPctg', 50.0), self.config["BUF_Goalie_V"], 1.0, False
            )
            
            buf_q = self.calculate_quantum_metrics(
                "away", round(away.get('sog', 0)/60, 3), away.get('hits', 0),
                away.get('faceoffWinningPctg', 50.0), self.config["MTL_Goalie_V"], 1.50, True
            )
            
            entropy = self.calculate_entropy(mtl_q['H'], buf_q['H'])
            
            payload = {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "MTL": mtl_q,
                "BUF": buf_q,
                "entropy": entropy,
                "metadata": {
                    "Hamiltonian": "Total system energy (Kinetic + Potential).",
                    "Psi_Squared": "Probability density of a state-change event (Goal).",
                    "Entropy": "Measure of system chaos vs stability.",
                    "Road_Warrior_Bias": "Multiplier for Buffalo road dominance (4-1 in playoffs)."
                }
            }
            
            self.save_persistence(payload)
            return payload
        except Exception as e:
            print(f"{C_RED}[ ERR ] {e}{C_RESET}")
            return None

    def save_persistence(self, data):
        history = []
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as f:
                try: history = json.load(f)
                except: history = []
        history.append(data)
        with open(self.history_file, 'w') as f:
            json.dump(history[-50:], f, indent=4)

if __name__ == "__main__":
    engine = ScoreEngine()
    try:
        while True:
            os.system('clear')
            print(f"{C_BOLD}+=================================================+")
            print(f"║      HEALY VECTOR LABS: QUANTUM CORE V7.0       ║")
            print(f"║          EXPLICTORY METADATA ENABLED            ║")
            print(f"+=================================================+{C_RESET}\n")
            
            game_id = engine.find_active_game()
            data = engine.get_veritas_payload(game_id)
            if data:
                print(f"System Entropy: {C_CYAN}{data['entropy']} S{C_RESET}\n")
                print(f"{'METRIC':<15} | {'MTL (HOME)':<15} | {'BUF (AWAY)':<15}")
                print("-" * 50)
                print(f"{'Possession A':<15} | {data['MTL']['amp']:<15} | {data['BUF']['amp']:<15}")
                print(f"{'Hamiltonian':<15} | {C_GREEN}{data['MTL']['H']:<15}{C_RESET} | {C_GREEN}{data['BUF']['H']:<15}{C_RESET}")
                print(f"{'Collapse %':<15} | {data['MTL']['psi_sq']:<15} | {data['BUF']['psi_sq']:<15}")
                
                # Strike Readout
                m_color = C_GREEN if data['MTL']['strike'] > 65 else C_WARN
                b_color = C_GREEN if data['BUF']['strike'] > 65 else C_WARN
                print(f"{C_BOLD}{'GOAL STRIKE':<15}{C_RESET} | {m_color}{data['MTL']['strike']:>14}%{C_RESET} | {b_color}{data['BUF']['strike']:>14}%{C_RESET}")
                
                print(f"\n{C_PURP}Explictory Metadata Loaded. Archive Sync: OK.{C_RESET}")
                time.sleep(30)
    except KeyboardInterrupt:
        print(f"\n{C_RED}[ SYSTEM ] ARCHIVE LOCKED.{C_RESET}")

