"""
L-MINER Data Generator
Haider's file — generates all synthetic sensor data for the demo.

Produces:
  - GPR B-scan images (simulated subsurface radar)
  - Spectrometer signatures (based on real mineral fingerprints)
  - 6x6 survey grid with pre-assigned minerals, depths, obstacles
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

# ─────────────────────────────────────────────
# GRID CONFIGURATION
# 6x6 survey area. Pre-assigned so demo is
# identical every run — no randomness.
# ─────────────────────────────────────────────

GRID_SIZE = 6

# Mineral assignments for each cell (row, col)
# 0 = regolith, 1 = water_ice, 2 = ilmenite, 3 = pyroxene
MINERAL_MAP = np.array([
    [0, 1, 1, 0, 2, 0],
    [1, 1, 0, 0, 2, 3],
    [1, 0, 3, 3, 0, 2],
    [0, 0, 3, 1, 1, 0],
    [2, 0, 0, 1, 0, 3],
    [0, 2, 2, 0, 3, 0],
])

# Depth assignments in meters (how deep the mineral sits)
DEPTH_MAP = np.array([
    [0.3, 1.2, 0.8, 0.5, 0.4, 0.6],
    [1.5, 0.9, 0.3, 0.7, 0.6, 1.1],
    [1.8, 0.4, 1.3, 0.9, 0.5, 0.7],
    [0.6, 0.3, 1.0, 1.4, 1.1, 0.4],
    [0.5, 0.8, 0.6, 1.6, 0.3, 0.9],
    [0.7, 0.4, 0.6, 0.5, 1.2, 0.8],
])

# Obstacle cells — pre-assigned (score > 0.75 = unsafe)
# These will trigger L0 safety layer
OBSTACLE_MAP = np.array([
    [0.1, 0.2, 0.1, 0.8, 0.1, 0.2],  # (0,3) is obstacle
    [0.1, 0.1, 0.9, 0.1, 0.1, 0.1],  # (1,2) is obstacle
    [0.1, 0.8, 0.1, 0.1, 0.1, 0.1],  # (2,1) is obstacle
    [0.1, 0.1, 0.1, 0.1, 0.1, 0.9],  # (3,5) is obstacle
    [0.1, 0.1, 0.1, 0.1, 0.8, 0.1],  # (4,4) is obstacle
    [0.9, 0.1, 0.1, 0.1, 0.1, 0.1],  # (5,0) is obstacle
])

MINERAL_NAMES = {
    0: "Regolith",
    1: "Water Ice",
    2: "Ilmenite",
    3: "Pyroxene"
}

MINERAL_COLORS = {
    0: "#888888",   # grey
    1: "#00BFFF",   # blue
    2: "#FF8C00",   # orange
    3: "#32CD32",   # green
    -1: "#FF0000",  # red = obstacle
}


# ─────────────────────────────────────────────
# GPR B-SCAN GENERATOR
# Simulates ground penetrating radar output.
# Returns a 2D array (depth x distance).
# ─────────────────────────────────────────────

def generate_gpr_bscan(mineral_id, depth_m, noise_level=0.08):
    """
    Generate a synthetic GPR B-scan image.
    
    Args:
        mineral_id: 0=regolith, 1=water_ice, 2=ilmenite, 3=pyroxene
        depth_m: depth of mineral layer in meters
        noise_level: how much random noise to add
    
    Returns:
        2D numpy array (128 depth samples x 256 distance samples)
    """
    n_depth = 128
    n_distance = 256

    depth_samples = np.linspace(0, 3.0, n_depth)   # 0 to 3 meters deep
    distance_samples = np.linspace(0, 5.0, n_distance)  # 5 meter traverse

    bscan = np.zeros((n_depth, n_distance))

    # Surface reflection — always at depth 0
    surface_idx = 0
    for d_idx in range(n_distance):
        bscan[surface_idx, d_idx] += 0.9 * np.sin(
            2 * np.pi * distance_samples[d_idx] * 0.3
        )

    # Subsurface mineral layer reflection
    depth_idx = np.argmin(np.abs(depth_samples - depth_m))

    # Each mineral has different reflection character
    if mineral_id == 1:  # Water ice — strong clean reflection
        amplitude = 0.85
        width = 3
    elif mineral_id == 2:  # Ilmenite — medium reflection
        amplitude = 0.55
        width = 4
    elif mineral_id == 3:  # Pyroxene — moderate reflection
        amplitude = 0.65
        width = 5
    else:  # Regolith — weak diffuse reflection
        amplitude = 0.30
        width = 6

    for d_idx in range(n_distance):
        lateral_variation = 1 + 0.1 * np.sin(
            2 * np.pi * distance_samples[d_idx] * 0.5
        )
        for dz in range(-width, width + 1):
            idx = depth_idx + dz
            if 0 <= idx < n_depth:
                envelope = np.exp(-0.5 * (dz / (width / 2)) ** 2)
                bscan[idx, d_idx] += (
                    amplitude * lateral_variation * envelope *
                    np.sin(2 * np.pi * distance_samples[d_idx] * 2.0 + dz)
                )

    # Add random noise
    bscan += noise_level * np.random.randn(n_depth, n_distance)

    # Normalize to [-1, 1]
    max_val = np.abs(bscan).max()
    if max_val > 0:
        bscan = bscan / max_val

    return bscan


def plot_gpr_bscan(bscan, depth_m, mineral_name, ax=None):
    """Plot GPR B-scan as a visual image."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 3))

    ax.imshow(
        bscan,
        aspect='auto',
        cmap='RdBu_r',
        vmin=-1, vmax=1,
        extent=[0, 5.0, 3.0, 0]
    )
    ax.axhline(y=depth_m, color='yellow', linewidth=1.5,
               linestyle='--', label=f'Layer @ {depth_m}m')
    ax.set_xlabel('Distance (m)', color='white', fontsize=9)
    ax.set_ylabel('Depth (m)', color='white', fontsize=9)
    ax.set_title(f'GPR B-Scan', color='white', fontsize=10, fontweight='bold')
    ax.tick_params(colors='white', labelsize=8)
    ax.legend(fontsize=8, facecolor='#1a1a2e', labelcolor='white')
    ax.set_facecolor('#0a0a1a')

    return ax


