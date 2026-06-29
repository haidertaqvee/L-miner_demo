
"""
L-MINER 3D Visualization  —  visualization_3d.py

Shows the L0 / L1 / L2 decision pipeline in real-time 3D:

  L0  —  Safety Layer
          • Camera FOV cone in front of rover (what it sees)
          • Obstacle cells highlighted with red warning pillars
          • Path travelled shown as green trail
          • Next-cell preview with pulsing yellow marker

  L1  —  Resource Manager
          • Battery bar rendered as a 3D bar-chart pillar beside rover
          • Thermal indicator sphere on the rover mast
          • Low-power / thermal-limit warning text annotations

  L2  —  Science (runs only when L0 + L1 both green)
          • Downward GPR beam cone from antenna
          • Subsurface mineral spheres at true depth
          • Dotted vertical connection lines surface → deposit
          • Confidence encoded as sphere size

Embed in dashboard:
    from visualization_3d import build_3d_figure
    fig = build_3d_figure(scan_log, system_state, show_gpr_beam, row, col)

Standalone test:
    python visualization_3d.py
"""

import numpy as np
import plotly.graph_objects as go

# ── Constants ────────────────────────────────────────────────────────────────

MINERAL_3D_COLORS = {
    'Re': 'rgba(120,120,130,0.85)',
    'Wi': 'rgba(41,182,246,0.92)',
    'Il': 'rgba(255,160,0,0.90)',
    'Py': 'rgba(102,187,106,0.90)',
    'OB': 'rgba(220,50,50,0.90)',
    'LP': 'rgba(255,170,0,0.70)',   # low-power skipped
}

MINERAL_LABELS = {
    'Re': 'Regolith', 'Wi': 'Water Ice',
    'Il': 'Ilmenite', 'Py': 'Pyroxene',
    'OB': 'Obstacle', 'LP': 'Low Power Skip',
}

MINERAL_DEPTHS = {
    'Wi': 1.20, 'Il': 0.80, 'Py': 1.00, 'Re': 0.50, 'OB': 0.0, 'LP': 0.0
}

# Must match data_generator.py MINERAL_MAP / OBSTACLE_MAP
GRID = [
    ['Wi', 'Re', 'Il', 'Py', 'Re', 'Wi'],
    ['Re', 'OB', 'Re', 'Wi', 'Il', 'Re'],
    ['Py', 'Re', 'Wi', 'Re', 'OB', 'Py'],
    ['Il', 'Wi', 'Re', 'Py', 'Re', 'Il'],
    ['Re', 'Re', 'OB', 'Il', 'Wi', 'Re'],
    ['Wi', 'Py', 'Re', 'Re', 'Py', 'Wi'],
]

BATTERY_CAPACITY = 100.0
LOW_POWER_THRESHOLD = 20.0
MAX_TEMP_C = 50.0
NOMINAL_TEMP_C = 28.0


# ── Terrain ──────────────────────────────────────────────────────────────────

def _generate_lunar_terrain(grid_size=72, seed=7):
    rng = np.random.default_rng(seed)
    x = np.linspace(0, 6, grid_size)
    y = np.linspace(0, 6, grid_size)
    X, Y = np.meshgrid(x, y)

    Z = (
        0.18 * np.sin(0.9 * X) * np.cos(0.7 * Y) +
        0.12 * np.sin(1.8 * X + 0.4) * np.cos(1.5 * Y + 0.3) +
        0.04 * rng.standard_normal((grid_size, grid_size))
    )

    craters = [
        (1.5, 1.0, 0.70, 0.28), (4.2, 4.5, 0.50, 0.18),
        (2.8, 3.8, 0.35, 0.12), (0.8, 4.2, 0.45, 0.16),
        (5.0, 1.8, 0.60, 0.22), (3.5, 0.5, 0.25, 0.09),
    ]
    for cx, cy, radius, depth in craters:
        d = np.sqrt((X - cx)**2 + (Y - cy)**2)
        Z -= depth * np.exp(-0.5 * (d / (radius * 0.6))**2)
        Z += depth * 0.45 * np.exp(-0.5 * ((d - radius) / (radius * 0.25))**2)

    Z += 0.04 * Y          # slight south-pole tilt
    return X, Y, Z * 0.55  # scale height for visual clarity


