"""
L-MINER Mk-II 3D Interactive Visualization — visualization_3d.py
Photorealistic 3D Digital Twin of the Lunar South Pole Autonomous Survey.

Upgrades & Scientific Corrections for ISSSP 2026 Global Finals:
  - True Heading-Projected Terrain Kinematics: Rover pitch and roll accurately
    project surface gradients onto the rover's forward/lateral axes with corrected right-hand rule.
  - Conformal Topographic Draping: Survey grid lines, dual tire tracks, and PSR volatile frost
    layers drape directly onto the 3D lunar topography instead of floating at fixed Z planes.
  - Active PSR Optical & Radar Physics:
      * Forward Active Broadband LED/Laser Illumination Cone on the Spectrometer Arm (solves PSR darkness)
      * L0 Dynamic Color-Shifting Stereo HazCam + Active LiDAR Frustum (Green / Amber / Crimson)
      * L2 3D Volumetric GPR Fresnel Cone (35° expansion), spherical wavefronts, and dielectric reflector disc
  - Subsurface Geological Stratigraphy Cutaway:
      * Layered boundary planes for Fine Regolith (0 to -0.4m), Megaregolith (-0.4 to -1.2m), and Bedrock (<-1.2m)
      * 3D Scattered Lunar Ejecta Boulders around hazardous crater rims
  - Compute Spec Alignment: Updated HUD telemetry to reflect NVIDIA Jetson Orin NX (Dual NVDLA + GPU).
"""

import numpy as np
import plotly.graph_objects as go
from data_generator import (
    MINERAL_MAP,
    OBSTACLE_MAP,
    DEPTH_MAP,
    MINERAL_NAMES,
    MINERAL_COLORS,
    GRID_SIZE,
)

# ── Color Palette & Physical Constants ───────────────────────────────────────

MINERAL_3D_COLORS = {
    'Wi': '#00E5FF',   # Water Ice - Luminous Cyan
    'Il': '#FF9100',   # Ilmenite - Titanium Amber
    'Py': '#00E676',   # Pyroxene - Emerald Silicate
    'Re': '#94A3B8',   # Regolith - Lunar Silver-Grey
    'OB': '#FF1744',   # Obstacle - Hazard Crimson
    'LP': '#FFD600',   # Low Power - Golden Warning
}

MINERAL_LABELS = {
    'Wi': 'Water Ice (H₂O Volatiles, εr≈3.15)',
    'Il': 'Ilmenite (FeTiO₃ Ore, εr≈6.5)',
    'Py': 'Pyroxene ((Mg,Fe)SiO₃, εr≈4.8)',
    'Re': 'Lunar Regolith Substrate (εr≈2.8)',
    'OB': 'Hazardous Obstacle / Slope',
    'LP': 'Power-Save Skipped',
}

BATTERY_CAPACITY = 100.0
LOW_POWER_THRESHOLD = 20.0
MAX_TEMP_C = 50.0
NOMINAL_TEMP_C = 28.0


# ── 3D Geometric Primitive Helpers ───────────────────────────────────────────

def _rotation_matrix(yaw_deg=0.0, pitch_deg=0.0, roll_deg=0.0):
    """
    3D Euler rotation matrix (Yaw -> Pitch -> Roll).
    Note: Positive pitch_deg tilts nose UP (+Z) when climbing positive slope.
    """
    y = np.radians(yaw_deg)
    p = np.radians(-pitch_deg)  # Negated so +slope pitches +X nose upward (+Z)
    r = np.radians(roll_deg)

    Rz = np.array([
        [np.cos(y), -np.sin(y), 0.0],
        [np.sin(y),  np.cos(y), 0.0],
        [0.0,        0.0,       1.0]
    ])
    Ry = np.array([
        [ np.cos(p), 0.0, np.sin(p)],
        [ 0.0,       1.0, 0.0      ],
        [-np.sin(p), 0.0, np.cos(p)]
    ])
    Rx = np.array([
        [1.0, 0.0,        0.0       ],
        [0.0, np.cos(r), -np.sin(r)],
        [0.0, np.sin(r),  np.cos(r)]
    ])
    return Rz @ Ry @ Rx


def _make_box_mesh(center, size, R=None, color='#D4AF37', opacity=1.0,
                   specular=0.45, roughness=0.40, name='box', hover_txt=None):
    """Solid 3D oriented bounding box mesh with PBR-like lighting."""
    cx, cy, cz = center
    sx, sy, sz = size
    dx, dy, dz = sx / 2.0, sy / 2.0, sz / 2.0

    local_verts = np.array([
        [-dx, -dy, -dz],
        [ dx, -dy, -dz],
        [ dx,  dy, -dz],
        [-dx,  dy, -dz],
        [-dx, -dy,  dz],
        [ dx, -dy,  dz],
        [ dx,  dy,  dz],
        [-dx,  dy,  dz]
    ])

    if R is not None:
        verts = (R @ local_verts.T).T + np.array([cx, cy, cz])
    else:
        verts = local_verts + np.array([cx, cy, cz])

    i = [0, 0, 4, 4, 0, 0, 1, 1, 2, 2, 3, 3]
    j = [1, 2, 5, 6, 4, 5, 5, 6, 6, 7, 7, 4]
    k = [2, 3, 6, 7, 1, 1, 2, 2, 3, 3, 0, 0]

    return go.Mesh3d(
        x=verts[:, 0].tolist(), y=verts[:, 1].tolist(), z=verts[:, 2].tolist(),
        i=i, j=j, k=k,
        color=color, opacity=opacity, name=name,
        flatshading=True,
        lighting=dict(ambient=0.42, diffuse=0.88, specular=specular, roughness=roughness, fresnel=0.25),
        showlegend=False,
        hoverinfo='skip' if hover_txt is None else 'all',
        hovertemplate=hover_txt
    )


def _make_cylinder_mesh(p1, p2, radius, n_sides=14, color='#1E293B', opacity=1.0,
                        name='cylinder', hover_txt=None):
    """Solid 3D cylinder mesh constructed between 3D endpoints p1 and p2."""
    p1 = np.array(p1, dtype=float)
    p2 = np.array(p2, dtype=float)
    v = p2 - p1
    mag = np.linalg.norm(v)
    if mag < 1e-6:
        return None
    v_norm = v / mag

    arbitrary = np.array([0.0, 0.0, 1.0]) if abs(v_norm[2]) < 0.9 else np.array([0.0, 1.0, 0.0])
    u1 = np.cross(v_norm, arbitrary)
    u1 /= np.linalg.norm(u1)
    u2 = np.cross(v_norm, u1)

    theta = np.linspace(0, 2 * np.pi, n_sides, endpoint=False)
    circle = np.outer(np.cos(theta), u1) + np.outer(np.sin(theta), u2)

    verts_bottom = p1 + radius * circle
    verts_top = p2 + radius * circle
    verts = np.vstack([verts_bottom, verts_top, p1, p2])

    center_bottom_idx = 2 * n_sides
    center_top_idx = 2 * n_sides + 1

    i, j, k = [], [], []
    for s in range(n_sides):
        nxt = (s + 1) % n_sides
        b1, b2 = s, nxt
        t1, t2 = s + n_sides, nxt + n_sides

        i.extend([b1, t1])
        j.extend([b2, t2])
        k.extend([t1, b2])

        i.append(center_bottom_idx)
        j.append(nxt)
        k.append(s)

        i.append(center_top_idx)
        j.append(t1)
        k.append(t2)

    return go.Mesh3d(
        x=verts[:, 0].tolist(),
        y=verts[:, 1].tolist(),
        z=verts[:, 2].tolist(),
        i=i, j=j, k=k,
        color=color, opacity=opacity, name=name,
        lighting=dict(ambient=0.42, diffuse=0.85, specular=0.40, roughness=0.45),
        showlegend=False,
        hoverinfo='skip' if hover_txt is None else 'all',
        hovertemplate=hover_txt
    )


