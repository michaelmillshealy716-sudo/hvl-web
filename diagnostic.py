import numpy as np

def run_diagnostic(e_values, r_values):
    e_variance = np.var(e_values)
    # Checking if the 'Strike' is stationary or fluctuating
    r_stability = np.mean(r_values) / (np.std(r_values) if np.std(r_values) > 0 else 0.001)
    
    print("\n" + "="*30)
    print("VERITAS ARCHITECT DIAGNOSTIC")
    print("="*30)
    print(f"Current Error (E): {e_values[-1]}")
    print(f"Error Variance:    {e_variance:.6f}")
    print(f"Confidence (R):   {r_values[-1]}")
    print(f"Stability Score:   {r_stability:.2f}")
    print("-" * 30)
    
    if e_variance < 0.05 and r_stability > 10.0:
        return "STATUS: [STRIKE] ALIGNMENT CONFIRMED. PROCEED TO 2ND DERIVATIVE."
    else:
        return "STATUS: [DRIFT] DETECTED. RE-CALIBRATE 1ST ORDER BEFORE ACCELERATING."

# Pre-loaded with your current 'Strike' alignment data
e_log = [1.266] * 10 
r_log = [63.89] * 10

print(run_diagnostic(e_log, r_log))