def _surface_z_at(row, col, Z, grid_size=72):
    """Interpolate terrain Z at a given grid cell centre."""
    xi = int(round((col + 0.5) / 6 * (grid_size - 1)))
    yi = int(round((row + 0.5) / 6 * (grid_size - 1)))
    xi = np.clip(xi, 0, grid_size - 1)
    yi = np.clip(yi, 0, grid_size - 1)
    return float(Z[yi, xi])


# ── Rover ─────────────────────────────────────────────────────────────────────

def _rover_traces(rx, ry, rz, heading_deg=0,
                  battery_pct=100, temperature=NOMINAL_TEMP_C,
                  l0_ok=True, l1_ok=True):
    """
    Full rover model + L1 status indicators.

    Visual indicators:
      - Battery pillar (green→amber→red) alongside chassis
      - Mast-tip thermal sphere (blue→yellow→red)
      - L0/L1 halo ring at base (green / orange / red)
    """
    traces = []
    h = np.radians(heading_deg)
    cos_h, sin_h = np.cos(h), np.sin(h)

    def rot(dx, dy):
        return dx * cos_h - dy * sin_h, dx * sin_h + dy * cos_h

    # ── Chassis outline ─────────────────────────────────
    chassis_pts = [(-0.22, -0.12), (0.22, -0.12), (0.22, 0.12),
                   (-0.22, 0.12), (-0.22, -0.12)]
    cx_r = [rx + rot(dx, dy)[0] for dx, dy in chassis_pts]
    cy_r = [ry + rot(dx, dy)[1] for dx, dy in chassis_pts]
    for z_face in [rz + 0.08, rz + 0.20]:
        traces.append(go.Scatter3d(
            x=cx_r, y=cy_r, z=[z_face] * 5,
            mode='lines', line=dict(color='#A0A8B0', width=3),
            showlegend=False, hoverinfo='skip'
        ))
    for i in range(4):
        traces.append(go.Scatter3d(
            x=[cx_r[i], cx_r[i]], y=[cy_r[i], cy_r[i]],
            z=[rz + 0.08, rz + 0.20],
            mode='lines', line=dict(color='#A0A8B0', width=3),
            showlegend=False, hoverinfo='skip'
        ))

    # ── Wheels ──────────────────────────────────────────
    for wx_off in [-0.18, 0.0, 0.18]:
        for wy_off in [-0.18, 0.18]:
            theta = np.linspace(0, 2 * np.pi, 16)
            wc_x, wc_y = rot(wx_off, wy_off)
            wrad = 0.055
            traces.append(go.Scatter3d(
                x=[rx + wc_x + wrad * np.cos(t) * sin_h for t in theta],
                y=[ry + wc_y + wrad * np.cos(t) * cos_h for t in theta],
                z=[rz + 0.04 + wrad * np.sin(t) for t in theta],
                mode='lines', line=dict(color='#2A2A35', width=2),
                showlegend=False, hoverinfo='skip'
            ))

    # ── Mast ────────────────────────────────────────────
    mast_dx, mast_dy = rot(0.15, 0.0)
    traces.append(go.Scatter3d(
        x=[rx + mast_dx, rx + mast_dx],
        y=[ry + mast_dy, ry + mast_dy],
        z=[rz + 0.20, rz + 0.52],
        mode='lines', line=dict(color='#C8C8C8', width=4),
        showlegend=False, hoverinfo='skip'
    ))

    # ── Thermal indicator on mast tip ───────────────────
    # Blue (cool) → Yellow (warm) → Red (hot)
    t_frac = np.clip((temperature - NOMINAL_TEMP_C) / (MAX_TEMP_C - NOMINAL_TEMP_C), 0, 1)
    r_ch = int(255 * t_frac)
    g_ch = int(200 * (1 - t_frac))
    b_ch = int(255 * (1 - t_frac))
    therm_color = f'rgb({r_ch},{g_ch},{b_ch})'
    therm_size  = 5 + 4 * t_frac          # grows as it gets hotter
    traces.append(go.Scatter3d(
        x=[rx + mast_dx], y=[ry + mast_dy], z=[rz + 0.54],
        mode='markers',
        marker=dict(size=therm_size, color=therm_color,
                    symbol='circle',
                    line=dict(color='white', width=1)),
        name=f'Temp: {temperature:.1f}°C',
        showlegend=False,
        hovertemplate=f'<b>Thermal Sensor</b><br>Temp: {temperature:.1f}°C<br>'
                      f'Max: {MAX_TEMP_C}°C<extra></extra>'
    ))

    # ── GPR antenna bar ─────────────────────────────────
    ant_x1, ant_y1 = rot(-0.10, -0.20)
    ant_x2, ant_y2 = rot(-0.10,  0.20)
    traces.append(go.Scatter3d(
        x=[rx + ant_x1, rx + ant_x2],
        y=[ry + ant_y1, ry + ant_y2],
        z=[rz + 0.06, rz + 0.06],
        mode='lines', line=dict(color='#FFD54F', width=5),
        showlegend=False, hoverinfo='skip'
    ))

    # ── Battery pillar (L1 visual) ──────────────────────
    #  Rendered as a thin vertical bar beside the rover
    batt_frac = np.clip(battery_pct / BATTERY_CAPACITY, 0.0, 1.0)
    batt_height = 0.50 * batt_frac           # max 0.5 units tall
    batt_color = (
        '#00FF88' if battery_pct > 50 else
        '#FFAA00' if battery_pct > LOW_POWER_THRESHOLD else
        '#FF4444'
    )
    bx_off, by_off = rot(0.0, -0.30)
    bx = rx + bx_off
    by = ry + by_off
    # Bar background (grey empty)
    traces.append(go.Scatter3d(
        x=[bx, bx], y=[by, by], z=[rz, rz + 0.50],
        mode='lines', line=dict(color='rgba(60,60,80,0.6)', width=6),
        showlegend=False, hoverinfo='skip'
    ))
    # Bar fill (coloured level)
    if batt_height > 0:
        traces.append(go.Scatter3d(
            x=[bx, bx], y=[by, by], z=[rz, rz + batt_height],
            mode='lines', line=dict(color=batt_color, width=6),
            showlegend=False,
            name=f'Battery {battery_pct:.0f}%',
            hovertemplate=f'<b>L1 Battery</b><br>{battery_pct:.1f}%<br>'
                          f'Threshold: {LOW_POWER_THRESHOLD}%<extra></extra>'
        ))
    # Battery label at top
    traces.append(go.Scatter3d(
        x=[bx], y=[by], z=[rz + 0.56],
        mode='text',
        text=[f'🔋{battery_pct:.0f}%'],
        textfont=dict(size=9, color=batt_color),
        showlegend=False, hoverinfo='skip'
    ))

    # ── L0/L1 status halo ring at rover base ────────────
    theta = np.linspace(0, 2 * np.pi, 40)
    halo_r = 0.35
    halo_color = (
        '#00FF88' if (l0_ok and l1_ok) else
        '#FFAA00' if (l0_ok and not l1_ok) else
        '#FF4444'
    )
    traces.append(go.Scatter3d(
        x=rx + halo_r * np.cos(theta),
        y=ry + halo_r * np.sin(theta),
        z=np.full(40, rz),
        mode='lines',
        line=dict(color=halo_color, width=3),
        showlegend=False,
        hovertemplate=(
            f'<b>Status Halo</b><br>'
            f'L0 Safety: {"✅ OK" if l0_ok else "⛔ BLOCKED"}<br>'
            f'L1 Resources: {"✅ OK" if l1_ok else "⚡ LOW"}<extra></extra>'
        )
    ))

    return traces


