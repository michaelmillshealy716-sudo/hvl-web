import os
import time
import math
import subprocess

# --- HEALY VECTOR LABS: REGIME 2 CENTROIDS (THE FUSE) ---
TARGET_PHI = 2924.28
TARGET_PSI = 29.24
DECAY_THRESHOLD = 0.15  # 15% drop from peak triggers "Cool Down"
peak_phi = 0

def vibrate(duration=100, count=1, pause=0.1):
    """Executes haptic feedback via Termux API"""
    try:
        for _ in range(count):
            subprocess.run(["termux-vibrate", "-d", str(duration)], check=True)
            if count > 1:
                time.sleep(pause)
    except Exception as e:
        print(f"[ERROR] Haptics failed: {e}")

def monitor_stream(live_phi, live_psi):
    global peak_phi
    
    # 1. CALCULATE PROXIMITY (THE MAGNITUDE)
    # Distance = $\sqrt{(\Phi_{live} - \Phi_{target})^2 + (\Psi_{live} - \Psi_{target})^2}$
    ds = math.sqrt((live_phi - TARGET_PHI)**2 + (live_psi - TARGET_PSI)**2)
    
    # 2. TRACK THE LOCAL PEAK
    if live_phi > peak_phi:
        peak_phi = live_phi
    
    # 3. TRAILING STOP: THE COOL DOWN ALERT
    if peak_phi > 500 and live_phi < (peak_phi * (1 - DECAY_THRESHOLD)):
        print(f"[!] DECAY DETECTED: Phi dropped to {live_phi:.2f}")
        vibrate(duration=30, count=3, pause=0.05) # Sharp, rapid decay alert
        peak_phi = live_phi # Reset peak to avoid alert-spamming
        return

    # 4. HAPTIC TIERING (THE SENSORY "FACE-READ")
    if 500 < live_phi < 1500:
        print(f"[AWAKENING] Phi: {live_phi:.2f} | Dist: {ds:.2f}")
        vibrate(duration=50, count=1) # Single short pulse
        
    elif 1500 <= live_phi < 2500:
        print(f"[THE COIL] Phi: {live_phi:.2f} | Dist: {ds:.2f}")
        vibrate(duration=100, count=2) # Double pulse
        
    elif live_phi >= 2500:
        print(f"!!! SINGULARITY !!! Phi: {live_phi:.2f}")
        vibrate(duration=800, count=1) # Long, heavy "Fuse" vibration

# --- THE EXECUTION LOOP (THE IGNITION) ---
print(">>> HEALY VECTOR LABS: PREDATOR MODE ACTIVE")
print(">>> MONITORING BTC/USD VOLATILITY...")

while True:
    # --- LIVE DATA INTEGRATION POINT ---
    # For now, we simulate your current BTC Phi/Psi (51.41 / 6.36)
    # Replace these two lines with your actual telemetry bridge
    current_phi = 51.41 
    current_psi = 6.36
    
    monitor_stream(current_phi, current_psi)
    
    # Refresh every 10 seconds to preserve A16 battery
    time.sleep(10)