def _make_cone_frustum_mesh(p_apex, p_base, r_apex, r_base, n_sides=16,
                            color='#00E5FF', opacity=0.25, name='cone', hover_txt=None):
    """3D translucent truncated cone mesh for optical / radar beams."""
    p1 = np.array(p_apex, dtype=float)
    p2 = np.array(p_base, dtype=float)
    v = p2 - p1
    mag = np.linalg.norm(v)
    if mag < 1e-6:
        return None
    v_norm = v / mag

    arbitrary = np.array([0.0, 0.0, 1.0]) if abs(v_norm[2]) < 0.9 else np.array([0.0, 1.0, 0.0])
    u1 = np.cross(v_norm, arbitrary)
    u1 /= np.linalg.norm(u1)
    u2 = np.cross(v_norm, u1)

    theta = np.linspace(0, 2 * np.pi, n_sides, endpoint=False)
    circle = np.outer(np.cos(theta), u1) + np.outer(np.sin(theta), u2)

    verts_top = p1 + r_apex * circle
    verts_bot = p2 + r_base * circle
    verts = np.vstack([verts_top, verts_bot])

    i, j, k = [], [], []
    for s in range(n_sides):
        nxt = (s + 1) % n_sides
        t1, t2 = s, nxt
        b1, b2 = s + n_sides, nxt + n_sides
        i.extend([t1, t2])
        j.extend([b1, b1])
        k.extend([t2, b2])

    return go.Mesh3d(
        x=verts[:, 0].tolist(), y=verts[:, 1].tolist(), z=verts[:, 2].tolist(),
        i=i, j=j, k=k,
        color=color, opacity=opacity, name=name,
        lighting=dict(ambient=0.65, diffuse=0.80, specular=0.30, roughness=0.50),
        showlegend=False,
        hoverinfo='skip' if hover_txt is None else 'all',
        hovertemplate=hover_txt
    )


def _make_ellipsoid_mesh(center, rx, ry, rz, n_lat=12, n_lon=16, color='#00E5FF',
                         opacity=0.88, name='deposit', hover_txt=None):
    """Solid 3D ellipsoid mesh for mineral bodies and angular boulders."""
    cx, cy, cz = center
    u = np.linspace(0, 2 * np.pi, n_lon)
    v = np.linspace(0, np.pi, n_lat)

    x = (cx + rx * np.outer(np.cos(u), np.sin(v))).flatten()
    y = (cy + ry * np.outer(np.sin(u), np.sin(v))).flatten()
    z = (cz + rz * np.outer(np.ones_like(u), np.cos(v))).flatten()

    i, j, k = [], [], []
    for lat in range(n_lat - 1):
        for lon in range(n_lon - 1):
            p1 = lat * n_lon + lon
            p2 = p1 + 1
            p3 = (lat + 1) * n_lon + lon
            p4 = p3 + 1

            i.extend([p1, p2])
            j.extend([p3, p3])
            k.extend([p2, p4])

    return go.Mesh3d(
        x=x.tolist(), y=y.tolist(), z=z.tolist(),
        i=i, j=j, k=k,
        color=color, opacity=opacity, name=name,
        lighting=dict(ambient=0.50, diffuse=0.90, specular=0.55, roughness=0.28),
        showlegend=False,
        hoverinfo='skip' if hover_txt is None else 'all',
        hovertemplate=hover_txt
    )


# ── High-Fidelity Lunar Polar Terrain & Boulders ─────────────────────────────

def _generate_lunar_terrain(grid_res=100, seed=42):
    """
    Generate high-resolution lunar South Pole terrain (Shackleton Rim analog):
      - Multi-scale impact craters with flat floors, raised structural rims, and ejecta decay
      - Regional polar slope toward Permanently Shadowed cold traps
      - Multi-octave fractal regolith micro-roughness
    """
    rng = np.random.default_rng(seed)
    x = np.linspace(0, GRID_SIZE, grid_res)
    y = np.linspace(0, GRID_SIZE, grid_res)
    X, Y = np.meshgrid(x, y)

    # Regional highland topography + gentle southward tilt
    Z = (
        0.15 * np.sin(0.68 * X + 0.3) * np.cos(0.58 * Y)
        + 0.08 * np.sin(1.45 * X + 0.6) * np.cos(1.25 * Y + 0.7)
        + 0.03 * np.cos(2.80 * X - 0.4) * np.sin(2.60 * Y + 0.2)
        + 0.032 * (Y - 3.0)
    )

    # Lunar crater catalogue (cx, cy, radius, depth)
    craters = [
        (1.5, 1.2, 0.95, 0.38),   # North-West Ice Basin (PSR-A)
        (3.8, 3.8, 0.85, 0.32),   # South-East Ice Depression (PSR-B)
        (3.5, 0.5, 0.55, 0.25),   # Obstacle crater near (0,3)
        (2.5, 1.5, 0.52, 0.23),   # Obstacle crater near (1,2)
        (1.5, 2.5, 0.54, 0.23),   # Obstacle crater near (2,1)
        (5.5, 3.5, 0.50, 0.26),   # Obstacle crater near (3,5)
        (4.5, 4.5, 0.48, 0.24),   # Obstacle crater near (4,4)
        (0.5, 5.5, 0.56, 0.27),   # Obstacle crater near (5,0)
        (5.1, 1.1, 0.40, 0.16),   # Secondary impact crater
        (2.8, 5.2, 0.36, 0.14),   # Secondary impact crater
        (0.8, 3.8, 0.32, 0.12),   # Micro-crater
    ]

    for cx, cy, radius, depth in craters:
        d = np.sqrt((X - cx)**2 + (Y - cy)**2)
        # Parabolic cavity + raised structural rim + continuous ejecta blanket
        Z -= depth * np.exp(-0.5 * (d / (radius * 0.60))**2.2)
        Z += depth * 0.42 * np.exp(-0.5 * ((d - radius * 0.92) / (radius * 0.20))**2)

    # Multi-scale fractal regolith roughness
    Z += 0.012 * rng.standard_normal((grid_res, grid_res))

    return X, Y, Z * 0.62


def _interp_z(x_val, y_val, Z):
    """Bilinear interpolation of terrain height Z at arbitrary continuous (x, y)."""
    grid_res = Z.shape[0]
    fx = np.clip(x_val / GRID_SIZE * (grid_res - 1), 0, grid_res - 1.001)
    fy = np.clip(y_val / GRID_SIZE * (grid_res - 1), 0, grid_res - 1.001)
    x0, y0 = int(fx), int(fy)
    dx, dy = fx - x0, fy - y0
    z00 = Z[y0, x0]
    z10 = Z[y0, x0 + 1]
    z01 = Z[y0 + 1, x0]
    z11 = Z[y0 + 1, x0 + 1]
    return float(z00 * (1 - dx) * (1 - dy) + z10 * dx * (1 - dy) + z01 * (1 - dx) * dy + z11 * dx * dy)


def _surface_elevation_and_attitude(row, col, heading_deg, Z):
    """
    Compute terrain elevation and heading-projected pitch and roll angles
    at cell center so all 6 rover wheels conform to local surface slope.
    """
    grid_res = Z.shape[0]
    cx, cy = col + 0.5, row + 0.5
    z_elev = _interp_z(cx, cy, Z)

    step = GRID_SIZE / grid_res
    dz_dx = (_interp_z(cx + step, cy, Z) - _interp_z(cx - step, cy, Z)) / (2.0 * step)
    dz_dy = (_interp_z(cx, cy + step, Z) - _interp_z(cx, cy - step, Z)) / (2.0 * step)

    # Project world gradient onto rover forward and lateral unit vectors
    h_rad = np.radians(heading_deg)
    fwd_slope = dz_dx * np.cos(h_rad) + dz_dy * np.sin(h_rad)
    lat_slope = -dz_dx * np.sin(h_rad) + dz_dy * np.cos(h_rad)

    pitch_deg = float(np.degrees(np.arctan(fwd_slope)))
    roll_deg = float(np.degrees(np.arctan(lat_slope)))

    return z_elev, pitch_deg, roll_deg


# ── Scattered Lunar Ejecta Boulders ──────────────────────────────────────────

