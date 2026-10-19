"""
Generates a 300-DPI Aerospace Concept-of-Operations (ConOps) Hero Image for L-MINER Mk-II.
Perfect for the ISSSP Community Page cover image, Poster graphic, and PPT Title Slide.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Polygon, Circle, Wedge

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']

fig, ax = plt.subplots(figsize=(16, 9), dpi=300)
fig.patch.set_facecolor('#040814')
ax.set_facecolor('#040814')
ax.set_xlim(0, 16)
ax.set_ylim(0, 9)
ax.axis('off')

# ── 1. Starfield & Deep Space Background ─────────────────────────────────────
rng = np.random.default_rng(42)
star_x = rng.uniform(0, 16, 140)
star_y = rng.uniform(4.3, 9.0, 140)
star_s = rng.uniform(2, 18, 140)
ax.scatter(star_x, star_y, s=star_s, color='#E2E8F0', alpha=0.55, edgecolors='none')

# Top Banner Title
ax.text(0.5, 8.45, "L-MINER Mk-II : AUTONOMOUS LUNAR SOUTH POLE PROSPECTING PAYLOAD",
        color='#00E5FF', fontsize=19, fontweight='bold')
ax.text(0.5, 8.05, "ISSSP 2026 Global Finals  |  Track 3: Innovative Design of Lunar Payloads  |  300×200×150 mm  |  6.20 kg  |  26 W Peak",
        color='#94A3B8', fontsize=11.5, fontweight='bold')

# ── 2. Lunar Surface & Subsurface Stratigraphy Cutaway (Y = 0 to 4.3) ────────
x_surf = np.linspace(0, 9.8, 300)
y_surf = 4.15 + 0.12 * np.sin(0.8 * x_surf) - 0.35 * np.exp(-((x_surf - 5.2) / 2.2)**2)

# Layer 3: Deep Fractured Bedrock
ax.fill_between(x_surf, 0.2, 1.6, color='#0F172A', alpha=0.95)
ax.text(0.3, 0.8, "LAYER 3: FRACTURED ANORTHOSITE BEDROCK (> 1.2 m, εr ≈ 8.0)",
        color='#64748B', fontsize=9.5, fontweight='bold')

# Layer 2: Blocky Megaregolith & Ice Trap Zone
ax.fill_between(x_surf, 1.6, 3.1, color='#1E293B', alpha=0.95)
ax.plot(x_surf, np.full_like(x_surf, 1.6), color='#334155', linestyle='--', linewidth=1.2)
ax.text(0.3, 2.75, "LAYER 2: BLOCKY MEGAREGOLITH & COLD-TRAP ZONE (0.4 – 1.2 m, εr ≈ 4.5)",
        color='#94A3B8', fontsize=9.5, fontweight='bold')

# Layer 1: Dry Fine Surface Regolith
ax.fill_between(x_surf, 3.1, y_surf, color='#334155', alpha=0.95)
ax.plot(x_surf, np.full_like(x_surf, 3.1), color='#475569', linestyle=':', linewidth=1.2)
ax.plot(x_surf, y_surf, color='#CBD5E1', linewidth=2.5)
ax.text(0.3, 3.55, "LAYER 1: DRY LUNAR REGOLITH OVERBURDEN (0.0 – 0.4 m, εr = 2.85, T < -200°C PSR)",
        color='#CBD5E1', fontsize=9.5, fontweight='bold')

# ── 3. Buried Subsurface Mineral Ore Bodies ──────────────────────────────────
# Water Ice Lens (Blue)
ice_lens = patches.Ellipse((4.2, 2.25), width=2.3, height=0.65, facecolor='#00E5FF',
                           edgecolor='#E0F7FA', linewidth=2, alpha=0.85)
ax.add_patch(ice_lens)
ax.text(4.2, 2.25, "WATER ICE LENS (H₂O)\nDepth: 0.9m | εr=3.15, tanδ=0.0009",
        color='#020617', fontsize=9, fontweight='bold', ha='center', va='center')

# Ilmenite Ore Body (Amber)
ilm_lens = patches.Ellipse((7.2, 2.05), width=1.6, height=0.55, facecolor='#FF9100',
                           edgecolor='#FFF3E0', linewidth=1.8, alpha=0.85)
ax.add_patch(ilm_lens)
ax.text(7.2, 2.05, "ILMENITE (FeTiO₃)\nεr=6.5, tanδ=0.08",
        color='#020617', fontsize=8.5, fontweight='bold', ha='center', va='center')

# Surface Boulder Obstacle (Red Hazard)
boulder = Polygon([[8.3, 4.05], [8.6, 4.65], [9.1, 4.50], [9.25, 4.08]],
                  closed=True, facecolor='#475569', edgecolor='#FF1744', linewidth=2.2)
ax.add_patch(boulder)
ax.text(8.8, 4.85, "⛔ L0 HAZARD\nBOULDER (>0.75)", color='#FF1744',
        fontsize=8.5, fontweight='bold', ha='center')

# ── 4. Rover & L-MINER Payload Cutaway on Surface ────────────────────────────
rx, ry = 4.2, 4.18
# Wheels
for wx in [rx - 0.9, rx, rx + 0.9]:
    w = Circle((wx, ry), 0.24, facecolor='#0F172A', edgecolor='#94A3B8', linewidth=2, zorder=6)
    ax.add_patch(w)
    ax.add_patch(Circle((wx, ry), 0.08, facecolor='#CBD5E1', zorder=7))

# Gold MLI Payload Box (L-MINER 300x200x150mm)
chassis = FancyBboxPatch((rx - 1.05, ry + 0.22), 2.1, 0.72,
                         boxstyle="round,pad=0.04", facecolor='#D4AF37',
                         edgecolor='#FEF08A', linewidth=2.2, zorder=6)
ax.add_patch(chassis)
ax.text(rx, ry + 0.58, "L-MINER PAYLOAD WEB\nJetson Orin NX + 2.5mm Al Vault\n15mm Aerogel + Gold MLI",
        color='#020617', fontsize=8.5, fontweight='bold', ha='center', va='center', zorder=7)

# Stereo HazCam Mast (L0)
ax.plot([rx + 0.75, rx + 0.75], [ry + 0.94, ry + 1.65], color='#CBD5E1', linewidth=4, zorder=6)
cam_head = FancyBboxPatch((rx + 0.55, ry + 1.65), 0.42, 0.24, boxstyle="round,pad=0.02",
                          facecolor='#1E293B', edgecolor='#00E5FF', linewidth=2, zorder=7)
ax.add_patch(cam_head)
ax.text(rx + 0.76, ry + 2.05, "L0 Stereo HazCam\n+ 850nm VCSEL LiDAR",
        color='#00E676', fontsize=8.5, fontweight='bold', ha='center')

# L0 Camera Green Inspection Cone towards Boulder
fov_poly = Polygon([[rx + 0.95, ry + 1.77], [8.5, 4.65], [8.5, 4.05]],
                   closed=True, facecolor='#00E676', alpha=0.18, edgecolor='#00E676', linestyle='--')
ax.add_patch(fov_poly)

# Forward Active SWIR Spectrometer Arm + Halogen Illumination Cone
ax.plot([rx + 1.05, rx + 1.45, rx + 1.60], [ry + 0.45, ry + 0.35, ry + 0.12],
        color='#CBD5E1', linewidth=3.5, zorder=6)
swir_cone = Polygon([[rx + 1.60, ry + 0.12], [rx + 1.35, ry - 0.18], [rx + 1.85, ry - 0.18]],
                    closed=True, facecolor='#FEF08A', alpha=0.55, edgecolor='#FDE047')
ax.add_patch(swir_cone)
ax.text(rx + 2.15, ry + 0.25, "0.5–2.5 μm SWIR\n+ 3W Active LED Ring\n(Solves Dark PSR)",
        color='#FEF08A', fontsize=8.5, fontweight='bold', ha='left', va='center')

# 500 MHz GPR Radar Wave Cone Penetrating to Water Ice Lens
gpr_cone = Polygon([[rx - 0.4, ry + 0.20], [rx - 1.35, 2.25], [rx + 1.35, 2.25]],
                   closed=True, facecolor='#FFD54F', alpha=0.18, edgecolor='#FFD54F', linestyle=':')
ax.add_patch(gpr_cone)
for r_arc in [0.6, 1.1, 1.6]:
    arc = patches.Arc((rx, ry + 0.2), r_arc*1.6, r_arc*2.1, angle=0, theta1=235, theta2=305,
                      color='#FFD54F', linewidth=2, linestyle='--')
    ax.add_patch(arc)
ax.text(rx - 1.65, 3.25, "500 MHz Dielectric-Loaded\nBow-Tie GPR Sounding Wave",
        color='#FFD54F', fontsize=8.5, fontweight='bold', ha='center')

# ── 5. Right Panel: 3-Tier Hierarchical AI Architecture & Specs (X=10.2 to 15.6)
panel_bg = FancyBboxPatch((10.1, 0.35), 5.6, 7.35, boxstyle="round,pad=0.1",
                          facecolor='#0B1120', edgecolor='#1E293B', linewidth=2)
ax.add_patch(panel_bg)
ax.text(12.9, 7.35, "3-TIER SAFETY-FIRST AI ARCHITECTURE",
        color='#00E5FF', fontsize=13, fontweight='bold', ha='center')
ax.text(12.9, 7.02, "Hardware-Partitioned on Jetson Orin NX + LEON3FT Watchdog",
        color='#94A3B8', fontsize=9.5, ha='center')

tiers = [
    (5.55, '#00E676', "TIER L0 : NAVIGATION & OBSTACLE SAFETY (HIGHEST PRIORITY)",
     "• Sensors: Stereo HazCam (65° FOV) + 850nm Active LiDAR + IMU\n"
     "• Compute: Dedicated NVDLA Core (INT8) + LEON3FT Rad-Hard Fallback\n"
     "• Guarantee: < 50 ms hard preemption — halts science if Hazard ≥ 0.75"),
    (3.75, '#FFD600', "TIER L1 : POWER & PSR THERMAL INTERLOCK",
     "• Monitors: 28V Bus SoC (≥ 20% Reserve) & Avionics Core Temp (≤ 50°C)\n"
     "• PSR Thermal Vault: 15mm Silica Aerogel + 10-Layer MLI + 2.5W Heater\n"
     "• Guarantee: Gates off 26W science burst during low-power / thermal spikes"),
    (1.95, '#00E5FF', "TIER L2 : MULTI-MODAL SCIENCE INFERENCE ENGINE",
     "• Inputs: 500 MHz GPR B-Scan (Depth, Amplitude, Loss-Tangent Slope)\n"
     "           + Active 0.5–2.5 μm SWIR Reflectance (1.0, 1.25, 1.5, 2.0 μm)\n"
     "• Output: Real-time 3D Subsurface Mineral Probability & Depth Map"),
]

for y_box, col, title, body in tiers:
    box = FancyBboxPatch((10.35, y_box), 5.1, 1.35, boxstyle="round,pad=0.06",
                         facecolor='#0F172A', edgecolor=col, linewidth=2)
    ax.add_patch(box)
    ax.text(10.55, y_box + 1.08, title, color=col, fontsize=9.5, fontweight='bold')
    ax.text(10.55, y_box + 0.50, body, color='#E2E8F0', fontsize=8.5, va='center', linespacing=1.45)

# Arrows connecting L0 -> L1 -> L2
ax.annotate("CLEAR", xy=(12.9, 5.15), xytext=(12.9, 5.52),
            arrowprops=dict(arrowstyle="->", color='#00E676', lw=2.5),
            color='#00E676', fontsize=8, fontweight='bold', ha='center')
ax.annotate("AUTHORIZED", xy=(12.9, 3.35), xytext=(12.9, 3.72),
            arrowprops=dict(arrowstyle="->", color='#FFD600', lw=2.5),
            color='#FFD600', fontsize=8, fontweight='bold', ha='center')

# Bottom Key Metrics Strip inside Right Panel
metrics_box = FancyBboxPatch((10.35, 0.55), 5.1, 1.10, boxstyle="round,pad=0.05",
                             facecolor='#1E293B', edgecolor='#38BDF8', linewidth=1.5)
ax.add_patch(metrics_box)
ax.text(12.9, 1.35, "VERIFIED FLIGHT FEASIBILITY BASELINE",
        color='#38BDF8', fontsize=9.5, fontweight='bold', ha='center')
ax.text(12.9, 0.88, "Mass: 6.20 kg  |  Power: 7W (Safe) / 19W (Nom) / 26W (Burst)\n"
                    "Shielding: 2.5mm Al-6061 (90-Day TID = 3.82 krad < 10 krad Limit)",
        color='#F8FAFC', fontsize=8.5, fontweight='bold', ha='center', linespacing=1.4)

plt.tight_layout()
plt.savefig('LMINER_Project_Overview_Hero.png', dpi=300, facecolor='#040814')
print("[OK] Saved high-resolution hero diagram: LMINER_Project_Overview_Hero.png")