# ── L0 Camera FOV Cone ───────────────────────────────────────────────────────

def _l0_fov_traces(rx, ry, rz, heading_deg=0, fov_deg=60, reach=1.2):
    """
    Show the stereo camera field-of-view as a fan of lines ahead of the rover.
    This is what L0 is 'looking at' to detect obstacles.
    """
    traces = []
    h = np.radians(heading_deg)
    half_fov = np.radians(fov_deg / 2)

    # Fan of rays
    angles = np.linspace(h - half_fov, h + half_fov, 9)
    for ang in angles:
        end_x = rx + reach * np.cos(ang)
        end_y = ry + reach * np.sin(ang)
        traces.append(go.Scatter3d(
            x=[rx, end_x], y=[ry, end_y], z=[rz + 0.45, rz + 0.45],
            mode='lines',
            line=dict(color='rgba(0,255,136,0.25)', width=1),
            showlegend=False, hoverinfo='skip'
        ))

    # Arc connecting ray tips
    arc_x = [rx + reach * np.cos(a) for a in angles]
    arc_y = [ry + reach * np.sin(a) for a in angles]
    arc_z = [rz + 0.45] * len(angles)
    traces.append(go.Scatter3d(
        x=arc_x, y=arc_y, z=arc_z,
        mode='lines',
        line=dict(color='rgba(0,255,136,0.40)', width=2),
        showlegend=False,
        hovertemplate='<b>L0 Camera FOV</b><br>Scanning for obstacles<extra></extra>'
    ))

    return traces