def _lunar_boulder_traces(Z_raw, seed=108):
    """Render realistic 3D angular lunar boulders around obstacle zones."""
    rng = np.random.default_rng(seed)
    traces = []

    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if OBSTACLE_MAP[r, c] > 0.75:
                cx, cy = c + 0.5, r + 0.5
                # Place 3 angular boulders per hazardous cell
                for b_idx in range(3):
                    bx = cx + rng.uniform(-0.26, 0.26)
                    by = cy + rng.uniform(-0.26, 0.26)
                    bz = _interp_z(bx, by, Z_raw)
                    rx = rng.uniform(0.06, 0.11)
                    ry = rng.uniform(0.05, 0.09)
                    rz = rng.uniform(0.04, 0.08)

                    boulder = _make_ellipsoid_mesh(
                        center=[bx, by, bz + rz * 0.55],
                        rx=rx, ry=ry, rz=rz,
                        n_lat=5, n_lon=6,  # Low-poly faceted rock appearance
                        color='#475569' if b_idx % 2 == 0 else '#64748B',
                        opacity=1.0,
                        name='Lunar Ejecta Boulder',
                        hover_txt=f'<b>Anorthositic Ejecta Boulder</b><br>Cell ({r}, {c}) Hazard<extra></extra>'
                    )
                    if boulder:
                        traces.append(boulder)
    return traces


# ── Subsurface Geological Stratigraphy Cutaway Walls ─────────────────────────

def _stratigraphy_cutaway_traces():
    """
    Render subsurface geological stratigraphy reference horizons:
      - Layer 1 (0.0m to -0.4m): Fine Regolith Overburden (εr ≈ 2.8)
      - Layer 2 (-0.4m to -1.2m): Blocky Megaregolith & Ice Lenses (εr ≈ 5.5)
      - Layer 3 (-1.2m to -2.2m): Fractured Anorthositic Bedrock (εr ≈ 8.0)
    """
    traces = []
    horizons = [
        (-0.40, 'rgba(148, 163, 184, 0.22)', 'Regolith / Megaregolith Boundary (-0.4m, εr≈2.8→5.5)'),
        (-1.20, 'rgba(56, 189, 248, 0.18)',  'Megaregolith / Fractured Bedrock Boundary (-1.2m, εr≈5.5→8.0)'),
    ]

    for z_depth, col_rgba, label in horizons:
        # Perimeter boundary frame showing geological horizon
        px = [0, GRID_SIZE, GRID_SIZE, 0, 0]
        py = [0, 0, GRID_SIZE, GRID_SIZE, 0]
        pz = [z_depth] * 5
        traces.append(go.Scatter3d(
            x=px, y=py, z=pz,
            mode='lines',
            line=dict(color=col_rgba, width=2, dash='dot'),
            showlegend=False,
            hovertemplate=f'<b>Stratigraphic Horizon</b><br>{label}<extra></extra>'
        ))

    return traces


# ── Photorealistic Solid 3D Rover Model ──────────────────────────────────────

