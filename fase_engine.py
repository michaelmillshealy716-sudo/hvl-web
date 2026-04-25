
import numpy as np
from scipy.ndimage import gaussian_filter1d

def get_quantum_state(price_array, sigma=1.5):
    # Phase Gamma: Gaussian Shield
    smoothed = gaussian_filter1d(price_array, sigma=sigma)

    # Phase Alpha: Higher-Order Derivatives
    v = np.gradient(smoothed)
    a = np.gradient(v)
    jerk = np.gradient(a)
    snap = np.gradient(jerk)
    crackle = np.gradient(snap)
    pop = np.gradient(crackle)

    # Phase Delta: Schrodinger Propagator
    kinetic = 0.5 * (v**2)
    potential = np.abs(jerk)
    hamiltonian = kinetic + potential

    # THE CYBER CRACK FIX: Dynamic Orbital Amplitude
    # Normalizes the violence of the trend to a 0.0 - 1.0 probability density
    h_max = np.max(np.abs(hamiltonian)) + 1e-8
    H_norm = hamiltonian / h_max
    prob_density = np.clip(1.0 - np.exp(-H_norm * 5.0), 0, 1)

    # Standard Delta for HUD
    v_raw = np.diff(price_array)[-1] if len(price_array) > 1 else 0
    a_raw = np.diff(np.diff(price_array))[-1] if len(price_array) > 2 else 0
    delta = (((price_array[-1] + v_raw + 0.5 * a_raw) - price_array[-1]) / price_array[-1]) * 100

    # PROTOCOL SYNC: Return exactly 3 values
    return pop[-1], prob_density[-1], delta

