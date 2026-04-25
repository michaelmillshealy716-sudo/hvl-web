import time
from smash_master import Veritas_Engine, Shinigo_Intel, Market_Telemetry

class HVL_Mainframe:
    def __init__(self):
        # Initializing the S.M.A.S.H. Subsystems
        self.veritas = Veritas_Engine()
        self.shinigo = Shinigo_Intel()
        self.telemetry = Market_Telemetry()
        self.uptime_cycles = 0

    def daemon_loop(self):
        print("\n" + "="*60)
        print(">>> HEALY VECTOR LABS: MAINFRAME ONLINE <<<")
        print(">>> S.M.A.S.H. SUBSYSTEMS: ENGAGED <<<")
        print("="*60)
        
        try:
            while True:
                # 1. Time & Cycle Tracking
                current_time = time.strftime('%H:%M:%S')
                print(f"\n[SYSTEM PULSE] {current_time} | CYCLE: {self.uptime_cycles}")
                
                # 2. Render the Environment
                self.telemetry.render_dashboard()
                
                # 3. Background Computation Matrix
                score = self.veritas.calculate_ifs(user_lat=8400, partner_lat=340, conversion_rate=0.8)
                strike_status = self.shinigo.calculate_strike_mass(micro_strikes=5, avg_weight=0.25)
                
                # 4. Daemon Output
                print(f"[DAEMON-V] VERITAS SCORE : {score:.4f}")
                print(f"[DAEMON-S] SHINIGO STATUS: {strike_status}")
                print(f"--- DAEMON SLEEPING FOR 60s (Ctrl+C to Terminate) ---")
                
                # Sleep cycle to prevent terminal flooding and API bans
                time.sleep(60)
                self.uptime_cycles += 1
                
        except KeyboardInterrupt:
            print("\n>>> HVL MAINFRAME: MANUAL OVERRIDE INITIATED. DISENGAGING. <<<")

# ==========================================
# --- MAINFRAME IGNITION ---
# ==========================================
if __name__ == "__main__":
    mainframe = HVL_Mainframe()
    mainframe.daemon_loop()