def _solid_rover_traces(rx, ry, rz, heading_deg=0.0, pitch_deg=0.0, roll_deg=0.0,
                        battery_pct=100.0, temperature=NOMINAL_TEMP_C,
                        l0_ok=True, l1_ok=True):
    """
    Construct a high-detail solid 3D digital twin of the L-MINER Mk-II rover:
      - Gold-foil Multi-Layer Insulation (MLI) chassis + thermal radiator louvers
      - Triple-junction GaAs solar panel array deck with silver busbar grid lines
      - 6 solid 3D cylindrical wheels with titanium hubs & rocker-bogie linkages
      - Sensor mast with Stereo HazCam lenses + Active LiDAR illuminator
      - Forward articulated NIR Spectrometer Arm with Active Broadband LED Light Cone
      - Rear 500 MHz bow-tie GPR antenna module
      - High-gain X-band parabolic dish antenna
      - L1 3D Battery Telemetry Cylinder & Mast Thermal Beacon
    """
    traces = []
    R = _rotation_matrix(yaw_deg=heading_deg, pitch_deg=pitch_deg, roll_deg=roll_deg)

    def to_world(local_p):
        return (R @ np.array(local_p)) + np.array([rx, ry, rz])

    # 1. Main Warm Electronics Box (WEB) Chassis (Gold MLI Thermal Blanket)
    chassis_mesh = _make_box_mesh(
        center=to_world([0.0, 0.0, 0.16]),
        size=[0.52, 0.36, 0.16],
        R=R,
        color='#D4AF37',
        specular=0.75,
        roughness=0.25,
        name='Rover Chassis (Gold MLI Foil)',
        hover_txt=(
            '<b>L-MINER Mk-II Warm Electronics Box (WEB)</b><br>'
            'Compute: NVIDIA Jetson Orin NX (16GB, Dual NVDLA)<br>'
            'Fallback: Rad-Hard LEON3FT / FPGA Safety Interlock<br>'
            'Thermal: Multi-Layer Insulation + Heat Pipe Loop<extra></extra>'
        )
    )
    if chassis_mesh:
        traces.append(chassis_mesh)

    # 2. Top Triple-Junction GaAs Solar Panel Deck
    solar_deck_mesh = _make_box_mesh(
        center=to_world([0.0, 0.0, 0.246]),
        size=[0.48, 0.32, 0.015],
        R=R,
        color='#0F172A',
        specular=0.80,
        roughness=0.20,
        name='GaAs Solar Array Deck',
        hover_txt='<b>Solar Array & Power Deck</b><br>Triple-Junction GaAs Cells<extra></extra>'
    )
    if solar_deck_mesh:
        traces.append(solar_deck_mesh)

    # Silver busbar cell grid lines on solar deck
    for x_line in [-0.24, -0.08, 0.08, 0.24]:
        p_a = to_world([x_line, -0.16, 0.256])
        p_b = to_world([x_line,  0.16, 0.256])
        traces.append(go.Scatter3d(
            x=[p_a[0], p_b[0]], y=[p_a[1], p_b[1]], z=[p_a[2], p_b[2]],
            mode='lines', line=dict(color='#38BDF8', width=1.5),
            showlegend=False, hoverinfo='skip'
        ))
    for y_line in [-0.16, 0.0, 0.16]:
        p_a = to_world([-0.24, y_line, 0.256])
        p_b = to_world([ 0.24, y_line, 0.256])
        traces.append(go.Scatter3d(
            x=[p_a[0], p_b[0]], y=[p_a[1], p_b[1]], z=[p_a[2], p_b[2]],
            mode='lines', line=dict(color='#FFD54F', width=2),
            showlegend=False, hoverinfo='skip'
        ))

    # 3. 6 Solid Cylindrical Wheels with Rocker-Bogie Titanium Linkages
    wheel_mounts = [
        (-0.21, -0.25, 0.04, -1),
        ( 0.00, -0.27, 0.04, -1),
        ( 0.21, -0.25, 0.04, -1),
        (-0.21,  0.25, 0.04,  1),
        ( 0.00,  0.27, 0.04,  1),
        ( 0.21,  0.25, 0.04,  1),
    ]
    wheel_rad = 0.068
    wheel_w = 0.058

    for side in [-1, 1]:
        # Main rocker-bogie pivot junction on chassis side
        rocker_pivot = to_world([0.02, side * 0.19, 0.15])
        bogie_pivot = to_world([-0.11, side * 0.22, 0.10])

        # Link front wheel to main rocker pivot
        front_axle = to_world([0.21, side * 0.22, 0.04])
        s1 = _make_cylinder_mesh(rocker_pivot, front_axle, radius=0.012, n_sides=8, color='#94A3B8')
        if s1:
            traces.append(s1)

        # Link main rocker pivot to rear bogie pivot
        s2 = _make_cylinder_mesh(rocker_pivot, bogie_pivot, radius=0.013, n_sides=8, color='#94A3B8')
        if s2:
            traces.append(s2)

        # Link rear bogie pivot to middle and rear wheels
        mid_axle = to_world([0.00, side * 0.24, 0.04])
        rear_axle = to_world([-0.21, side * 0.22, 0.04])
        s3 = _make_cylinder_mesh(bogie_pivot, mid_axle, radius=0.011, n_sides=8, color='#64748B')
        s4 = _make_cylinder_mesh(bogie_pivot, rear_axle, radius=0.011, n_sides=8, color='#64748B')
        if s3:
            traces.append(s3)
        if s4:
            traces.append(s4)

    for wx, wy, wz, side in wheel_mounts:
        p_inner = to_world([wx, wy - side * (wheel_w / 2.0), wz])
        p_outer = to_world([wx, wy + side * (wheel_w / 2.0), wz])

        w_mesh = _make_cylinder_mesh(
            p_inner, p_outer, radius=wheel_rad, n_sides=16,
            color='#1E293B', name='Rover Wheel',
            hover_txt='<b>Rocker-Bogie Wheel</b><br>Titanium Mesh & Chevron Grousers<extra></extra>'
        )
        if w_mesh:
            traces.append(w_mesh)

        # Titanium outer rim hub
        hub_center = to_world([wx, wy + side * (wheel_w / 2.0 + 0.003), wz])
        traces.append(go.Scatter3d(
            x=[hub_center[0]], y=[hub_center[1]], z=[hub_center[2]],
            mode='markers',
            marker=dict(size=5, color='#E2E8F0', line=dict(color='#0F172A', width=1.5)),
            showlegend=False, hoverinfo='skip'
        ))

    # 4. Remote Sensing Mast & Stereo HazCam + Active LiDAR Head
    mast_base = to_world([0.18, 0.0, 0.25])
    mast_top = to_world([0.18, 0.0, 0.58])
    mast_mesh = _make_cylinder_mesh(mast_base, mast_top, radius=0.018, n_sides=10, color='#CBD5E1')
    if mast_mesh:
        traces.append(mast_mesh)

    # HazCam optical camera head box
    cam_box = _make_box_mesh(
        center=to_world([0.19, 0.0, 0.58]),
        size=[0.06, 0.16, 0.05],
        R=R, color='#1E293B', name='HazCam Housing',
        hover_txt='<b>L0 Stereo HazCam & Active LED Floodlight</b><br>10 Hz Obstacle & Slope Detection<extra></extra>'
    )
    if cam_box:
        traces.append(cam_box)

    # Dual stereo sapphire lenses + central active LiDAR/LED illuminator
    for y_off, col_lens in [(-0.055, '#00E5FF'), (0.0, '#FFFBEB'), (0.055, '#00E5FF')]:
        c_start = to_world([0.21, y_off, 0.58])
        c_end = to_world([0.245, y_off, 0.58])
        lens_mesh = _make_cylinder_mesh(c_start, c_end, radius=0.013, n_sides=10, color=col_lens)
        if lens_mesh:
            traces.append(lens_mesh)

    # 5. L1 Thermal Indicator Beacon on Mast Peak
    t_frac = np.clip((temperature - NOMINAL_TEMP_C) / (MAX_TEMP_C - NOMINAL_TEMP_C), 0.0, 1.0)
    therm_r = int(255 * t_frac)
    therm_g = int(225 * (1.0 - t_frac))
    therm_b = int(255 * (1.0 - t_frac * 0.85))
    therm_color = f'rgb({therm_r},{therm_g},{therm_b})'
    therm_pos = to_world([0.18, 0.0, 0.64])

    traces.append(go.Scatter3d(
        x=[therm_pos[0]], y=[therm_pos[1]], z=[therm_pos[2]],
        mode='markers',
        marker=dict(
            size=7.5 + 4.0 * t_frac,
            color=therm_color,
            symbol='circle',
            line=dict(color='white', width=1.5)
        ),
        showlegend=False,
        hovertemplate=(
            f'<b>L1 Thermal Management Loop</b><br>'
            f'WEB Avionics Temp: <b>{temperature:.1f}°C</b><br>'
            f'Throttle Ceiling: {MAX_TEMP_C:.0f}°C<extra></extra>'
        )
    ))

    # 6. High-Gain Parabolic Dish Antenna
    dish_base = to_world([-0.18, 0.09, 0.25])
    dish_center = to_world([-0.20, 0.11, 0.40])
    dish_mount = _make_cylinder_mesh(dish_base, dish_center, radius=0.011, color='#94A3B8')
    if dish_mount:
        traces.append(dish_mount)

    dish_r = 0.085
    theta_d = np.linspace(0, 2 * np.pi, 20)
    dish_rim = np.array([dish_center + R @ np.array([
        dish_r * np.cos(t) * 0.4 - 0.03,
        dish_r * np.sin(t),
        dish_r * np.cos(t) * 0.9
    ]) for t in theta_d])
    traces.append(go.Scatter3d(
        x=dish_rim[:, 0], y=dish_rim[:, 1], z=dish_rim[:, 2],
        mode='lines',
        line=dict(color='#FFD54F', width=3.5),
        showlegend=False,
        hovertemplate='<b>X-Band High-Gain Dish</b><br>Polar Relay / Direct-to-Earth Link<extra></extra>'
    ))

    # 7. Rear 500 MHz Ground Penetrating Radar (GPR) Bow-Tie Array
    gpr_box = _make_box_mesh(
        center=to_world([-0.27, 0.0, 0.07]),
        size=[0.06, 0.34, 0.035],
        R=R, color='#FFD54F', name='GPR Transceiver Array',
        hover_txt=(
            '<b>L2 500 MHz UHF GPR Bow-Tie Array</b><br>'
            'Measures Dielectric Contrast & Loss Tangent Slope<br>'
            'Penetration Depth: 0.2 – 3.0 m<extra></extra>'
        )
    )
    if gpr_box:
        traces.append(gpr_box)

    # 8. Forward Articulated NIR Spectrometer Arm + Active Halogen/LED Illuminator
    arm_shoulder = to_world([0.25, -0.07, 0.15])
    arm_elbow = to_world([0.33, -0.07, 0.12])
    arm_head = to_world([0.36, -0.07, 0.055])
    arm_ground = to_world([0.38, -0.07, 0.00])

    s_arm1 = _make_cylinder_mesh(arm_shoulder, arm_elbow, radius=0.012, color='#CBD5E1')
    s_arm2 = _make_cylinder_mesh(arm_elbow, arm_head, radius=0.010, color='#94A3B8')
    if s_arm1:
        traces.append(s_arm1)
    if s_arm2:
        traces.append(s_arm2)

    # Active Broadband Illumination Cone (crucial for operating inside dark PSRs!)
    illum_cone = _make_cone_frustum_mesh(
        arm_head, arm_ground, r_apex=0.012, r_base=0.075, n_sides=14,
        color='#FEF08A', opacity=0.45, name='Active NIR Illumination',
        hover_txt=(
            '<b>Active Broadband Halogen/LED Illuminator</b><br>'
            '0.5–2.5 μm Active Optical Source for Dark PSRs<br>'
            'Enables Surface Frost & Regolith Spectroscopy<extra></extra>'
        )
    )
    if illum_cone:
        traces.append(illum_cone)

    # 9. L1 3D Battery Telemetry Pillar (Floating beside Rover)
    bx_pos = to_world([-0.02, -0.40, 0.02])
    bx_top = to_world([-0.02, -0.40, 0.56])
    batt_frac = np.clip(battery_pct / BATTERY_CAPACITY, 0.0, 1.0)
    batt_color = '#00E676' if battery_pct > 50 else ('#FFD600' if battery_pct > LOW_POWER_THRESHOLD else '#FF1744')

    batt_frame = _make_cylinder_mesh(
        bx_pos, bx_top, radius=0.024, n_sides=12,
        color='#334155', opacity=0.32, name='Battery HUD'
    )
    if batt_frame:
        traces.append(batt_frame)

    bx_fill_top = bx_pos + (bx_top - bx_pos) * batt_frac
    if batt_frac > 0.02:
        batt_fill = _make_cylinder_mesh(
            bx_pos, bx_fill_top, radius=0.020, n_sides=12,
            color=batt_color, opacity=0.95, name='Battery Reserve',
            hover_txt=f'<b>L1 Payload Power Allocation</b><br>SoC: <b>{battery_pct:.1f}%</b><br>Reserve Interlock: {LOW_POWER_THRESHOLD}%<extra></extra>'
        )
        if batt_fill:
            traces.append(batt_fill)

    traces.append(go.Scatter3d(
        x=[bx_top[0]], y=[bx_top[1]], z=[bx_top[2] + 0.06],
        mode='text',
        text=[f'⚡{battery_pct:.0f}%'],
        textfont=dict(size=9, color=batt_color, family='monospace'),
        showlegend=False, hoverinfo='skip'
    ))

    # 10. Rover Safety Interlock Aura Halo
    halo_theta = np.linspace(0, 2 * np.pi, 40)
    halo_r = 0.45
    halo_color = '#00E676' if (l0_ok and l1_ok) else ('#FFD600' if (l0_ok and not l1_ok) else '#FF1744')

    local_halo = np.vstack([
        halo_r * np.cos(halo_theta),
        halo_r * np.sin(halo_theta),
        np.full_like(halo_theta, 0.012)
    ])
    world_halo = (R @ local_halo).T + np.array([rx, ry, rz])

    traces.append(go.Scatter3d(
        x=world_halo[:, 0], y=world_halo[:, 1], z=world_halo[:, 2],
        mode='lines',
        line=dict(color=halo_color, width=3.5),
        showlegend=False,
        hovertemplate=(
            f'<b>Payload Autonomy Interlock</b><br>'
            f'L0 Hazard Check: {"✅ CLEAR" if l0_ok else "⛔ OBSTACLE HALT"}<br>'
            f'L1 Power/Thermal: {"✅ NOMINAL" if l1_ok else "⚡ STANDBY HOLD"}<extra></extra>'
        )
    ))

    return traces


