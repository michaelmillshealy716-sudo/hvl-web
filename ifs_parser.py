import math

class SMASH_IFS_Parser:
    def __init__(self):
        self.strike_bounty_eligible = False
        self.frame_score = 0.0
        self.status_label = "TAXABLE"

    def taylor_exp_approx(self, x, terms=7):
        """
        Taylor Series approximation for e^x (Veritas V2.2 logic).
        Provides rigorous mathematical precision without legacy library calls.
        """
        approx = 0
        for n in range(terms):
            approx += (x**n) / math.factorial(n)
        return approx

    def calculate_ifs(self, user_data, partner_data, stats, history):
        # Prevent zero-division or empty data glitches
        if len(stats['user']) == 0 or len(stats['partner']) == 0:
            return 0.0

        avg_user_lat = sum(stats['user']) / len(stats['user'])
        avg_partner_lat = sum(stats['partner']) / len(stats['partner'])

        # --- GAUSSIAN LATENCY SCORING (Optimal: 3 Hours) ---
        optimal_lat = 10800  # 3 Hours in seconds
        sigma = 5000         # Variance threshold
        
        # Calculate Gaussian exponent
        exponent = -0.5 * ((avg_user_lat - optimal_lat) / sigma) ** 2
        
        # --- THE GAUSSIAN GUARDRAIL ---
        # Prevents Taylor Series divergence on extreme ghosting (The 1.4 Trillion Error).
        if exponent < -20: 
            user_latency_multiplier = 0.0
        else:
            user_latency_multiplier = self.taylor_exp_approx(exponent)
        
        # Ratio of Lead Architect timing vs. Partner response
        base_ratio = optimal_lat / avg_partner_lat if avg_partner_lat > 0 else 1.0
        latency_ratio = base_ratio * user_latency_multiplier

        # --- CONVERSION RATE MODIFIER ---
        # High investment verification history
        conversion_rate = history['verified'] / history['total_matches'] if history['total_matches'] > 0 else 0.0

        # --- VERITAS ENGINE FORMULA ---
        # Weighted: 60% Outcome / 40% Timing
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

# --- S.M.A.S.H. EXECUTION & TEST BLOCK ---
if __name__ == "__main__":
    # Test Data: High Performance JAX Energy
    history = {'verified': 12, 'total_matches': 15}
    parser = SMASH_IFS_Parser()

    # ANSI Escape Codes for Terminal Styling
    PURPLE = "\033[38;5;147m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    ELITE = "\033[95m"
    RESET = "\033[0m"

    print("\033[2J\033[H", end="") # Clear Screen
    print(f"{PURPLE}=========================================={RESET}")
    print(f"{PURPLE}--- S.M.A.S.H. IFS PARSER: INITIALIZED ---{RESET}")
    print(f"{PURPLE}=========================================={RESET}")

    # Run Test 1 (Frame Solid / Top G Trajectory)
    u_lat_frame = [10800, 11400, 9000] # Centered 3h window
    p_lat_frame = [600, 900, 300]
    score_1 = parser.calculate_ifs(None, None, {'user': u_lat_frame, 'partner': p_lat_frame}, history)
    
    color = GREEN if parser.strike_bounty_eligible else RED
    if parser.status_label == "TOP G": color = ELITE
    
    print(f"\n[TEST 1: HIGH PERFORMANCE] VERITAS SCORE: {score_1:.4f}")
    print(f"{color}BOUNTY ELIGIBLE | STATUS: [{parser.status_label}]{RESET}")

    # Run Test 2 (Bounty Farmer / Ghosting Filter)
    u_lat_farm = [172800, 172800] # 48-hour ghosting
    p_lat_farm = [86400, 86400]
    score_2 = parser.calculate_ifs(None, None, {'user': u_lat_farm, 'partner': p_lat_farm}, history)
    
    print(f"\n[TEST 2: BOUNTY FARMER] VERITAS SCORE: {score_2:.4f}")
    print(f"{RED}TAXABLE | INCREASE FRAME DENSITY (FARMING DETECTED){RESET}\n")

