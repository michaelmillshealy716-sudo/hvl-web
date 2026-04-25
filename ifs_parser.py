import math

class SMASH_IFS_Parser:
    def __init__(self):
        self.strike_bounty_eligible = False
        self.frame_score = 0.0
        self.status_label = "TAXABLE"

    def calculate_ifs(self, user_data, partner_data, stats, history):
        if len(stats['user']) == 0 or len(stats['partner']) == 0:
            return 0.0 
            
        avg_user_lat = sum(stats['user']) / len(stats['user'])
        avg_partner_lat = sum(stats['partner']) / len(stats['partner'])

        # --- GAUSSIAN LATENCY SCORING ---
        optimal_lat = 10800 # 3 Hours
        sigma = 5000 
        
        user_latency_multiplier = math.exp(-0.5 * ((avg_user_lat - optimal_lat) / sigma) ** 2)
        base_ratio = optimal_lat / avg_partner_lat if avg_partner_lat > 0 else 1.0
        latency_ratio = base_ratio * user_latency_multiplier

        # Conversion Rate Modifier
        conversion_rate = history['verified'] / history['total_matches'] if history['total_matches'] > 0 else 0.0

        # Veritas Engine Formula
        self.frame_score = (0.4 * latency_ratio) + (0.6 * conversion_rate)

        # --- THE HIERARCHY OF FRAME ---
        if self.frame_score > 15.0 and conversion_rate >= 0.95:
            self.status_label = "TOP G"
            self.strike_bounty_eligible = True
        elif self.frame_score > 5.0 and conversion_rate >= 0.8:
            self.status_label = "FRAME SOLID"
            self.strike_bounty_eligible = True
        else:
            self.status_label = "TAXABLE"
            self.strike_bounty_eligible = False

        return self.frame_score

# ==========================================
# --- S.M.A.S.H. EXECUTION & TEST BLOCK ---
# ==========================================

# Test Case 1: FRAME SOLID
user_latencies_frame = [3600, 7200, 14400] 
partner_latencies_high_interest = [300, 600, 120] 

# Test Case 2: BOUNTY FARMER
user_latencies_farmer = [172800, 172800] 
partner_latencies_lost_interest = [86400, 86400] 

history = {'verified': 12, 'total_matches': 15}
parser = SMASH_IFS_Parser()

print('\033[2J\033[H', end='')
print("\033[38;5;147m==========================================\033[0m")
print("\033[38;5;147m--- S.M.A.S.H. IFS PARSER: INITIALIZED ---\033[0m")
print("\033[38;5;147m==========================================\033[0m")

# Run Test 1 (FRAME SOLID)
score_frame = parser.calculate_ifs(None, None, {'user': user_latencies_frame, 'partner': partner_latencies_high_interest}, history)
print(f"\n[TEST 1: HIGH PERFORMANCE] VERITAS SCORE: {score_frame:.4f}")
if parser.strike_bounty_eligible:
    color = "\033[92m" # Green
    if parser.status_label == "TOP G": color = "\033[95m" # Purple/Elite
    print(f"{color}BOUNTY ELIGIBLE | STATUS: {parser.status_label}\033[0m")
else:
    print("\033[91mTAXABLE | INCREASE FRAME DENSITY\033[0m")

# Run Test 2 (Farmer)
score_farm = parser.calculate_ifs(None, None, {'user': user_latencies_farmer, 'partner': partner_latencies_lost_interest}, history)
print(f"\n[TEST 2: BOUNTY FARMER] VERITAS SCORE: {score_farm:.4f}")
if parser.strike_bounty_eligible:
    print(f"\033[92mBOUNTY ELIGIBLE | STATUS: {parser.status_label}\033[0m")
else:
    print("\033[91mTAXABLE | INCREASE FRAME DENSITY (FARMING DETECTED)\033[0m")
print("\n")