# ── L0 HazCam Optical Field-of-View Cone (Dynamic State Color) ──────────────

def _l0_camera_frustum_traces(rx, ry, rz, heading_deg, Z_raw, l0_ok=True, obs_score=0.0):
    """
    Render 3D stereo HazCam + Active LiDAR inspection frustum projecting ahead.
    Dynamically shifts color: Emerald (Clear) -> Amber (Caution) -> Crimson (Blocked).
    """
    traces = []
    h = np.radians(heading_deg)
    fov_deg = 62.0
    reach = 1.15
    half_fov = np.radians(fov_deg / 2.0)
    angles = np.linspace(h - half_fov, h + half_fov, 11)

    if not l0_ok or (obs_score is not None and obs_score >= 0.75):
        ray_col = 'rgba(255, 23, 68, 0.38)'
        arc_col = 'rgba(255, 23, 68, 0.90)'
        status_lbl = '⛔ HAZARD DETECTED — HALT'
    elif obs_score is not None and obs_score >= 0.45:
        ray_col = 'rgba(255, 214, 0, 0.30)'
        arc_col = 'rgba(255, 214, 0, 0.85)'
        status_lbl = '⚠️ MODERATE SLOPE CAUTION'
    else:
        ray_col = 'rgba(0, 230, 118, 0.24)'
        arc_col = 'rgba(0, 230, 118, 0.80)'
        status_lbl = '✅ TERRAIN CLEAR (DLA < 50ms)'

    cam_origin = np.array([rx + 0.21 * np.cos(h), ry + 0.21 * np.sin(h), rz + 0.58])

    arc_x, arc_y, arc_z = [], [], []
    for ang in angles:
        ex = np.clip(rx + reach * np.cos(ang), 0.05, GRID_SIZE - 0.05)
        ey = np.clip(ry + reach * np.sin(ang), 0.05, GRID_SIZE - 0.05)
        ez = _interp_z(ex, ey, Z_raw) + 0.025
        arc_x.append(ex)
        arc_y.append(ey)
        arc_z.append(ez)

        traces.append(go.Scatter3d(
            x=[cam_origin[0], ex], y=[cam_origin[1], ey], z=[cam_origin[2], ez],
            mode='lines',
            line=dict(color=ray_col, width=1.8),
            showlegend=False, hoverinfo='skip'
        ))

    traces.append(go.Scatter3d(
        x=arc_x, y=arc_y, z=arc_z,
        mode='lines',
        line=dict(color=arc_col, width=3.0),
        showlegend=False,
        hovertemplate=f'<b>L0 Stereo HazCam + Active LiDAR Frustum</b><br>Status: {status_lbl}<extra></extra>'
    ))

    return traces


# ── Holographic Obstacle Hazard Beacons ─────────────────────────────────────

def _obstacle_hazard_traces(row, col, Z_raw):
    """Render holographic hazard exclusion beacons at verified obstacles (OBSTACLE_MAP > 0.75)."""
    cx, cy = col + 0.5, row + 0.5
    sz = _interp_z(cx, cy, Z_raw)
    score = float(OBSTACLE_MAP[row, col])
    traces = []

    column_mesh = _make_cylinder_mesh(
        [cx, cy, sz], [cx, cy, sz + 0.72], radius=0.032, n_sides=10,
        color='#FF1744', opacity=0.78, name='Hazard Pillar',
        hover_txt=(
            f'<b>⛔ L0 HAZARD EXCLUSION ZONE</b><br>'
            f'Grid Cell: ({row}, {col})<br>'
            f'Hazard Score: <b>{score:.2f}</b> (Threshold: 0.75)<br>'
            f'Action: Science Arm & GPR Gated Off<extra></extra>'
        )
    )
    if column_mesh:
        traces.append(column_mesh)

    traces.append(go.Scatter3d(
        x=[cx], y=[cy], z=[sz + 0.80],
        mode='markers+text',
        marker=dict(size=10, color='#FF1744', symbol='diamond', line=dict(color='white', width=1.5)),
        text=['⛔'],
        textfont=dict(size=11),
        showlegend=False,
        hovertemplate=f'<b>L0 EXCLUSION ZONE</b><br>Coordinates: ({row}, {col})<br>Hazard Score: {score:.2f}<extra></extra>'
    ))

    # Conformal ground hazard perimeter ring
    theta = np.linspace(0, 2 * np.pi, 28)
    hr = 0.42
    rx_ring = cx + hr * np.cos(theta)
    ry_ring = cy + hr * np.sin(theta)
    rz_ring = [_interp_z(x, y, Z_raw) + 0.02 for x, y in zip(rx_ring, ry_ring)]

    traces.append(go.Scatter3d(
        x=rx_ring, y=ry_ring, z=rz_ring,
        mode='lines',
        line=dict(color='rgba(255, 23, 68, 0.85)', width=2.5),
        showlegend=False, hoverinfo='skip'
    ))

    return traces


# ── L2 Subsurface GPR Fresnel Radar Cone & Wavefronts ───────────────────────

def _gpr_wavefront_traces(rx, ry, rz, target_depth_m=1.0):
    """
    Render physically grounded 500 MHz GPR radar wave propagation:
      - 3D translucent conical Fresnel radar beam (35° expansion in regolith)
      - Concentric spherical downward-propagating electromagnetic wave crests
      - Dielectric reflection interface disc at target mineral horizon
    """
    traces = []
    target_z = -target_depth_m
    apex_z = rz + 0.05
    max_r = 0.38

    # 1. Volumetric 3D GPR Fresnel Cone
    gpr_cone = _make_cone_frustum_mesh(
        [rx, ry, apex_z], [rx, ry, target_z],
        r_apex=0.04, r_base=max_r, n_sides=20,
        color='#FFD54F', opacity=0.20, name='GPR Radar Cone',
        hover_txt=(
            f'<b>L2 500 MHz GPR Fresnel Cone</b><br>'
            f'Target Dielectric Horizon: <b>{target_depth_m:.2f} m</b><br>'
            f'Extracts Peak Amplitude & Loss Tangent Attenuation<extra></extra>'
        )
    )
    if gpr_cone:
        traces.append(gpr_cone)

    # 2. Central Radar Axis Pulse
    traces.append(go.Scatter3d(
        x=[rx, rx], y=[ry, ry], z=[apex_z, target_z],
        mode='lines',
        line=dict(color='#FFD54F', width=3.5, dash='dash'),
        showlegend=False, hoverinfo='skip'
    ))

    # 3. Concentric Propagating Wavefront Rings
    theta = np.linspace(0, 2 * np.pi, 28)
    for frac in [0.25, 0.50, 0.75, 1.0]:
        z_slice = apex_z - frac * (apex_z - target_z)
        r_slice = 0.04 + (max_r - 0.04) * frac
        traces.append(go.Scatter3d(
            x=rx + r_slice * np.cos(theta),
            y=ry + r_slice * np.sin(theta),
            z=np.full_like(theta, z_slice),
            mode='lines',
            line=dict(color=f'rgba(255, 213, 79, {0.80 - 0.35 * frac})', width=2.2),
            showlegend=False, hoverinfo='skip'
        ))

    # 4. Dielectric Reflection Horizon Disc at Target Depth
    reflect_disc = _make_cylinder_mesh(
        [rx, ry, target_z - 0.015], [rx, ry, target_z + 0.015],
        radius=max_r * 1.05, n_sides=20,
        color='#FFD600', opacity=0.45, name='Dielectric Reflector',
        hover_txt=f'<b>Dielectric Reflection Boundary</b><br>Depth: {target_depth_m:.2f} m<extra></extra>'
    )
    if reflect_disc:
        traces.append(reflect_disc)

    return traces


