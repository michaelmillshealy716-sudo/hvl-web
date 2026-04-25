import numpy as np

# 1. SOVEREIGN PARSER (Extracting from proprietary strings)
parsed_data = []
try:
    with open('verified_springs.log', 'r') as f:
        for line in f:
            try:
                # Slices: [0]Time/Status, [1]Price, [2]PSI, [3]PHI
                parts = line.split('|')
                
                # Extract the raw numbers by splitting at the colon
                psi_str = parts[2].split(':')[1].strip()
                phi_str = parts[3].split(':')[1].strip()
                
                parsed_data.append([float(psi_str), float(phi_str)])
            except Exception:
                continue # If a line is corrupted, skip it silently

    data = np.array(parsed_data)
    print(f">>> INGESTED {len(data)} CLEAN PULSES. INITIALIZING VERITAS V2.2...")
    
    if len(data) == 0:
        print("FATAL ERROR: No valid PSI/PHI data extracted. Check log format.")
        exit()
        
except Exception as e:
    print(f"FATAL ERROR: {e}")
    exit()

# 2. THE CUSTOM SIEVE (Robust Standardization)
mean = np.mean(data, axis=0)
std = np.std(data, axis=0)
std = np.where(std == 0, 1.0, std) # Prevent division by zero
scaled_data = (data - mean) / std

# 3. SOVEREIGN K-MEANS ENGINE
k_regimes = 5
iterations = 20
np.random.seed(716)

print(">>> COMPILING SOVEREIGN K-MEANS MATRIX...")

random_indices = np.random.choice(len(scaled_data), k_regimes, replace=False)
centroids = scaled_data[random_indices]

for _ in range(iterations):
    distances = np.linalg.norm(scaled_data[:, np.newaxis] - centroids, axis=2)
    regimes = np.argmin(distances, axis=1)
    new_centroids = np.array([scaled_data[regimes == i].mean(axis=0) if len(scaled_data[regimes == i]) > 0 else centroids[i] for i in range(k_regimes)])
    if np.all(centroids == new_centroids):
        break
    centroids = new_centroids

# 4. ARCHITECT'S LOG
print("=========================================")
print("HEALY VECTOR LABS: 5-REGIME ALPHA SCAN")
print("=========================================")

for i in range(k_regimes):
    cluster_points = data[regimes == i]
    weight = len(cluster_points)
    
    if weight == 0:
        continue
        
    avg_psi = np.mean(cluster_points[:, 0])
    avg_phi = np.mean(cluster_points[:, 1])
    
    if avg_phi > 4000: 
        status = "MARSHMALLOW (High-Alpha Strike)"
    elif avg_phi > 1000: 
        status = "THE FUSE (Pre-Strike Tension)"
    elif avg_phi > 400: 
        status = "OATS (Structural Resistance)"
    elif avg_phi > 100: 
        status = "BUBBLING MILK (Low Tension Movement)"
    else: 
        status = "FLAT MILK (Background Noise)"
    
    print(f"[REGIME {i}] - {status}")
    print(f" -> Events: {weight} | Velocity (PSI): {avg_psi:.4f} | Tension (PHI): {avg_phi:.2f}")
    print("-" * 40)