# ── Obstacle Warning Pillars ──────────────────────────────────────────────────

def _obstacle_warning_traces(row, col):
    """Red pulsing marker + vertical danger pillar over obstacle cells."""
    cx, cy = col + 0.5, row + 0.5
    traces = []

    # Danger pillar
    traces.append(go.Scatter3d(
        x=[cx, cx], y=[cy, cy], z=[0.0, 0.60],
        mode='lines',
        line=dict(color='rgba(255,50,50,0.70)', width=4),
        showlegend=False,
        hovertemplate=f'<b>⛔ L0 OBSTACLE</b><br>Grid ({row},{col})<extra></extra>'
    ))
    # Warning sphere at top
    traces.append(go.Scatter3d(
        x=[cx], y=[cy], z=[0.65],
        mode='markers+text',
        marker=dict(size=10, color='rgba(255,60,60,0.85)',
                    symbol='circle',
                    line=dict(color='white', width=2)),
        text=['⛔'],
        textfont=dict(size=12),
        showlegend=False,
        hovertemplate=f'<b>⛔ L0 OBSTACLE</b><br>Grid ({row},{col})<br>'
                      f'L0 blocked traversal<extra></extra>'
    ))
    # Danger ring
    theta = np.linspace(0, 2 * np.pi, 30)
    r = 0.45
    traces.append(go.Scatter3d(
        x=cx + r * np.cos(theta), y=cy + r * np.sin(theta),
        z=np.full(30, 0.01),
        mode='lines',
        line=dict(color='rgba(255,80,80,0.50)', width=2),
        showlegend=False, hoverinfo='skip'
    ))
    return traces


# ── GPR Beam ─────────────────────────────────────────────────────────────────

def _gpr_beam_traces(rx, ry, rz, depth=1.2):
    """L2 GPR pulse: vertical beam + spreading cone tip underground."""
    traces = []
    # Main beam
    traces.append(go.Scatter3d(
        x=[rx, rx], y=[ry, ry], z=[rz + 0.06, -(depth * 0.9)],
        mode='lines',
        line=dict(color='rgba(255,213,79,0.75)', width=3, dash='dot'),
        showlegend=False,
        hovertemplate='<b>L2 GPR Beam</b><br>Penetrating to {:.2f}m<extra></extra>'.format(depth)
    ))
    # Spreading cone at target depth
    cone_r = 0.18
    theta = np.linspace(0, 2 * np.pi, 24)
    traces.append(go.Scatter3d(
        x=rx + cone_r * np.cos(theta),
        y=ry + cone_r * np.sin(theta),
        z=np.full(24, -depth),
        mode='lines',
        line=dict(color='rgba(255,213,79,0.35)', width=2),
        showlegend=False, hoverinfo='skip'
    ))
    # Side legs of cone
    for ang in [0, np.pi/2, np.pi, 3*np.pi/2]:
        traces.append(go.Scatter3d(
            x=[rx, rx + cone_r * np.cos(ang)],
            y=[ry, ry + cone_r * np.sin(ang)],
            z=[rz + 0.06, -depth],
            mode='lines',
            line=dict(color='rgba(255,213,79,0.20)', width=1),
            showlegend=False, hoverinfo='skip'
        ))
    return traces


# ── Mineral Deposits ──────────────────────────────────────────────────────────