# ── Volumetric Subsurface Geological Deposits ───────────────────────────────

def _volumetric_deposit_traces(scanned, Z_raw):
    """
    Render volumetric mineral deposits as 3D ellipsoidal ore lenses at exact depth:
      - 3D deposit ellipsoid body (volume scaled by ML confidence)
      - Translucent vertical borehole sounding column from true surface Z to deposit
      - Conformal surface detection reticle
    """
    traces = []

    for (row, col), info in scanned.items():
        status = info.get('status', 'scanned')
        cx, cy = col + 0.5, row + 0.5
        sz = _interp_z(cx, cy, Z_raw)

        if status == 'obstacle':
            continue

        if status == 'low_power':
            # Render L1 Low-Power Standby marker on surface
            theta = np.linspace(0, 2 * np.pi, 24)
            traces.append(go.Scatter3d(
                x=cx + 0.26 * np.cos(theta),
                y=cy + 0.26 * np.sin(theta),
                z=[_interp_z(cx + 0.26 * np.cos(t), cy + 0.26 * np.sin(t), Z_raw) + 0.02 for t in theta],
                mode='lines',
                line=dict(color='#FFD600', width=2.5, dash='dash'),
                showlegend=False,
                hovertemplate=f'<b>⚡ L1 Low-Power Hold</b><br>Cell ({row}, {col}) Skipped for Recharge<extra></extra>'
            ))
            continue

        mineral_code = info.get('mineral', 'Re')[:2]
        depth = info.get('depth_m', float(DEPTH_MAP[row, col]))
        conf = info.get('confidence', 0.85)
        cz = -depth

        color = MINERAL_3D_COLORS.get(mineral_code, MINERAL_3D_COLORS['Re'])
        label = MINERAL_LABELS.get(mineral_code, 'Mineral Deposit')

        rx = 0.16 + 0.12 * conf
        ry = 0.16 + 0.12 * conf
        rz = 0.08 + 0.06 * conf

        deposit_mesh = _make_ellipsoid_mesh(
            center=[cx, cy, cz], rx=rx, ry=ry, rz=rz,
            color=color, opacity=0.90, name=label,
            hover_txt=(
                f'<b>{label}</b><br>'
                f'Survey Cell: ({row}, {col})<br>'
                f'Subsurface Depth: <b>{depth:.2f} m</b><br>'
                f'L2 Classifier Confidence: <b>{conf * 100:.1f}%</b><extra></extra>'
            )
        )
        if deposit_mesh:
            traces.append(deposit_mesh)

        # Vertical sounding core cylinder from exact surface elevation down to deposit
        core_mesh = _make_cylinder_mesh(
            [cx, cy, sz], [cx, cy, cz], radius=0.016, n_sides=8,
            color=color, opacity=0.38, name='Sounding Core'
        )
        if core_mesh:
            traces.append(core_mesh)

        # Conformal surface detection reticle
        theta = np.linspace(0, 2 * np.pi, 22)
        rx_ret = cx + 0.22 * np.cos(theta)
        ry_ret = cy + 0.22 * np.sin(theta)
        rz_ret = [_interp_z(x, y, Z_raw) + 0.018 for x, y in zip(rx_ret, ry_ret)]

        traces.append(go.Scatter3d(
            x=rx_ret, y=ry_ret, z=rz_ret,
            mode='lines',
            line=dict(color=color, width=1.8),
            showlegend=False, hoverinfo='skip'
        ))

    return traces


# ── Permanently Shadowed Regions (PSR) Conformal Cold Traps ─────────────────

def _psr_cold_traps(Z_raw):
    """
    Render Permanently Shadowed Regions (PSR-A and PSR-B) conformed to the
    lowest crater floor topography where T < 40 K (-233°C) traps water ice.
    """
    surfaces = []

    # PSR-A (North-West Ice Basin around crater (1.5, 1.2))
    px1 = np.linspace(0.55, 2.45, 26)
    py1 = np.linspace(0.35, 2.05, 26)
    PX1, PY1 = np.meshgrid(px1, py1)
    PZ1 = np.zeros_like(PX1)
    for i in range(PX1.shape[0]):
        for j in range(PX1.shape[1]):
            dist = np.hypot(PX1[i, j] - 1.5, PY1[i, j] - 1.2)
            if dist <= 0.88:
                PZ1[i, j] = _interp_z(PX1[i, j], PY1[i, j], Z_raw) + 0.008
            else:
                PZ1[i, j] = np.nan

    surfaces.append(go.Surface(
        x=PX1, y=PY1, z=PZ1,
        colorscale=[[0, 'rgba(2, 12, 45, 0.55)'], [1, 'rgba(0, 229, 255, 0.40)']],
        showscale=False, opacity=0.50,
        name='Permanently Shadowed Region (PSR-A)',
        hovertemplate='<b>PSR-A Cold Trap Floor</b><br>Temp < 40 K (-233°C)<br>Surface Frost & Buried Ice Lens<extra></extra>'
    ))

    # PSR-B (South-East Ice Depression around crater (3.8, 3.8))
    px2 = np.linspace(2.95, 4.65, 24)
    py2 = np.linspace(2.95, 4.65, 24)
    PX2, PY2 = np.meshgrid(px2, py2)
    PZ2 = np.zeros_like(PX2)
    for i in range(PX2.shape[0]):
        for j in range(PX2.shape[1]):
            dist = np.hypot(PX2[i, j] - 3.8, PY2[i, j] - 3.8)
            if dist <= 0.78:
                PZ2[i, j] = _interp_z(PX2[i, j], PY2[i, j], Z_raw) + 0.008
            else:
                PZ2[i, j] = np.nan

    surfaces.append(go.Surface(
        x=PX2, y=PY2, z=PZ2,
        colorscale=[[0, 'rgba(2, 12, 45, 0.50)'], [1, 'rgba(0, 200, 255, 0.38)']],
        showscale=False, opacity=0.45,
        name='Permanently Shadowed Region (PSR-B)',
        hovertemplate='<b>PSR-B Cold Trap Basin</b><br>Temp < 45 K (-228°C)<br>High Volatile Retention<extra></extra>'
    ))

    return surfaces


# ── Conformal Survey Grid, Dual Tire Tracks & Target Reticle ────────────────

