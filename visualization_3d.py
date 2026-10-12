"""
L-MINER 3D Interactive Visualization — visualization_3d.py
Photorealistic 3D Digital Twin of the Lunar South Pole Autonomous Survey.

Coupled with data_generator.py:
  - Exact synchronization with MINERAL_MAP, OBSTACLE_MAP, and DEPTH_MAP
  - High-resolution lunar terrain with realistic impact crater mechanics and low polar sun illumination
  - Solid 3D rover model:
      * Gold-foil MLI insulated chassis and dark silicon solar deck
      * 6 solid 3D cylindrical wheels with rocker-bogie titanium suspension struts
      * Mast-mounted HazCam stereo vision head, robotic spectrometer arm, and parabolic antenna dish
      * Local terrain slope adaptation (pitch and roll follow surface gradient)
  - Volumetric subsurface geology:
      * 3D mineral deposit ellipsoid bodies at true physical depths (sized by ML confidence)
      * Translucent borehole core sounding columns
      * Concentric GPR radar wave propagation wavefronts
  - L0 / L1 / L2 Autonomy visualization:
      * L0: HazCam optical FOV cone and holographic obstacle hazard beacons
      * L1: 3D battery telemetry pillar and color-shifting mast thermal indicator
      * L2: Penetrating subterranean GPR sounding beam
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
    'Wi': 'Water Ice (H₂O Volatiles)',
    'Il': 'Ilmenite (FeTiO₃ Ore)',
    'Py': 'Pyroxene ((Mg,Fe)SiO₃)',
    'Re': 'Lunar Regolith Substrate',
    'OB': 'Hazardous Obstacle',
    'LP': 'Power-Save Skipped',
}

BATTERY_CAPACITY = 100.0
LOW_POWER_THRESHOLD = 20.0
MAX_TEMP_C = 50.0
NOMINAL_TEMP_C = 28.0


# ── 3D Geometric Primitive Helpers ───────────────────────────────────────────

def _rotation_matrix(yaw_deg=0.0, pitch_deg=0.0, roll_deg=0.0):
    """3D Euler rotation matrix (Yaw -> Pitch -> Roll)."""
    y = np.radians(yaw_deg)
    p = np.radians(pitch_deg)
    r = np.radians(roll_deg)

    Rz = np.array([
        [np.cos(y), -np.sin(y), 0.0],
        [np.sin(y),  np.cos(y), 0.0],
        [0.0, 0.0, 1.0]
    ])
    Ry = np.array([
        [np.cos(p), 0.0, np.sin(p)],
        [0.0, 1.0, 0.0],
        [-np.sin(p), 0.0, np.cos(p)]
    ])
    Rx = np.array([
        [1.0, 0.0, 0.0],
        [0.0, np.cos(r), -np.sin(r)],
        [0.0, np.sin(r),  np.cos(r)]
    ])
    return Rz @ Ry @ Rx


def _make_box_mesh(center, size, R=None, color='#D4AF37', opacity=1.0, name='box', hover_txt=None):
    """Solid 3D oriented bounding box mesh with realistic lighting."""
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

    x = verts[:, 0].tolist()
    y = verts[:, 1].tolist()
    z = verts[:, 2].tolist()

    # 12 triangular faces
    i = [0, 0, 4, 4, 0, 0, 1, 1, 2, 2, 3, 3]
    j = [1, 2, 5, 6, 4, 5, 5, 6, 6, 7, 7, 4]
    k = [2, 3, 6, 7, 1, 1, 2, 2, 3, 3, 0, 0]

    return go.Mesh3d(
        x=x, y=y, z=z, i=i, j=j, k=k,
        color=color, opacity=opacity, name=name,
        lighting=dict(ambient=0.45, diffuse=0.85, specular=0.40, roughness=0.45),
        showlegend=False,
        hoverinfo='skip' if hover_txt is None else 'all',
        hovertemplate=hover_txt
    )


def _make_cylinder_mesh(p1, p2, radius, n_sides=14, color='#1E293B', opacity=1.0, name='cylinder', hover_txt=None):
    """Solid 3D cylinder mesh constructed between 3D endpoints p1 and p2."""
    p1 = np.array(p1, dtype=float)
    p2 = np.array(p2, dtype=float)
    v = p2 - p1
    mag = np.linalg.norm(v)
    if mag < 1e-6:
        return None
    v_norm = v / mag

    # Orthogonal basis
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

        # Side quad faces (2 triangles)
        i.extend([b1, t1])
        j.extend([b2, t2])
        k.extend([t1, b2])

        # Bottom circle cap
        i.append(center_bottom_idx)
        j.append(nxt)
        k.append(s)

        # Top circle cap
        i.append(center_top_idx)
        j.append(t1)
        k.append(t2)

    return go.Mesh3d(
        x=verts[:, 0].tolist(),
        y=verts[:, 1].tolist(),
        z=verts[:, 2].tolist(),
        i=i, j=j, k=k,
        color=color, opacity=opacity, name=name,
        lighting=dict(ambient=0.45, diffuse=0.85, specular=0.35, roughness=0.5),
        showlegend=False,
        hoverinfo='skip' if hover_txt is None else 'all',
        hovertemplate=hover_txt
    )


def _make_ellipsoid_mesh(center, rx, ry, rz, n_lat=12, n_lon=16, color='#00E5FF', opacity=0.85, name='deposit', hover_txt=None):
    """Solid 3D ellipsoid mesh for mineral bodies."""
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
        lighting=dict(ambient=0.55, diffuse=0.9, specular=0.5, roughness=0.3),
        showlegend=False,
        hoverinfo='skip' if hover_txt is None else 'all',
        hovertemplate=hover_txt
    )


# ── High-Fidelity Lunar Polar Terrain Model ──────────────────────────────────

def _generate_lunar_terrain(grid_res=96, seed=42):
    """
    Generate high-resolution lunar south-pole terrain:
      - Multi-scale impact craters with raised rims and power-law morphology
      - Regional polar slope toward Permanently Shadowed cold traps
      - Natural fractal regolith micro-roughness
    """
    rng = np.random.default_rng(seed)
    x = np.linspace(0, GRID_SIZE, grid_res)
    y = np.linspace(0, GRID_SIZE, grid_res)
    X, Y = np.meshgrid(x, y)

    # Base undulation and regional polar depression
    Z = (
        0.16 * np.sin(0.70 * X + 0.3) * np.cos(0.60 * Y)
        + 0.09 * np.sin(1.50 * X + 0.6) * np.cos(1.30 * Y + 0.7)
        + 0.035 * (Y - 3.0)  # gentle southward polar depression
    )

    # Lunar crater catalogue (cx, cy, radius, depth)
    craters = [
        (1.5, 1.2, 0.95, 0.36),   # North-West Ice Basin (PSR-A)
        (3.8, 3.8, 0.85, 0.30),   # South-East Ice Depression (PSR-B)
        (3.5, 0.5, 0.55, 0.24),   # Obstacle crater near (0,3)
        (2.5, 1.5, 0.52, 0.22),   # Obstacle crater near (1,2)
        (1.5, 2.5, 0.54, 0.22),   # Obstacle crater near (2,1)
        (5.5, 3.5, 0.50, 0.25),   # Obstacle crater near (3,5)
        (4.5, 4.5, 0.48, 0.23),   # Obstacle crater near (4,4)
        (0.5, 5.5, 0.56, 0.26),   # Obstacle crater near (5,0)
        (5.1, 1.1, 0.42, 0.16),   # Minor impact crater
        (2.8, 5.2, 0.38, 0.14),   # Minor impact crater
    ]

    for cx, cy, radius, depth in craters:
        d = np.sqrt((X - cx)**2 + (Y - cy)**2)
        # Parabolic/Gaussian crater bowl (negative) + ejecta rim uplift (positive)
        Z -= depth * np.exp(-0.5 * (d / (radius * 0.62))**2)
        Z += depth * 0.38 * np.exp(-0.5 * ((d - radius) / (radius * 0.22))**2)

    # Micro-roughness (lunar regolith texture)
    Z += 0.018 * rng.standard_normal((grid_res, grid_res))

    return X, Y, Z * 0.62


def _surface_elevation_and_normal(row, col, Z, grid_res=96):
    """
    Interpolate terrain elevation and surface normal at cell center.
    Returns (z_elev, pitch_deg, roll_deg).
    """
    xi = int(round((col + 0.5) / GRID_SIZE * (grid_res - 1)))
    yi = int(round((row + 0.5) / GRID_SIZE * (grid_res - 1)))
    xi = np.clip(xi, 1, grid_res - 2)
    yi = np.clip(yi, 1, grid_res - 2)

    z_elev = float(Z[yi, xi])

    # Finite difference gradient
    dz_dx = (Z[yi, xi + 1] - Z[yi, xi - 1]) / (2.0 * (GRID_SIZE / grid_res))
    dz_dy = (Z[yi + 1, xi] - Z[yi - 1, xi]) / (2.0 * (GRID_SIZE / grid_res))

    pitch_deg = np.degrees(np.arctan(dz_dx))
    roll_deg = np.degrees(np.arctan(dz_dy))

    return z_elev, float(pitch_deg), float(roll_deg)


# ── Photorealistic Solid 3D Rover Model ──────────────────────────────────────

def _solid_rover_traces(rx, ry, rz, heading_deg=0.0, pitch_deg=0.0, roll_deg=0.0,
                        battery_pct=100.0, temperature=NOMINAL_TEMP_C,
                        l0_ok=True, l1_ok=True):
    """
    Construct a solid 3D digital twin of the prospecting rover:
      - Gold-foil Multi-Layer Insulation (MLI) faceted chassis body
      - Dark silicon solar panel array deck on top
      - 6 solid 3D cylindrical wheels with titanium rocker-bogie linkages
      - Directional sensor mast with dual HazCam stereo lenses
      - Robotic spectrometer arm & rear GPR radar antenna bar
      - Earth communications parabolic dish
      - L1 3D Battery Telemetry Cylinder and Mast Thermal Sphere
      - Ground status safety aura halo
    """
    traces = []
    R = _rotation_matrix(yaw_deg=heading_deg, pitch_deg=pitch_deg, roll_deg=roll_deg)

    def to_world(local_p):
        return (R @ np.array(local_p)) + np.array([rx, ry, rz])

    # 1. Main Chassis Body (Gold MLI Thermal Foil)
    chassis_mesh = _make_box_mesh(
        center=to_world([0.0, 0.0, 0.16]),
        size=[0.52, 0.36, 0.16],
        R=R,
        color='#D4AF37',  # Metallic Gold
        name='Rover Chassis (Gold MLI Foil)',
        hover_txt='<b>L-MINER Chassis</b><br>Gold Multi-Layer Insulation (MLI)<extra></extra>'
    )
    if chassis_mesh:
        traces.append(chassis_mesh)

    # 2. Solar Panel Array Deck (Top silicon deck with frame)
    solar_deck_mesh = _make_box_mesh(
        center=to_world([0.0, 0.0, 0.245]),
        size=[0.48, 0.32, 0.015],
        R=R,
        color='#0F172A',  # Dark Silicon
        name='Silicon Solar Panel Deck',
        hover_txt='<b>Solar Panel Deck</b><br>Triple-Junction GaAs Solar Cells<extra></extra>'
    )
    if solar_deck_mesh:
        traces.append(solar_deck_mesh)

    # Gold grid border on solar deck
    deck_corners = [
        [-0.24, -0.16, 0.255], [ 0.24, -0.16, 0.255],
        [ 0.24,  0.16, 0.255], [-0.24,  0.16, 0.255], [-0.24, -0.16, 0.255]
    ]
    dc_world = np.array([to_world(p) for p in deck_corners])
    traces.append(go.Scatter3d(
        x=dc_world[:, 0], y=dc_world[:, 1], z=dc_world[:, 2],
        mode='lines',
        line=dict(color='#FFD54F', width=2),
        showlegend=False, hoverinfo='skip'
    ))

    # 3. 6 Solid 3D Cylindrical Wheels with Rocker-Bogie Struts
    wheel_mounts = [
        # (x_local, y_local, z_local, side)
        (-0.20, -0.25, 0.035, -1),
        ( 0.00, -0.27, 0.035, -1),
        ( 0.20, -0.25, 0.035, -1),
        (-0.20,  0.25, 0.035,  1),
        ( 0.00,  0.27, 0.035,  1),
        ( 0.20,  0.25, 0.035,  1),
    ]

    wheel_rad = 0.065
    wheel_w = 0.055

    for wx, wy, wz, side in wheel_mounts:
        # Wheel axle endpoints
        p_inner = to_world([wx, wy - side * (wheel_w / 2.0), wz])
        p_outer = to_world([wx, wy + side * (wheel_w / 2.0), wz])

        # Solid wheel drum
        w_mesh = _make_cylinder_mesh(
            p_inner, p_outer, radius=wheel_rad, n_sides=14,
            color='#1E293B', name='Rover Wheel',
            hover_txt='<b>Rocker-Bogie Wheel</b><br>Titanium Chevron Tread<extra></extra>'
        )
        if w_mesh:
            traces.append(w_mesh)

        # Titanium hubcap marker
        hub_center = to_world([wx, wy + side * (wheel_w / 2.0), wz])
        traces.append(go.Scatter3d(
            x=[hub_center[0]], y=[hub_center[1]], z=[hub_center[2]],
            mode='markers',
            marker=dict(size=4.5, color='#CBD5E1', line=dict(color='#0F172A', width=1)),
            showlegend=False, hoverinfo='skip'
        ))

        # Titanium suspension strut connecting wheel to chassis
        chassis_anchor = to_world([wx * 0.7, side * 0.17, 0.12])
        strut_mesh = _make_cylinder_mesh(
            chassis_anchor, p_inner, radius=0.012, n_sides=8,
            color='#64748B', name='Suspension Strut'
        )
        if strut_mesh:
            traces.append(strut_mesh)

    # 4. Sensor Mast & Dual Stereo HazCam Head
    mast_base = to_world([0.18, 0.0, 0.24])
    mast_top = to_world([0.18, 0.0, 0.58])
    mast_mesh = _make_cylinder_mesh(
        mast_base, mast_top, radius=0.016, n_sides=10,
        color='#94A3B8', name='HazCam Mast'
    )
    if mast_mesh:
        traces.append(mast_mesh)

    # HazCam crossbar
    cam_l = to_world([0.18, -0.07, 0.58])
    cam_r = to_world([0.18,  0.07, 0.58])
    cam_bar_mesh = _make_cylinder_mesh(
        cam_l, cam_r, radius=0.014, n_sides=8,
        color='#334155', name='Stereo Cam Bar'
    )
    if cam_bar_mesh:
        traces.append(cam_bar_mesh)

    # Dual optical camera barrels (Cyan coated lenses)
    for c_pos in [cam_l, cam_r]:
        lens_front = c_pos + R @ np.array([0.04, 0.0, 0.0])
        lens_mesh = _make_cylinder_mesh(
            c_pos, lens_front, radius=0.012, n_sides=8,
            color='#00E5FF', name='HazCam Lens',
            hover_txt='<b>L0 HazCam Optics</b><br>Stereo Hazard Detection Lenses<extra></extra>'
        )
        if lens_mesh:
            traces.append(lens_mesh)

    # 5. L1 Thermal Indicator Sphere on Mast Peak
    t_frac = np.clip((temperature - NOMINAL_TEMP_C) / (MAX_TEMP_C - NOMINAL_TEMP_C), 0.0, 1.0)
    therm_r = int(255 * t_frac)
    therm_g = int(220 * (1.0 - t_frac))
    therm_b = int(255 * (1.0 - t_frac * 0.8))
    therm_color = f'rgb({therm_r},{therm_g},{therm_b})'
    therm_pos = to_world([0.18, 0.0, 0.63])

    traces.append(go.Scatter3d(
        x=[therm_pos[0]], y=[therm_pos[1]], z=[therm_pos[2]],
        mode='markers',
        marker=dict(
            size=7 + 4 * t_frac,
            color=therm_color,
            symbol='circle',
            line=dict(color='white', width=1.5)
        ),
        showlegend=False,
        hovertemplate=(
            f'<b>L1 Thermal Avionics</b><br>'
            f'Core Temperature: <b>{temperature:.1f}°C</b><br>'
            f'Thermal Cutoff: {MAX_TEMP_C:.0f}°C<extra></extra>'
        )
    ))

    # 6. High-Gain Earth Communications Dish
    dish_base = to_world([-0.18, 0.08, 0.25])
    dish_center = to_world([-0.20, 0.10, 0.38])
    dish_mount = _make_cylinder_mesh(dish_base, dish_center, radius=0.010, color='#64748B')
    if dish_mount:
        traces.append(dish_mount)

    # Parabolic dish rim
    dish_r = 0.08
    theta_d = np.linspace(0, 2 * np.pi, 18)
    dish_rim = np.array([dish_center + R @ np.array([
        dish_r * np.cos(t) * 0.4 - 0.03,
        dish_r * np.sin(t),
        dish_r * np.cos(t) * 0.9
    ]) for t in theta_d])
    traces.append(go.Scatter3d(
        x=dish_rim[:, 0], y=dish_rim[:, 1], z=dish_rim[:, 2],
        mode='lines',
        line=dict(color='#FFD54F', width=3),
        showlegend=False,
        hovertemplate='<b>High-Gain Antenna Dish</b><br>Direct-To-Earth Polar Telemetry<extra></extra>'
    ))

    # 7. Rear Ground Penetrating Radar (GPR) Antenna Bar
    gpr_p1 = to_world([-0.26, -0.18, 0.06])
    gpr_p2 = to_world([-0.26,  0.18, 0.06])
    gpr_bar_mesh = _make_cylinder_mesh(
        gpr_p1, gpr_p2, radius=0.012, n_sides=8,
        color='#FFD54F', name='GPR Transmit Dipole',
        hover_txt='<b>L2 GPR Antenna Array</b><br>500 MHz Ground-Coupled Dipole<extra></extra>'
    )
    if gpr_bar_mesh:
        traces.append(gpr_bar_mesh)

    # 8. Forward Spectrometer Robotic Arm
    arm_p1 = to_world([0.24, -0.06, 0.14])
    arm_p2 = to_world([0.34, -0.06, 0.06])
    arm_mesh = _make_cylinder_mesh(
        arm_p1, arm_p2, radius=0.010, color='#94A3B8',
        name='Spectrometer Arm',
        hover_txt='<b>Reflectance Spectrometer Sensor</b><br>0.5–2.5 μm Contact Optics<extra></extra>'
    )
    if arm_mesh:
        traces.append(arm_mesh)

    # 9. L1 3D Battery Telemetry Solid Pillar (Beside Rover)
    bx_pos = to_world([-0.02, -0.38, 0.02])
    bx_top = to_world([-0.02, -0.38, 0.58])
    batt_frac = np.clip(battery_pct / BATTERY_CAPACITY, 0.0, 1.0)
    batt_color = '#00E676' if battery_pct > 50 else ('#FFD600' if battery_pct > LOW_POWER_THRESHOLD else '#FF1744')

    # Glass container cylinder
    batt_frame = _make_cylinder_mesh(
        bx_pos, bx_top, radius=0.024, n_sides=10,
        color='rgba(100, 116, 139, 0.35)', name='Battery HUD'
    )
    if batt_frame:
        traces.append(batt_frame)

    # Active level cylinder
    bx_fill_top = bx_pos + (bx_top - bx_pos) * batt_frac
    if batt_frac > 0.02:
        batt_fill = _make_cylinder_mesh(
            bx_pos, bx_fill_top, radius=0.022, n_sides=10,
            color=batt_color, name='Battery Reserve',
            hover_txt=f'<b>L1 Battery Status</b><br>Charge: <b>{battery_pct:.1f}%</b><br>Cutoff: {LOW_POWER_THRESHOLD}%<extra></extra>'
        )
        if batt_fill:
            traces.append(batt_fill)

    # Text indicator at top
    traces.append(go.Scatter3d(
        x=[bx_top[0]], y=[bx_top[1]], z=[bx_top[2] + 0.06],
        mode='text',
        text=[f'🔋 {battery_pct:.0f}%'],
        textfont=dict(size=9, color=batt_color, family='monospace'),
        showlegend=False, hoverinfo='skip'
    ))

    # 10. Rover Safety Aura Halo (Floor Projection)
    halo_theta = np.linspace(0, 2 * np.pi, 40)
    halo_r = 0.44
    halo_color = '#00E676' if (l0_ok and l1_ok) else ('#FFD600' if (l0_ok and not l1_ok) else '#FF1744')

    hx = rx + halo_r * (np.cos(halo_theta) * np.cos(np.radians(heading_deg)) - np.sin(halo_theta) * np.sin(np.radians(heading_deg)))
    hy = ry + halo_r * (np.cos(halo_theta) * np.sin(np.radians(heading_deg)) + np.sin(halo_theta) * np.cos(np.radians(heading_deg)))
    hz = np.full(40, rz + 0.015)

    traces.append(go.Scatter3d(
        x=hx, y=hy, z=hz,
        mode='lines',
        line=dict(color=halo_color, width=3),
        showlegend=False,
        hovertemplate=(
            f'<b>Rover Safety Halo</b><br>'
            f'L0 Hazard Check: {"✅ ALL CLEAR" if l0_ok else "⛔ HAZARD BLOCKED"}<br>'
            f'L1 Power/Temp:   {"✅ NOMINAL" if l1_ok else "⚡ LOW POWER / THERMAL"}<extra></extra>'
        )
    ))

    return traces


# ── L0 HazCam Optical Field-of-View Cone ────────────────────────────────────

def _l0_camera_frustum_traces(rx, ry, rz, heading_deg=0.0, fov_deg=65, reach=1.35):
    """
    Render 3D optical vision volume projecting ahead from HazCam lenses.
    Visualizes active terrain inspected by L0 Safety System for hazards.
    """
    traces = []
    h = np.radians(heading_deg)
    half_fov = np.radians(fov_deg / 2)
    angles = np.linspace(h - half_fov, h + half_fov, 11)

    cam_origin = np.array([rx + 0.18 * np.cos(h), ry + 0.18 * np.sin(h), rz + 0.58])

    # Fan of optical rays
    for ang in angles:
        ray_end = np.array([rx + reach * np.cos(ang), ry + reach * np.sin(ang), rz + 0.04])
        traces.append(go.Scatter3d(
            x=[cam_origin[0], ray_end[0]],
            y=[cam_origin[1], ray_end[1]],
            z=[cam_origin[2], ray_end[2]],
            mode='lines',
            line=dict(color='rgba(0, 230, 118, 0.22)', width=1.5),
            showlegend=False, hoverinfo='skip'
        ))

    # Outer perimeter arc on ground
    arc_x = [rx + reach * np.cos(a) for a in angles]
    arc_y = [ry + reach * np.sin(a) for a in angles]
    arc_z = [rz + 0.04] * len(angles)

    traces.append(go.Scatter3d(
        x=arc_x, y=arc_y, z=arc_z,
        mode='lines',
        line=dict(color='rgba(0, 230, 118, 0.65)', width=2.5),
        showlegend=False,
        hovertemplate='<b>L0 HazCam Optical Frustum</b><br>Real-time autonomous clearance inspection<extra></extra>'
    ))

    return traces


# ── Holographic Obstacle Hazard Beacons ─────────────────────────────────────

def _obstacle_hazard_traces(row, col, Z_raw):
    """
    Render holographic hazard beacons at verified obstacles (OBSTACLE_MAP > 0.75).
    """
    cx, cy = col + 0.5, row + 0.5
    sz, _, _ = _surface_elevation_and_normal(row, col, Z_raw)
    traces = []

    # Hazard beam column
    column_mesh = _make_cylinder_mesh(
        [cx, cy, sz], [cx, cy, sz + 0.75], radius=0.035, n_sides=8,
        color='rgba(255, 23, 68, 0.85)', name='Hazard Pillar',
        hover_txt=f'<b>⛔ L0 HAZARD EXCLUSION ZONE</b><br>Cell ({row}, {col})<br>Slope / Boulder Hazard > 0.75<extra></extra>'
    )
    if column_mesh:
        traces.append(column_mesh)

    # Danger beacon marker at top
    traces.append(go.Scatter3d(
        x=[cx], y=[cy], z=[sz + 0.82],
        mode='markers+text',
        marker=dict(
            size=11, color='#FF1744', symbol='diamond',
            line=dict(color='white', width=1.5)
        ),
        text=['⛔'],
        textfont=dict(size=11),
        showlegend=False,
        hovertemplate=f'<b>L0 EXCLUSION ZONE</b><br>Coordinates: ({row}, {col})<br>Autonomous Pathing Bypassed<extra></extra>'
    ))

    # Ground boundary perimeter ring
    theta = np.linspace(0, 2 * np.pi, 28)
    hr = 0.44
    traces.append(go.Scatter3d(
        x=cx + hr * np.cos(theta),
        y=cy + hr * np.sin(theta),
        z=np.full(28, sz + 0.02),
        mode='lines',
        line=dict(color='rgba(255, 23, 68, 0.75)', width=2),
        showlegend=False, hoverinfo='skip'
    ))

    return traces


# ── L2 Subsurface GPR Wave Propagation Cone ─────────────────────────────────

def _gpr_wavefront_traces(rx, ry, rz, target_depth_m=1.0):
    """
    Render subterranean radar wave propagation:
      - Sounding beam line from GPR dipole to target layer
      - 3 concentric spherical wavefront surfaces spreading in dielectric soil
      - Horizontal dielectric reflection horizon plane at true depth
    """
    traces = []
    target_z = -target_depth_m

    # Central pencil beam
    traces.append(go.Scatter3d(
        x=[rx, rx], y=[ry, ry], z=[rz + 0.06, target_z],
        mode='lines',
        line=dict(color='#FFD54F', width=3.5, dash='dash'),
        showlegend=False,
        hovertemplate=f'<b>L2 GPR Sounding Pulse</b><br>Penetrating to Horizon: {target_depth_m:.2f} m<extra></extra>'
    ))

    # Concentric spherical wavefront rings in subterranean dielectric
    theta = np.linspace(0, 2 * np.pi, 24)
    for frac in [0.35, 0.70, 1.0]:
        z_slice = rz - frac * (rz - target_z)
        r_slice = 0.14 + 0.26 * frac
        traces.append(go.Scatter3d(
            x=rx + r_slice * np.cos(theta),
            y=ry + r_slice * np.sin(theta),
            z=np.full(24, z_slice),
            mode='lines',
            line=dict(color=f'rgba(255, 213, 79, {0.70 - 0.25 * frac})', width=2),
            showlegend=False, hoverinfo='skip'
        ))

    # Dielectric Reflector Horizon Plane (Small subterranean disc)
    reflector_r = 0.38
    traces.append(go.Scatter3d(
        x=rx + reflector_r * np.cos(theta),
        y=ry + reflector_r * np.sin(theta),
        z=np.full(24, target_z),
        mode='lines',
        line=dict(color='#FFD600', width=2.5),
        showlegend=False,
        hovertemplate=f'<b>Dielectric Reflection Horizon</b><br>Target Depth: {target_depth_m:.2f} m<extra></extra>'
    ))

    return traces


# ── Volumetric Subsurface Geological Deposits ───────────────────────────────

def _volumetric_deposit_traces(scanned):
    """
    Render volumetric mineral deposits as 3D ellipsoids at their exact depth:
      - 3D deposit ellipsoid body (volume proportional to ML confidence)
      - Translucent vertical borehole sounding column from surface to deposit
      - Surface detection target reticle
    """
    traces = []

    for (row, col), info in scanned.items():
        status = info.get('status', 'scanned')
        if status == 'obstacle':
            continue  # Handled by obstacle hazard pillars

        mineral_code = info.get('mineral', 'Re')[:2]
        depth = info.get('depth_m', float(DEPTH_MAP[row, col]))
        conf = info.get('confidence', 0.85)

        cx, cy = col + 0.5, row + 0.5
        cz = -depth

        color = MINERAL_3D_COLORS.get(mineral_code, MINERAL_3D_COLORS['Re'])
        label = MINERAL_LABELS.get(mineral_code, 'Mineral Deposit')

        # Radii scaled by confidence (real mineral lens geometry)
        rx = 0.16 + 0.12 * conf
        ry = 0.16 + 0.12 * conf
        rz = 0.08 + 0.06 * conf

        # 3D Mineral Body Mesh
        deposit_mesh = _make_ellipsoid_mesh(
            center=[cx, cy, cz], rx=rx, ry=ry, rz=rz,
            color=color, opacity=0.90, name=label,
            hover_txt=(
                f'<b>{label}</b><br>'
                f'Survey Grid: ({row}, {col})<br>'
                f'Physical Depth: <b>{depth:.2f} m</b><br>'
                f'ML Confidence: <b>{conf * 100:.1f}%</b><extra></extra>'
            )
        )
        if deposit_mesh:
            traces.append(deposit_mesh)

        # Translucent vertical borehole sounding core cylinder
        core_mesh = _make_cylinder_mesh(
            [cx, cy, 0.02], [cx, cy, cz], radius=0.016, n_sides=8,
            color=color, opacity=0.35, name='Borehole Sounding Core'
        )
        if core_mesh:
            traces.append(core_mesh)

        # Surface detection reticle
        theta = np.linspace(0, 2 * np.pi, 20)
        traces.append(go.Scatter3d(
            x=cx + 0.22 * np.cos(theta),
            y=cy + 0.22 * np.sin(theta),
            z=np.full(20, 0.025),
            mode='lines',
            line=dict(color=color, width=1.5),
            showlegend=False, hoverinfo='skip'
        ))

    return traces


# ── Permanently Shadowed Regions (PSR) Cold Traps ────────────────────────────

def _psr_cold_traps():
    """
    Render thermal cold-trap regions accurately overlaying
    areas where water ice volatiles survive in MINERAL_MAP.
    """
    surfaces = []
    # PSR-A (North-West Basin cold trap)
    px1 = np.linspace(0.1, 2.9, 28)
    py1 = np.linspace(0.1, 2.5, 28)
    PX1, PY1 = np.meshgrid(px1, py1)
    PZ1 = np.full_like(PX1, -0.16)

    surfaces.append(go.Surface(
        x=PX1, y=PY1, z=PZ1,
        colorscale=[[0, 'rgba(0, 30, 90, 0.28)'], [1, 'rgba(0, 200, 255, 0.35)']],
        showscale=False, opacity=0.38,
        name='Permanently Shadowed Region (PSR-A)',
        hovertemplate='<b>Permanently Shadowed Region (PSR-A)</b><br>Thermal Cold Trap (< 40 K)<br>High Volatile Retention<extra></extra>'
    ))

    # PSR-B (South-East Depression)
    px2 = np.linspace(2.8, 4.9, 22)
    py2 = np.linspace(2.8, 4.9, 22)
    PX2, PY2 = np.meshgrid(px2, py2)
    PZ2 = np.full_like(PX2, -0.14)

    surfaces.append(go.Surface(
        x=PX2, y=PY2, z=PZ2,
        colorscale=[[0, 'rgba(0, 25, 80, 0.26)'], [1, 'rgba(0, 180, 240, 0.32)']],
        showscale=False, opacity=0.35,
        name='Permanently Shadowed Region (PSR-B)',
        hovertemplate='<b>Permanently Shadowed Region (PSR-B)</b><br>Secondary Cold Trap Basin<extra></extra>'
    ))

    return surfaces


# ── Survey Grid, Trail & Target Reticle ──────────────────────────────────────

def _grid_and_trail_traces(scanned, current_row, current_col, scan_index, scan_order, Z_raw):
    """Grid lines, traversal breadcrumbs, and next target reticle."""
    traces = []

    # 1. Coordinate Grid Lines
    for i in range(GRID_SIZE + 1):
        v = float(i)
        for xs, ys in [([0, GRID_SIZE], [v, v]), ([v, v], [0, GRID_SIZE])]:
            traces.append(go.Scatter3d(
                x=xs, y=ys, z=[0.015, 0.015],
                mode='lines',
                line=dict(color='rgba(56, 189, 248, 0.20)', width=1.5),
                showlegend=False, hoverinfo='skip'
            ))

    # 2. Glowing Traversal Breadcrumb Trail
    if scanned:
        cells = list(scanned.keys())
        xs = [c + 0.5 for _, c in cells] + [current_col + 0.5]
        ys = [r + 0.5 for r, _ in cells] + [current_row + 0.5]
        zs = [0.035] * len(xs)

        traces.append(go.Scatter3d(
            x=xs, y=ys, z=zs,
            mode='lines+markers',
            line=dict(color='rgba(0, 230, 118, 0.45)', width=3, dash='dot'),
            marker=dict(size=3.5, color='#00E676'),
            showlegend=False,
            hovertemplate='Rover Traversal Waypoint<extra></extra>'
        ))

    # 3. Next Target Reticle
    if scan_order and scan_index < len(scan_order):
        nr, nc = scan_order[scan_index]
        cx, cy = nc + 0.5, nr + 0.5
        sz, _, _ = _surface_elevation_and_normal(nr, nc, Z_raw)
        theta = np.linspace(0, 2 * np.pi, 28)

        traces.append(go.Scatter3d(
            x=cx + 0.44 * np.cos(theta),
            y=cy + 0.44 * np.sin(theta),
            z=np.full(28, sz + 0.04),
            mode='lines',
            line=dict(color='#FFD600', width=2.5),
            showlegend=False,
            hovertemplate=f'<b>Next Survey Target</b><br>Coordinates: ({nr}, {nc})<extra></extra>'
        ))

    return traces


# ── Legend Dummy Traces ──────────────────────────────────────────────────────

def _legend_traces():
    items = [
        ('Water Ice (H₂O)',         '#00E5FF'),
        ('Ilmenite (FeTiO₃)',       '#FF9100'),
        ('Pyroxene (Silicate)',     '#00E676'),
        ('Lunar Regolith',          '#94A3B8'),
        ('⛔ L0 Hazard Obstacle',    '#FF1744'),
        ('⚡ L1 Power Hold',        '#FFD600'),
        ('🔬 L2 GPR Radar Sounding','#FFD54F'),
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
    """Aerospace-grade HUD overlay annotation."""
    l0_txt = '✅ L0 HAZARD: CLEAR' if l0_ok else '⛔ L0 HAZARD: BLOCKED'
    if not l0_ok and obs_score is not None:
        l0_txt += f' ({obs_score:.2f})'

    l1_txt = '✅ L1 RESOURCES: NOMINAL' if l1_ok else f'⚡ L1 RESOURCE: PAUSED ({battery_pct:.0f}%)'
    l2_txt = '🔬 L2 ML SOUNDING: ACTIVE' if l2_active else '💤 L2 ML SOUNDING: STANDBY'

    lines = [
        '<b style="color:#00E5FF;letter-spacing:1px">L-MINER AUTONOMY HUD</b>',
        f'<span style="color:{"#00E676" if l0_ok else "#FF1744"}">{l0_txt}</span>',
        f'<span style="color:{"#00E676" if l1_ok else "#FFD600"}">{l1_txt}</span>',
        f'<span style="color:{"#00E5FF" if l2_active else "#94A3B8"}">{l2_txt}</span>',
        f'<span style="color:#7DD3FC">AVIONICS: {temperature:.1f}°C  |  PWR: {battery_pct:.0f}%</span>',
    ]

    return dict(
        text='<br>'.join(lines),
        align='left',
        showarrow=False,
        xref='paper', yref='paper',
        x=0.01, y=0.98,
        bordercolor='rgba(0, 229, 255, 0.40)',
        borderwidth=1,
        borderpad=8,
        bgcolor='rgba(3, 7, 18, 0.90)',
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
    Build master photorealistic 3D digital twin of the lunar south pole mission.
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
    obs_score = last_l0.get('obstacle_score') if last_l0 else None

    # Calculate dynamic heading
    heading_deg = 0.0
    if scan_order and scan_index < len(scan_order):
        next_r, next_c = scan_order[scan_index]
        dr = next_r - current_row
        dc = next_c - current_col
        if dr != 0 or dc != 0:
            heading_deg = np.degrees(np.arctan2(dr, dc))
    elif len(scan_log) >= 2:
        prev = scan_log[-2]
        heading_deg = np.degrees(np.arctan2(current_row - prev['row'], current_col - prev['col']))

    # 1. High-Resolution Photorealistic Terrain
    X, Y, Z_raw = _generate_lunar_terrain(grid_res=96, seed=42)

    terrain = go.Surface(
        x=X, y=Y, z=Z_raw,
        colorscale=[
            [0.00, '#020306'],  # deep shadowed crater floor (PSR)
            [0.15, '#0A0D14'],  # shadowed interior walls
            [0.35, '#171C26'],  # basaltic mare floor
            [0.55, '#2B3342'],  # highland regolith
            [0.75, '#4A5568'],  # illuminated slope
            [0.90, '#7A889E'],  # ejecta blanket
            [1.00, '#A8B6CC'],  # sunlit rim crest highlights
        ],
        showscale=False,
        lighting=dict(
            ambient=0.35,
            diffuse=0.85,
            roughness=0.65,
            specular=0.25,
            fresnel=0.20
        ),
        lightposition=dict(x=12.0, y=-4.0, z=2.2),  # Low polar sun angle
        name='Lunar South Pole Terrain',
        hovertemplate='Lunar Surface Elevation: %{z:.2f} m<extra></extra>',
    )

    # 2. Permanent Shadowed Regions (PSR)
    psr_surfaces = _psr_cold_traps()

    # 3. Grid Lines, Traversal Breadcrumb Trail & Target Reticle
    nav_traces = _grid_and_trail_traces(scanned, current_row, current_col, scan_index, scan_order, Z_raw)

    # 4. Obstacle Hazard Holographic Beacons
    obstacle_traces = []
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if OBSTACLE_MAP[r, c] > 0.75:
                obstacle_traces.extend(_obstacle_hazard_traces(r, c, Z_raw))

    # 5. Volumetric Subsurface Geological Deposits
    deposit_traces = _volumetric_deposit_traces(scanned)

    # 6. Solid 3D Rover Digital Twin
    rz, pitch_deg, roll_deg = _surface_elevation_and_normal(current_row, current_col, Z_raw)
    rover_traces = _solid_rover_traces(
        rx=current_col + 0.5,
        ry=current_row + 0.5,
        rz=rz + 0.02,
        heading_deg=heading_deg,
        pitch_deg=pitch_deg,
        roll_deg=roll_deg,
        battery_pct=battery_pct,
        temperature=temperature,
        l0_ok=l0_ok,
        l1_ok=l1_ok,
    )

    # 7. L0 HazCam Optical Frustum
    fov_traces = _l0_camera_frustum_traces(
        rx=current_col + 0.5,
        ry=current_row + 0.5,
        rz=rz + 0.02,
        heading_deg=heading_deg,
    )

    # 8. L2 GPR Radar Wave Propagation Pulse
    beam_traces = []
    if show_gpr_beam:
        true_depth = float(DEPTH_MAP[current_row, current_col])
        beam_traces = _gpr_wavefront_traces(
            rx=current_col + 0.5,
            ry=current_row + 0.5,
            rz=rz + 0.02,
            target_depth_m=true_depth,
        )

    # 9. Legend
    legend_traces = _legend_traces()

    # Assemble all 3D layers
    all_traces = (
        [terrain]
        + psr_surfaces
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

    fig.update_layout(
        paper_bgcolor='#030712',
        annotations=[ann],
        scene=dict(
            xaxis=dict(
                title=dict(text='East Traversal (km)', font=dict(color='#7DD3FC', size=11)),
                range=[0, GRID_SIZE],
                backgroundcolor='#050B18', gridcolor='#1E293B',
                showbackground=True, zerolinecolor='#1E293B',
                tickfont=dict(color='#7DD3FC', size=9),
            ),
            yaxis=dict(
                title=dict(text='North Traversal (km)', font=dict(color='#7DD3FC', size=11)),
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
                eye=dict(x=1.60, y=-1.65, z=1.20),
                up=dict(x=0, y=0, z=1),
            ),
            bgcolor='#030712',
            aspectmode='manual',
            aspectratio=dict(x=1.45, y=1.45, z=0.60),
        ),
        legend=dict(
            font=dict(color='#E2E8F0', size=10, family='monospace'),
            bgcolor='rgba(11, 15, 25, 0.90)',
            bordercolor='rgba(0, 229, 255, 0.35)',
            borderwidth=1,
            x=0.76, y=0.98,
        ),
        margin=dict(l=0, r=0, t=32, b=0),
        height=600,
        title=dict(
            text=(
                '<b style="color:#00E5FF">L-MINER 3D DIGITAL TWIN</b>  ·  '
                f'<span style="color:#CBD5E1">Rover Pos: ({current_row}, {current_col})</span>  ·  '
                f'<span style="color:#00E676">Scanned: {n_scanned}</span>  ·  '
                f'<span style="color:#FF1744">Hazards: {n_obstacle}</span>  ·  '
                f'<span style="color:#FFD600">Power-Saves: {n_lp}</span>'
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
        {'row': 0, 'col': 1, 'mineral': 'Wi', 'confidence': 0.98, 'depth_m': 1.20, 'status': 'scanned'},
        {'row': 0, 'col': 2, 'mineral': 'Wi', 'confidence': 0.96, 'depth_m': 0.80, 'status': 'scanned'},
        {'row': 0, 'col': 3, 'mineral': 'OB', 'confidence': 0.00, 'depth_m': 0.00, 'status': 'obstacle'},
        {'row': 0, 'col': 4, 'mineral': 'Il', 'confidence': 0.91, 'depth_m': 0.40, 'status': 'scanned'},
    ]

    print("[3D] Building high-fidelity 3D Digital Twin...")
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
    print("[OK] Successfully generated photorealistic 3d_test.html")