def _deposit_traces(scanned):
    """
    Underground mineral spheres with:
    - Size ∝ confidence
    - Vertical dotted connection line
    - Color by mineral type
    Only drawn when L2 ran (status == 'scanned').
    """
    traces = []
    for (row, col), info in scanned.items():
        mineral = info.get('mineral', 'Re')
        depth   = info.get('depth_m', MINERAL_DEPTHS.get(mineral, 0.5))
        status  = info.get('status', 'scanned')
        conf    = info.get('confidence', 0.7)
        cx, cy  = col + 0.5, row + 0.5

        if status == 'obstacle':
            continue   # obstacles shown separately by _obstacle_warning_traces

        if status == 'low_power':
            color = MINERAL_3D_COLORS['LP']
            label = 'Low Power Skip'
            sz    = 5
        else:
            mc = mineral[:2]
            color = MINERAL_3D_COLORS.get(mc, MINERAL_3D_COLORS['Re'])
            label = MINERAL_LABELS.get(mc, mineral)
            sz    = int(7 + 8 * conf)   # 7–15 based on confidence

        # Sphere
        traces.append(go.Scatter3d(
            x=[cx], y=[cy], z=[-depth],
            mode='markers',
            marker=dict(size=sz, color=color, symbol='circle',
                        line=dict(color='white', width=1)),
            name=label,
            showlegend=False,
            hovertemplate=(
                f'<b>{label}</b><br>'
                f'Grid ({row},{col})<br>'
                f'Depth: {depth:.2f} m<br>'
                f'Confidence: {conf*100:.0f}%'
                '<extra></extra>'
            )
        ))

        # Vertical dotted line surface→deposit
        line_color = color.replace('0.85', '0.35').replace(
                           '0.92', '0.35').replace('0.90', '0.35')
        traces.append(go.Scatter3d(
            x=[cx, cx], y=[cy, cy], z=[0.01, -depth],
            mode='lines',
            line=dict(color=line_color, width=1, dash='dot'),
            showlegend=False, hoverinfo='skip'
        ))

    return traces


# ── Scan Trail ────────────────────────────────────────────────────────────────

def _scan_trail_traces(scanned, current_row, current_col):
    """Green dotted path showing rover's traversal history."""
    if not scanned:
        return []
    # Build ordered list of visited cells
    cells = sorted(scanned.keys(), key=lambda rc: list(scanned.keys()).index(rc))
    xs = [c + 0.5 for _, c in cells] + [current_col + 0.5]
    ys = [r + 0.5 for r, _ in cells] + [current_row + 0.5]
    zs = [0.04] * len(xs)
    return [go.Scatter3d(
        x=xs, y=ys, z=zs,
        mode='lines',
        line=dict(color='rgba(0,255,136,0.35)', width=2, dash='dot'),
        showlegend=False,
        hovertemplate='Rover path<extra></extra>'
    )]


# ── PSR Overlay ───────────────────────────────────────────────────────────────

def _psr_surface():
    psr_x = np.linspace(0.3, 2.7, 30)
    psr_y = np.linspace(3.3, 5.7, 30)
    PX, PY = np.meshgrid(psr_x, psr_y)
    PZ = np.full_like(PX, -0.22)
    return go.Surface(
        x=PX, y=PY, z=PZ,
        colorscale=[[0, 'rgba(0,0,100,0.30)'], [1, 'rgba(0,30,150,0.30)']],
        showscale=False, opacity=0.28,
        name='Permanently Shadowed Region',
        hovertemplate='PSR — Potential Ice Zone<extra></extra>'
    )


# ── Survey Grid Lines ─────────────────────────────────────────────────────────

def _grid_line_traces():
    traces = []
    for i in range(7):
        v = float(i)
        for xs, ys in [([0, 6], [v, v]), ([v, v], [0, 6])]:
            traces.append(go.Scatter3d(
                x=xs, y=ys, z=[0.02, 0.02],
                mode='lines',
                line=dict(color='rgba(100,180,255,0.20)', width=1),
                showlegend=False, hoverinfo='skip'
            ))
    return traces


# ── Next-cell preview ─────────────────────────────────────────────────────────