def _grid_and_trail_traces(scanned, current_row, current_col, scan_index, scan_order, Z_raw):
    """Conformal topographic grid lines, dual rover wheel tracks, and next target reticle."""
    traces = []
    n_pts = 40
    u_vals = np.linspace(0, GRID_SIZE, n_pts)

    # 1. Topographically Draped Survey Grid Lines
    for i in range(GRID_SIZE + 1):
        v = float(i)
        # East-West line at y = v
        z_ew = [_interp_z(x, v, Z_raw) + 0.008 for x in u_vals]
        traces.append(go.Scatter3d(
            x=u_vals, y=[v] * n_pts, z=z_ew,
            mode='lines',
            line=dict(color='rgba(56, 189, 248, 0.22)', width=1.5),
            showlegend=False, hoverinfo='skip'
        ))
        # North-South line at x = v
        z_ns = [_interp_z(v, y, Z_raw) + 0.008 for y in u_vals]
        traces.append(go.Scatter3d(
            x=[v] * n_pts, y=u_vals, z=z_ns,
            mode='lines',
            line=dict(color='rgba(56, 189, 248, 0.22)', width=1.5),
            showlegend=False, hoverinfo='skip'
        ))

    # 2. Dual Rover Wheel Tracks & Center Traversal Trail
    if scanned:
        cells = list(scanned.keys())
        waypoints = [(c + 0.5, r + 0.5) for r, c in cells] + [(current_col + 0.5, current_row + 0.5)]

        wx = [p[0] for p in waypoints]
        wy = [p[1] for p in waypoints]
        wz = [_interp_z(x, y, Z_raw) + 0.022 for x, y in waypoints]

        # Center telemetry breadcrumb path
        traces.append(go.Scatter3d(
            x=wx, y=wy, z=wz,
            mode='lines+markers',
            line=dict(color='rgba(0, 230, 118, 0.65)', width=3.0, dash='dot'),
            marker=dict(size=3.5, color='#00E676'),
            showlegend=False,
            hovertemplate='Autonomous Rover Traverse Path<extra></extra>'
        ))

        # Parallel wheel track imprints in regolith
        for seg_idx in range(len(waypoints) - 1):
            p1 = np.array(waypoints[seg_idx])
            p2 = np.array(waypoints[seg_idx + 1])
            dv = p2 - p1
            dist = np.linalg.norm(dv)
            if dist > 1e-4:
                perp = np.array([-dv[1], dv[0]]) / dist * 0.24
                for side in [-1.0, 1.0]:
                    t_pts = np.linspace(0, 1, 8)
                    tx = [p1[0] + t * dv[0] + side * perp[0] for t in t_pts]
                    ty = [p1[1] + t * dv[1] + side * perp[1] for t in t_pts]
                    tz = [_interp_z(x, y, Z_raw) + 0.010 for x, y in zip(tx, ty)]
                    traces.append(go.Scatter3d(
                        x=tx, y=ty, z=tz,
                        mode='lines',
                        line=dict(color='rgba(148, 163, 184, 0.40)', width=2.0),
                        showlegend=False, hoverinfo='skip'
                    ))

    # 3. Next Target Reticle
    if scan_order and scan_index < len(scan_order):
        nr, nc = scan_order[scan_index]
        cx, cy = nc + 0.5, nr + 0.5
        theta = np.linspace(0, 2 * np.pi, 28)
        rx_t = cx + 0.42 * np.cos(theta)
        ry_t = cy + 0.42 * np.sin(theta)
        rz_t = [_interp_z(x, y, Z_raw) + 0.025 for x, y in zip(rx_t, ry_t)]

        traces.append(go.Scatter3d(
            x=rx_t, y=ry_t, z=rz_t,
            mode='lines',
            line=dict(color='#FFD600', width=2.8),
            showlegend=False,
            hovertemplate=f'<b>Next Autonomous Waypoint</b><br>Grid Cell: ({nr}, {nc})<extra></extra>'
        ))

    return traces


# ── Legend Dummy Traces ──────────────────────────────────────────────────────

def _legend_traces():
    items = [
        ('Water Ice (H₂O Lens)',       '#00E5FF'),
        ('Ilmenite (FeTiO₃ Ore)',      '#FF9100'),
        ('Pyroxene (Silicate)',        '#00E676'),
        ('Dry Lunar Regolith',         '#94A3B8'),
        ('⛔ L0 Hazard / Boulder',      '#FF1744'),
        ('⚡ L1 Low-Power Hold',        '#FFD600'),
        ('🔬 L2 500MHz GPR Cone',      '#FFD54F'),
        ('💡 Active PSR Illuminator',  '#FEF08A'),
    ]
    traces = []
    for name, color in items:
        traces.append(go.Scatter3d(
            x=[None], y=[None], z=[None],
            mode='markers',
            marker=dict(size=8.5, color=color),
            name=name, showlegend=True
        ))
    return traces


# ── Decision HUD Annotation ──────────────────────────────────────────────────

def _decision_hud_annotation(l0_ok, l1_ok, l2_active, battery_pct, temperature, obs_score=None):
    """Aerospace-grade HUD overlay annotation with Orin NX DLA telemetry."""
    l0_txt = '✅ L0 SAFETY (DLA): CLEAR' if l0_ok else '⛔ L0 SAFETY (DLA): HALT'
    if obs_score is not None:
        l0_txt += f' [H={obs_score:.2f}]'

    l1_txt = '✅ L1 POWER/THERM: NOMINAL' if l1_ok else f'⚡ L1 INTERLOCK: RECHARGE ({battery_pct:.0f}%)'
    l2_txt = '🔬 L2 GPR+NIR ML: SOUNDING' if l2_active else '💤 L2 GPR+NIR ML: GATED / IDLE'

    lines = [
        '<b style="color:#00E5FF;letter-spacing:1px">L-MINER Mk-II AUTONOMY HUD (ORIN NX)</b>',
        f'<span style="color:{"#00E676" if l0_ok else "#FF1744"}">{l0_txt}</span>',
        f'<span style="color:{"#00E676" if l1_ok else "#FFD600"}">{l1_txt}</span>',
        f'<span style="color:{"#00E5FF" if l2_active else "#94A3B8"}">{l2_txt}</span>',
        f'<span style="color:#7DD3FC">WEB TEMP: {temperature:.1f}°C  |  BUS SOC: {battery_pct:.0f}%</span>',
    ]

    return dict(
        text='<br>'.join(lines),
        align='left',
        showarrow=False,
        xref='paper', yref='paper',
        x=0.01, y=0.98,
        bordercolor='rgba(0, 229, 255, 0.45)',
        borderwidth=1,
        borderpad=8,
        bgcolor='rgba(3, 7, 18, 0.92)',
        font=dict(size=10, color='white', family='monospace'),
    )


# ── Master 3D Builder ────────────────────────────────────────────────────────