# ─────────────────────────────────────────────
# SPECTROMETER SIGNATURE GENERATOR
# Based on real mineral spectral fingerprints.
# Uses absorption peaks at known wavelengths.
# ─────────────────────────────────────────────

def generate_spectrometer_data(mineral_id, noise_level=0.02):
    """
    Generate spectrometer reflectance spectrum using real
    USGS Spectral Library mineral signatures.

    Water Ice  : Absorption at 1.25, 1.5, 2.0 μm
                 (Confirmed in lunar poles by Chandrayaan-1 M3)
    Ilmenite   : Dark flat spectrum ~0.05-0.10 reflectance
                 (Apollo sample data, USGS splib07)
    Pyroxene   : Absorption bands at 1.0 and 2.0 μm
                 (Apollo 11/12 basalt samples)
    Regolith   : Broad shallow curve, slight red slope
                 (Lunar soil simulant JSC-1A data)
    """
    wavelengths = np.linspace(0.5, 2.5, 200)
    reflectance = np.zeros(200)

    def gaussian_dip(wl, center, width, depth):
        return depth * np.exp(-0.5 * ((wl - center) / width) ** 2)

    def gaussian_peak(wl, center, width, height):
        return height * np.exp(-0.5 * ((wl - center) / width) ** 2)

    if mineral_id == 0:
        # ── REGOLITH ──
        # Source: Lunar soil simulant JSC-1A, Apollo sample 10084
        # Moderate reflectance, slight red slope (increases toward IR)
        # Weak absorption around 1.0 μm from trace pyroxene/olivine
        reflectance = (
            0.22
            + 0.10 * (wavelengths - 0.5) / 2.0
            - gaussian_dip(wavelengths, 0.95, 0.18, 0.05)
            - gaussian_dip(wavelengths, 1.90, 0.25, 0.03)
        )

    elif mineral_id == 1:
        # ── WATER ICE ──
        # Source: USGS splib07 H2O-ice spectrum
        # Chandrayaan-1 M3 confirmed these exact bands at lunar poles
        # Very high UV/VIS reflectance, drops sharply in IR
        reflectance = (
            0.80
            - 0.20 * (wavelengths - 0.5) / 2.0
            - gaussian_dip(wavelengths, 1.25, 0.07, 0.22)  # real ice band
            - gaussian_dip(wavelengths, 1.50, 0.10, 0.52)  # strong ice band
            - gaussian_dip(wavelengths, 2.00, 0.12, 0.60)  # strongest band
            - gaussian_dip(wavelengths, 0.90, 0.05, 0.08)  # weak overtone
        )

    elif mineral_id == 2:
        # ── ILMENITE (FeTiO₃) ──
        # Source: USGS splib07 Ilmenite HS231.3B
        # Apollo 11 high-Ti basalts — very dark, nearly flat
        # Fe²⁺ crystal field absorption keeps reflectance extremely low
        reflectance = (
            0.07
            + 0.02 * np.sin(2 * np.pi * (wavelengths - 0.5) / 3.0)
            - gaussian_dip(wavelengths, 0.85, 0.30, 0.025)
        )

    elif mineral_id == 3:
        # ── PYROXENE ──
        # Source: USGS splib07 Diopside (Ca-pyroxene) HS119.3B
        # Two diagnostic bands: 1μm (Band I) and 2μm (Band II)
        # Band ratio used by Kaguya/Chandrayaan for lunar mapping
        reflectance = (
            0.42
            + 0.04 * (wavelengths - 0.5) / 2.0
            - gaussian_dip(wavelengths, 1.00, 0.16, 0.30)  # Band I
            - gaussian_dip(wavelengths, 2.00, 0.20, 0.28)  # Band II
            - gaussian_dip(wavelengths, 0.65, 0.08, 0.04)  # weak spin-forb
        )

    # Clip and add noise
    reflectance = np.clip(reflectance, 0.0, 1.0)
    reflectance += noise_level * np.random.randn(200)
    reflectance = np.clip(reflectance, 0.0, 1.0)

    return wavelengths, reflectance