def _next_cell_trace(scan_index, scan_order):
    """Yellow pulsing ring showing the next cell to be scanned."""
    if scan_index >= len(scan_order):
        return []
    nr, nc = scan_order[scan_index]
    cx, cy = nc + 0.5, nr + 0.5
    theta = np.linspace(0, 2 * np.pi, 30)
    return [go.Scatter3d(
        x=cx + 0.42 * np.cos(theta),
        y=cy + 0.42 * np.sin(theta),
        z=np.full(30, 0.03),
        mode='lines',
        line=dict(color='rgba(255,230,0,0.55)', width=2),
        showlegend=False,
        hovertemplate=f'<b>Next Scan Target</b><br>Grid ({nr},{nc})<extra></extra>'
    )]


# ── Legend dummy traces ───────────────────────────────────────────────────────

def _legend_traces():
    items = [
        ('Water Ice',         '#29B6F6'),
        ('Ilmenite',          '#FFA000'),
        ('Pyroxene',          '#66BB6A'),
        ('Regolith',          '#787882'),
        ('⛔ Obstacle (L0)',  '#DC3232'),
        ('⚡ Low Power (L1)', '#FFAA00'),
        ('🔬 GPR Beam (L2)',  '#FFD54F'),
    ]
    traces = []
    for name, color in items:
        traces.append(go.Scatter3d(
            x=[None], y=[None], z=[None],
            mode='markers',
            marker=dict(size=8, color=color),
            name=name, showlegend=True
        ))
    return traces


# ── Decision Annotation Box ───────────────────────────────────────────────────

def _decision_annotation(l0_ok, l1_ok, l2_active,
                         battery_pct, temperature,
                         obstacle_score=None):
    """
    Build a text annotation string showing current L0/L1/L2 decision state.
    Returned as a Plotly layout annotation dict.
    """
    l0_txt = '✅ L0 SAFE' if l0_ok else '⛔ L0 BLOCKED'
    l1_txt = '✅ L1 OK'   if l1_ok else f'⚡ L1 LOW ({battery_pct:.0f}%)'
    l2_txt = '🔬 L2 SCANNING' if l2_active else '💤 L2 STANDBY'

    if not l0_ok and obstacle_score is not None:
        l0_txt += f' (score {obstacle_score:.2f})'

    lines = [
        '<b style="color:#8AB4F8">AI DECISION PIPELINE</b>',
        f'<span style="color:{"#00FF88" if l0_ok else "#FF4444"}">{l0_txt}</span>',
        f'<span style="color:{"#00FF88" if l1_ok else "#FFAA00"}">{l1_txt}</span>',
        f'<span style="color:{"#00BFFF" if l2_active else "#556677"}">{l2_txt}</span>',
        f'<span style="color:#7ab3d4">🌡 {temperature:.1f}°C  🔋 {battery_pct:.0f}%</span>',
    ]
    return dict(
        text='<br>'.join(lines),
        align='left',
        showarrow=False,
        xref='paper', yref='paper',
        x=0.01, y=0.22,
        bordercolor='#3A3A5A',
        borderwidth=1,
        borderpad=6,
        bgcolor='rgba(13,13,26,0.85)',
        font=dict(size=11, color='white', family='monospace'),
    )