def build_3d_figure(
    scan_log=None,
    system_state=None,
    show_gpr_beam=False,
    current_row=0,
    current_col=0,
    scan_index=0,
    scan_order=None,
    last_l0=None,
    last_l1=None,
    **legacy_kwargs,
):
    """
    Build master photorealistic 3D digital twin of the Lunar South Pole mission.
    100% drop-in compatible with dashboard.py.
    """
    if 'row' in legacy_kwargs and 'current_row' not in legacy_kwargs:
        current_row = legacy_kwargs.pop('row')
    if 'col' in legacy_kwargs and 'current_col' not in legacy_kwargs:
        current_col = legacy_kwargs.pop('col')
    if 'system_state' in legacy_kwargs and system_state is None:
        system_state = legacy_kwargs.pop('system_state')

    if scan_log is None:
        scan_log = []
    if scan_order is None:
        scan_order = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE)]

    scanned = {(d['row'], d['col']): d for d in scan_log}

    battery_pct = system_state.battery if system_state else BATTERY_CAPACITY
    temperature = system_state.temperature if system_state else NOMINAL_TEMP_C

    l0_ok = last_l0['safe'] if last_l0 else True
    l1_ok = last_l1['can_scan'] if last_l1 else True
    l2_active = show_gpr_beam
    obs_score = last_l0.get('obstacle_score') if last_l0 else float(OBSTACLE_MAP[current_row, current_col])

    # Calculate dynamic heading toward next waypoint
    heading_deg = 0.0
    if scan_order and scan_index < len(scan_order):
        next_r, next_c = scan_order[scan_index]
        dr = next_r - current_row
        dc = next_c - current_col
        if dr != 0 or dc != 0:
            heading_deg = float(np.degrees(np.arctan2(dr, dc)))
    elif len(scan_log) >= 2:
        prev = scan_log[-2]
        heading_deg = float(np.degrees(np.arctan2(current_row - prev['row'], current_col - prev['col'])))

    # 1. High-Resolution Lunar Polar Terrain
    X, Y, Z_raw = _generate_lunar_terrain(grid_res=100, seed=42)

    terrain = go.Surface(
        x=X, y=Y, z=Z_raw,
        colorscale=[
            [0.00, '#02040A'],  # Deep PSR crater floor (< 40 K)
            [0.16, '#0A1124'],  # Shadowed crater walls
            [0.35, '#182030'],  # Basaltic mare floor
            [0.55, '#2D3748'],  # Highland anorthositic regolith
            [0.75, '#4A5568'],  # Grazing solar-illuminated slope
            [0.90, '#718096'],  # Fresh ejecta blanket
            [1.00, '#CBD5E1'],  # Sunlit crater rim crest (1.5° grazing sun)
        ],
        showscale=False,
        lighting=dict(
            ambient=0.30,
            diffuse=0.90,
            roughness=0.70,
            specular=0.32,
            fresnel=0.25
        ),
        lightposition=dict(x=15.0, y=-6.0, z=1.8),  # 1.8° Low Polar Grazing Sun
        name='Lunar South Pole Topography',
        hovertemplate='Surface Coordinates: (%{x:.2f} m, %{y:.2f} m)<br>Elevation: %{z:.2f} m<extra></extra>',
    )

    # 2. Conformal Permanently Shadowed Regions (PSRs)
    psr_surfaces = _psr_cold_traps(Z_raw)

    # 3. Subsurface Geological Stratigraphy Cutaway Horizons
    strat_traces = _stratigraphy_cutaway_traces()

    # 4. Scattered 3D Lunar Ejecta Boulders
    boulder_traces = _lunar_boulder_traces(Z_raw)

    # 5. Conformal Grid Lines, Dual Wheel Tracks & Target Reticle
    nav_traces = _grid_and_trail_traces(scanned, current_row, current_col, scan_index, scan_order, Z_raw)

    # 6. Obstacle Hazard Holographic Beacons
    obstacle_traces = []
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if OBSTACLE_MAP[r, c] > 0.75:
                obstacle_traces.extend(_obstacle_hazard_traces(r, c, Z_raw))

    # 7. Volumetric Subsurface Geological Deposits
    deposit_traces = _volumetric_deposit_traces(scanned, Z_raw)

    # 8. Solid 3D Rover Digital Twin with True Heading-Projected Attitude
    rz, pitch_deg, roll_deg = _surface_elevation_and_attitude(current_row, current_col, heading_deg, Z_raw)
    rover_traces = _solid_rover_traces(
        rx=current_col + 0.5,
        ry=current_row + 0.5,
        rz=rz + 0.015,
        heading_deg=heading_deg,
        pitch_deg=pitch_deg,
        roll_deg=roll_deg,
        battery_pct=battery_pct,
        temperature=temperature,
        l0_ok=l0_ok,
        l1_ok=l1_ok,
    )

    # 9. L0 HazCam Optical + Active LiDAR Frustum
    fov_traces = _l0_camera_frustum_traces(
        rx=current_col + 0.5,
        ry=current_row + 0.5,
        rz=rz + 0.015,
        heading_deg=heading_deg,
        Z_raw=Z_raw,
        l0_ok=l0_ok,
        obs_score=obs_score,
    )

    # 10. L2 3D GPR Fresnel Cone & Radar Wavefronts
    beam_traces = []
    if show_gpr_beam:
        true_depth = float(DEPTH_MAP[current_row, current_col])
        beam_traces = _gpr_wavefront_traces(
            rx=current_col + 0.5,
            ry=current_row + 0.5,
            rz=rz + 0.015,
            target_depth_m=true_depth,
        )

    # 11. Legend
    legend_traces = _legend_traces()

    all_traces = (
        [terrain]
        + psr_surfaces
        + strat_traces
        + boulder_traces
        + nav_traces
        + obstacle_traces
        + deposit_traces
        + rover_traces
        + fov_traces
        + beam_traces
        + legend_traces
    )

    fig = go.Figure(data=all_traces)

    ann = _decision_hud_annotation(
        l0_ok, l1_ok, l2_active,
        battery_pct, temperature, obs_score
    )

    n_scanned = len([d for d in scan_log if d.get('status') == 'scanned'])
    n_obstacle = len([d for d in scan_log if d.get('status') == 'obstacle'])
    n_lp = len([d for d in scan_log if d.get('status') == 'low_power'])

    # Corrected physical units: Survey Patch in meters (m), matching 5m GPR scan window
    fig.update_layout(
        paper_bgcolor='#030712',
        annotations=[ann],
        scene=dict(
            xaxis=dict(
                title=dict(text='East Survey Grid (m)', font=dict(color='#7DD3FC', size=11)),
                range=[0, GRID_SIZE],
                backgroundcolor='#050B18', gridcolor='#1E293B',
                showbackground=True, zerolinecolor='#1E293B',
                tickfont=dict(color='#7DD3FC', size=9),
            ),
            yaxis=dict(
                title=dict(text='North Survey Grid (m)', font=dict(color='#7DD3FC', size=11)),
                range=[0, GRID_SIZE],
                backgroundcolor='#050B18', gridcolor='#1E293B',
                showbackground=True, zerolinecolor='#1E293B',
                tickfont=dict(color='#7DD3FC', size=9),
            ),
            zaxis=dict(
                title=dict(text='Subsurface Depth / Elevation (m)', font=dict(color='#7DD3FC', size=11)),
                range=[-2.2, 1.1],
                backgroundcolor='#030712', gridcolor='#1E293B',
                showbackground=True, zerolinecolor='#334155',
                tickfont=dict(color='#7DD3FC', size=9),
            ),
            camera=dict(
                eye=dict(x=1.62, y=-1.65, z=1.22),
                up=dict(x=0, y=0, z=1),
            ),
            bgcolor='#030712',
            aspectmode='manual',
            aspectratio=dict(x=1.45, y=1.45, z=0.62),
        ),
        legend=dict(
            font=dict(color='#E2E8F0', size=10, family='monospace'),
            bgcolor='rgba(11, 15, 25, 0.90)',
            bordercolor='rgba(0, 229, 255, 0.35)',
            borderwidth=1,
            x=0.75, y=0.98,
        ),
        margin=dict(l=0, r=0, t=32, b=0),
        height=620,
        title=dict(
            text=(
                '<b style="color:#00E5FF">L-MINER Mk-II 3D DIGITAL TWIN</b>  ·  '
                f'<span style="color:#CBD5E1">Cell: ({current_row}, {current_col})</span>  ·  '
                f'<span style="color:#00E676">Scanned: {n_scanned}</span>  ·  '
                f'<span style="color:#FF1744">Hazards: {n_obstacle}</span>  ·  '
                f'<span style="color:#FFD600">Power-Holds: {n_lp}</span>'
            ),
            font=dict(color='#00E5FF', size=12, family='monospace'),
            x=0.5, xanchor='center', y=0.99,
        ),
    )

    return fig


if __name__ == '__main__':
    class _SampleState:
        battery = 84.0
        temperature = 30.5

    sample_log = [
        {'row': 0, 'col': 0, 'mineral': 'Re', 'confidence': 0.92, 'depth_m': 0.30, 'status': 'scanned'},
        {'row': 0, 'col': 1, 'mineral': 'Wi', 'confidence': 0.96, 'depth_m': 1.20, 'status': 'scanned'},
        {'row': 0, 'col': 2, 'mineral': 'Wi', 'confidence': 0.94, 'depth_m': 0.80, 'status': 'scanned'},
        {'row': 0, 'col': 3, 'mineral': 'OB', 'confidence': 0.00, 'depth_m': 0.00, 'status': 'obstacle'},
        {'row': 0, 'col': 4, 'mineral': 'Il', 'confidence': 0.91, 'depth_m': 0.45, 'status': 'scanned'},
    ]

    print("[3D] Building upgraded L-MINER Mk-II 3D Digital Twin...")
    fig = build_3d_figure(
        scan_log=sample_log,
        system_state=_SampleState(),
        show_gpr_beam=True,
        current_row=0, current_col=2,
        scan_index=4,
        last_l0={'safe': True, 'obstacle_score': 0.12},
        last_l1={'can_scan': True, 'reason': 'OK'},
    )
    fig.write_html('3d_test.html', include_plotlyjs='cdn')
    print("[OK] Successfully generated 3d_test.html")