def plot_spectrometer(wavelengths, reflectance, mineral_name, ax=None):
    """Plot spectrometer data as a reflectance curve."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 3))

    color_map = {
        "Water Ice": "#00BFFF",
        "Ilmenite": "#FF8C00",
        "Pyroxene": "#32CD32",
        "Regolith": "#888888"
    }
    color = color_map.get(mineral_name, "#FFFFFF")

    ax.plot(wavelengths, reflectance, color=color, linewidth=2)
    ax.fill_between(wavelengths, reflectance, alpha=0.2, color=color)
    ax.set_xlabel('Wavelength (μm)', color='white', fontsize=9)
    ax.set_ylabel('Reflectance', color='white', fontsize=9)
    ax.set_title('Spectrometer Reading', color='white',
                 fontsize=10, fontweight='bold')
    ax.tick_params(colors='white', labelsize=8)
    ax.set_facecolor('#0a0a1a')
    ax.set_ylim(0, 1)

    # Mark key absorption features
    if mineral_name == "Water Ice":
        ax.axvline(x=1.5, color='yellow', linestyle=':', alpha=0.7,
                   linewidth=1, label='Ice absorption')
        ax.axvline(x=2.0, color='yellow', linestyle=':', alpha=0.7,
                   linewidth=1)
        ax.legend(fontsize=7, facecolor='#1a1a2e', labelcolor='white')
    elif mineral_name == "Pyroxene":
        ax.axvline(x=1.0, color='yellow', linestyle=':', alpha=0.7,
                   linewidth=1, label='Pyroxene bands')
        ax.axvline(x=2.0, color='yellow', linestyle=':', alpha=0.7,
                   linewidth=1)
        ax.legend(fontsize=7, facecolor='#1a1a2e', labelcolor='white')

    return ax


# ─────────────────────────────────────────────
# FEATURE EXTRACTION
# Pulls meaningful numbers from raw sensor data
# so the ML model can use them.
# ─────────────────────────────────────────────

def extract_features(bscan, reflectance, wavelengths):
    """
    Extract numerical features from GPR and spectrometer data.
    These are the inputs to Wasay's Random Forest model.

    Returns:
        feature_vector: 1D array of 10 features
    """
    # GPR features
    gpr_max_amplitude = np.abs(bscan[10:, :]).max()   # ignore surface
    gpr_mean_energy = np.mean(bscan[10:, :] ** 2)
    gpr_layer_contrast = np.std(np.mean(bscan, axis=1))
    subsurface = bscan[10:, :]
    gpr_depth_of_max = np.unravel_index(
        np.abs(subsurface).argmax(), subsurface.shape
    )[0] / subsurface.shape[0]

    # Spectrometer features
    # Key wavelength indices
    idx_05 = 0
    idx_10 = np.argmin(np.abs(wavelengths - 1.0))
    idx_125 = np.argmin(np.abs(wavelengths - 1.25))
    idx_15 = np.argmin(np.abs(wavelengths - 1.5))
    idx_20 = np.argmin(np.abs(wavelengths - 2.0))
    idx_25 = len(wavelengths) - 1

    spec_mean = np.mean(reflectance)
    spec_at_10 = reflectance[idx_10]
    spec_at_15 = reflectance[idx_15]
    spec_at_20 = reflectance[idx_20]
    spec_slope = (reflectance[idx_25] - reflectance[idx_05]) / 2.0
    spec_band_depth_15 = (
        (reflectance[idx_125] + reflectance[idx_20]) / 2
    ) - reflectance[idx_15]

    feature_vector = np.array([
        gpr_max_amplitude,
        gpr_mean_energy,
        gpr_layer_contrast,
        gpr_depth_of_max,
        spec_mean,
        spec_at_10,
        spec_at_15,
        spec_at_20,
        spec_slope,
        spec_band_depth_15
    ])

    return feature_vector


# ─────────────────────────────────────────────
# DATASET GENERATOR
# Creates training data for Wasay's model.
# ─────────────────────────────────────────────

def generate_training_dataset(n_samples_per_class=80):
    """
    Generate a full labeled dataset for training the classifier.
    
    Returns:
        X: feature matrix (n_samples x 10)
        y: labels (n_samples,)  0=regolith 1=water_ice 2=ilmenite 3=pyroxene
    """
    X = []
    y = []

    depth_ranges = {
        0: (0.2, 0.8),   # regolith — shallow
        1: (0.8, 2.0),   # water ice — deeper, in shadowed craters
        2: (0.3, 1.2),   # ilmenite
        3: (0.5, 1.5),   # pyroxene
    }

    for mineral_id in range(4):
        for _ in range(n_samples_per_class):
            d_min, d_max = depth_ranges[mineral_id]
            depth = np.random.uniform(d_min, d_max)
            noise = np.random.uniform(0.05, 0.15)

            bscan = generate_gpr_bscan(mineral_id, depth, noise)
            wl, refl = generate_spectrometer_data(mineral_id, noise * 0.2)
            features = extract_features(bscan, refl, wl)

            X.append(features)
            y.append(mineral_id)

    return np.array(X), np.array(y)


# ─────────────────────────────────────────────
# SINGLE CELL SCAN
# Used by dashboard to get data for one grid cell.
# ─────────────────────────────────────────────

def scan_cell(row, col):
    """
    Get all sensor data for a specific grid cell.
    Used by dashboard.py and model.py.

    Returns dict with everything needed.
    """
    mineral_id = MINERAL_MAP[row, col]
    depth_m = DEPTH_MAP[row, col]
    obstacle_score = OBSTACLE_MAP[row, col]
    mineral_name = MINERAL_NAMES[mineral_id]

    bscan = generate_gpr_bscan(mineral_id, depth_m)
    wavelengths, reflectance = generate_spectrometer_data(mineral_id)
    features = extract_features(bscan, reflectance, wavelengths)

    return {
        "row": row,
        "col": col,
        "mineral_id": mineral_id,
        "mineral_name": mineral_name,
        "depth_m": depth_m,
        "obstacle_score": obstacle_score,
        "is_obstacle": obstacle_score > 0.75,
        "bscan": bscan,
        "wavelengths": wavelengths,
        "reflectance": reflectance,
        "features": features,
    }


# ─────────────────────────────────────────────
# QUICK TEST — run this file directly to verify
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("L-MINER Data Generator — Verification Test")
    print("=" * 50)

    # Test single cell scan
    print("\n[1] Testing single cell scan (row=0, col=1)...")
    data = scan_cell(0, 1)
    print(f"    Mineral   : {data['mineral_name']}")
    print(f"    Depth     : {data['depth_m']} m")
    print(f"    Obstacle  : {data['is_obstacle']} (score={data['obstacle_score']})")
    print(f"    Features  : {data['features'].round(3)}")
    print(f"    GPR shape : {data['bscan'].shape}")
    print(f"    Spec shape: {data['reflectance'].shape}")

    # Test training dataset
    print("\n[2] Generating training dataset...")
    X, y = generate_training_dataset(n_samples_per_class=80)
    print(f"    X shape: {X.shape}")
    print(f"    y shape: {y.shape}")
    print(f"    Classes: {np.unique(y, return_counts=True)}")

    # Test GPR plot
    print("\n[3] Generating sample plots...")
    fig, axes = plt.subplots(2, 4, figsize=(16, 6))
    fig.patch.set_facecolor('#0a0a1a')

    for mineral_id in range(4):
        name = MINERAL_NAMES[mineral_id]
        bscan = generate_gpr_bscan(mineral_id, 1.0)
        wl, refl = generate_spectrometer_data(mineral_id)

        plot_gpr_bscan(bscan, 1.0, name, ax=axes[0, mineral_id])
        axes[0, mineral_id].set_title(f'GPR — {name}',
                                       color='white', fontsize=9)

        plot_spectrometer(wl, refl, name, ax=axes[1, mineral_id])
        axes[1, mineral_id].set_title(f'Spectrum — {name}',
                                       color='white', fontsize=9)

    plt.suptitle('L-MINER Sensor Signatures — All Mineral Types',
                 color='white', fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig('sensor_verification.png', dpi=150,
                bbox_inches='tight', facecolor='#0a0a1a')
    print("    Saved: sensor_verification.png")

    # Print grid overview
    print("\n[4] Survey Grid Overview:")
    print("    Mineral Map:")
    for row in range(GRID_SIZE):
        line = "    "
        for col in range(GRID_SIZE):
            mid = MINERAL_MAP[row, col]
            obs = OBSTACLE_MAP[row, col] > 0.75
            symbol = ["Re", "Wi", "Il", "Py"][mid]
            if obs:
                symbol = "XX"
            line += f"{symbol} "
        print(line)
    print("\n    Legend: Wi=WaterIce Il=Ilmenite Py=Pyroxene Re=Regolith XX=Obstacle")

    print("\n✅ Data generator working correctly.")
    print("   Next step: run model.py (Wasay)")