# ── Main Builder ──────────────────────────────────────────────────────────────

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
    Build the full interactive 3D figure showing the L0/L1/L2 pipeline.

    Parameters
    ----------
    scan_log     : list of dicts — completed scan history
    system_state : SystemState object (or None for defaults)
    show_gpr_beam: bool — True when L2 just ran a scan
    current_row / current_col : rover grid position
    scan_index   : next cell index in scan_order
    scan_order   : list of (row,col) tuples
    last_l0      : dict from l0_safety_check() or None
    last_l1      : dict from l1_resource_check() or None

    Returns
    -------
    plotly.graph_objects.Figure
    """
    # Backward compatibility for older callers that still use legacy names.
    if 'row' in legacy_kwargs and 'current_row' not in legacy_kwargs:
        current_row = legacy_kwargs.pop('row')
    if 'col' in legacy_kwargs and 'current_col' not in legacy_kwargs:
        current_col = legacy_kwargs.pop('col')
    if 'system_state' in legacy_kwargs and system_state is None:
        system_state = legacy_kwargs.pop('system_state')

    # Ignore any additional legacy keywords rather than raising a TypeError.

    if scan_log is None:
        scan_log = []
    if scan_order is None:
        scan_order = [(r, c) for r in range(6) for c in range(6)]

    scanned = {(d['row'], d['col']): d for d in scan_log}

    # Extract system state
    battery_pct = system_state.battery     if system_state else BATTERY_CAPACITY
    temperature = system_state.temperature if system_state else NOMINAL_TEMP_C

    # L0/L1 status
    l0_ok    = last_l0['safe']     if last_l0 else True
    l1_ok    = last_l1['can_scan'] if last_l1 else True
    l2_active = show_gpr_beam

    obs_score = last_l0.get('obstacle_score') if last_l0 else None

    # ── Terrain ───────────────────────────────────────────────────────────
    X, Y, Z_raw = _generate_lunar_terrain(grid_size=72, seed=7)

    terrain = go.Surface(
        x=X, y=Y, z=Z_raw,
        colorscale=[
            [0.0,  '#1A1A2E'], [0.25, '#2D2D3E'],
            [0.5,  '#4A4A5A'], [0.75, '#6B6B7A'],
            [1.0,  '#9B9BAA'],
        ],
        showscale=False, opacity=1.0,
        lighting=dict(ambient=0.5, diffuse=0.7,
                      roughness=0.5, specular=0.2),
        lightposition=dict(x=2, y=5, z=10),
        name='Lunar Surface',
        hovertemplate='Lunar South Pole<extra></extra>',
    )

    # ── PSR ───────────────────────────────────────────────────────────────
    psr = _psr_surface()

    # ── Grid lines ────────────────────────────────────────────────────────
    grid_traces = _grid_line_traces()

    # ── Obstacle warnings (all known obstacle cells, even unscanned) ──────
    obstacle_traces = []
    for row in range(6):
        for col in range(6):
            if GRID[row][col] == 'OB':
                obstacle_traces += _obstacle_warning_traces(row, col)

    # ── Scan trail ────────────────────────────────────────────────────────
    trail_traces = _scan_trail_traces(scanned, current_row, current_col)

    # ── Next-cell preview ─────────────────────────────────────────────────
    next_traces = _next_cell_trace(scan_index, scan_order)

    # ── Mineral deposits (L2 results) ─────────────────────────────────────
    deposit_traces = _deposit_traces(scanned)

    # ── Rover with L1 battery/thermal indicators ──────────────────────────
    rz = _surface_z_at(current_row, current_col, Z_raw) + 0.04
    rover_traces = _rover_traces(
        rx=current_col + 0.5,
        ry=current_row + 0.5,
        rz=rz,
        battery_pct=battery_pct,
        temperature=temperature,
        l0_ok=l0_ok,
        l1_ok=l1_ok,
    )

    # ── L0 camera FOV ─────────────────────────────────────────────────────
    fov_traces = _l0_fov_traces(
        rx=current_col + 0.5,
        ry=current_row + 0.5,
        rz=rz,
        heading_deg=0,
    )

    # ── GPR beam (L2 only) ────────────────────────────────────────────────
    beam_traces = []
    if show_gpr_beam:
        mc = GRID[current_row][current_col]
        depth = MINERAL_DEPTHS.get(mc, 1.0)
        beam_traces = _gpr_beam_traces(
            rx=current_col + 0.5,
            ry=current_row + 0.5,
            rz=rz,
            depth=depth,
        )

    # ── Legend ────────────────────────────────────────────────────────────
    legend_traces = _legend_traces()

    # ── Assemble ──────────────────────────────────────────────────────────
    all_traces = (
        [terrain, psr]
        + grid_traces
        + obstacle_traces
        + trail_traces
        + next_traces
        + deposit_traces
        + rover_traces
        + fov_traces
        + beam_traces
        + legend_traces
    )

    fig = go.Figure(data=all_traces)

    # ── Decision annotation ────────────────────────────────────────────────
    ann = _decision_annotation(
        l0_ok, l1_ok, l2_active,
        battery_pct, temperature, obs_score
    )

    n_scanned  = len([d for d in scan_log if d.get('status') == 'scanned'])
    n_obstacle = len([d for d in scan_log if d.get('status') == 'obstacle'])
    n_lp       = len([d for d in scan_log if d.get('status') == 'low_power'])

    fig.update_layout(
        paper_bgcolor='#0D0D1A',
        annotations=[ann],
        scene=dict(
            xaxis=dict(
                title=dict(text='East → (km)', font=dict(color='#8AB4F8')),
                range=[0, 6],
                backgroundcolor='#0D0D1A', gridcolor='#2A2A40',
                showbackground=True, zerolinecolor='#2A2A40',
                tickfont=dict(color='#8AB4F8'),
            ),
            yaxis=dict(
                title=dict(text='North → (km)', font=dict(color='#8AB4F8')),
                range=[0, 6],
                backgroundcolor='#0D0D1A', gridcolor='#2A2A40',
                showbackground=True, zerolinecolor='#2A2A40',
                tickfont=dict(color='#8AB4F8'),
            ),
            zaxis=dict(
                title=dict(text='Depth / Elevation (m)',
                           font=dict(color='#8AB4F8')),
                range=[-1.6, 0.9],
                backgroundcolor='#0A0A18', gridcolor='#2A2A40',
                showbackground=True, zerolinecolor='#4A4A6A',
                tickfont=dict(color='#8AB4F8'),
            ),
            camera=dict(
                eye=dict(x=1.6, y=-1.8, z=1.2),
                up=dict(x=0, y=0, z=1),
            ),
            bgcolor='#0D0D1A',
            aspectmode='manual',
            aspectratio=dict(x=1.5, y=1.5, z=0.6),
        ),
        legend=dict(
            font=dict(color='white', size=11),
            bgcolor='rgba(20,20,40,0.85)',
            bordercolor='#3A3A5A', borderwidth=1,
            x=0.76, y=0.98,
        ),
        margin=dict(l=0, r=0, t=36, b=0),
        height=570,
        title=dict(
            text=(
                '<b>L-MINER 3D</b>  |  '
                f'Rover @ ({current_row},{current_col})  |  '
                f'Scanned: {n_scanned}  '
                f'Obstacles: {n_obstacle}  '
                f'Low-Power: {n_lp}'
            ),
            font=dict(color='#8AB4F8', size=13),
            x=0.5, xanchor='center', y=0.99,
        ),
    )

    return fig


# ── Standalone test ────────────────────────────────────────────────────────────

if __name__ == '__main__':

    class _FakeState:
        battery = 62.0
        temperature = 33.5

    fake_log = [
        {'row': 0, 'col': 0, 'mineral': 'Wi', 'confidence': 0.88,
         'depth_m': 1.20, 'status': 'scanned'},
        {'row': 0, 'col': 1, 'mineral': 'Re', 'confidence': 0.75,
         'depth_m': 0.50, 'status': 'scanned'},
        {'row': 0, 'col': 2, 'mineral': 'Il', 'confidence': 0.82,
         'depth_m': 0.80, 'status': 'scanned'},
        {'row': 0, 'col': 3, 'mineral': 'Py', 'confidence': 0.79,
         'depth_m': 1.00, 'status': 'scanned'},
        {'row': 1, 'col': 0, 'mineral': 'Re', 'confidence': 0.60,
         'depth_m': 0.50, 'status': 'low_power'},
        {'row': 1, 'col': 3, 'mineral': 'Wi', 'confidence': 0.91,
         'depth_m': 1.20, 'status': 'scanned'},
        {'row': 2, 'col': 2, 'mineral': 'Wi', 'confidence': 0.85,
         'depth_m': 1.20, 'status': 'scanned'},
    ]

    fake_l0 = {'safe': True,     'obstacle_score': 0.12, 'status': 'SAFE'}
    fake_l1 = {'can_scan': True, 'reason': 'OK'}

    print("Building 3D figure with L0/L1/L2 visualisation...")
    fig = build_3d_figure(
        scan_log=fake_log,
        system_state=_FakeState(),
        show_gpr_beam=True,
        current_row=2, current_col=3,
        scan_index=9,
        scan_order=[(r, c) for r in range(6) for c in range(6)],
        last_l0=fake_l0,
        last_l1=fake_l1,
    )

    out = '3d_test.html'
    fig.write_html(out, include_plotlyjs='cdn')
    print(f"✅  Saved → {out}")
