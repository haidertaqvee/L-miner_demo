"""
L-MINER Mission Dashboard
file — the visual demo judges see.

Run with: python -m streamlit run dashboard.py
"""

import streamlit as st
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import inspect
import textwrap
import time
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from data_generator import (
    scan_cell, MINERAL_NAMES, MINERAL_COLORS,
    MINERAL_MAP, OBSTACLE_MAP, GRID_SIZE,
    plot_gpr_bscan, plot_spectrometer
)
from model import load_model, predict_mineral
from l0_l1_logic import (
    SystemState, process_cell, recharge,
    LOW_POWER_THRESHOLD, BATTERY_CAPACITY
)
from visualization_3d import build_3d_figure

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="L-MINER | Lunar Mineral Detection",
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────
# CUSTOM CSS — Space theme
# ─────────────────────────────────────────────

st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #050a14;
        color: #e0e8f0;
    }

    /* Header */
    .lminer-header {
        background: linear-gradient(135deg, #0d1b2a 0%, #1a3a5c 50%, #0d1b2a 100%);
        border: 1px solid #1e5080;
        border-radius: 12px;
        padding: 18px 28px;
        margin-bottom: 20px;
        text-align: center;
    }
    .lminer-title {
        font-size: 2.4rem;
        font-weight: 800;
        letter-spacing: 4px;
        background: linear-gradient(90deg, #00bfff, #ffffff, #00bfff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .lminer-subtitle {
        color: #7ab3d4;
        font-size: 0.9rem;
        letter-spacing: 2px;
        margin-top: 4px;
    }

    /* Status cards */
    .status-card {
        background: #0d1b2a;
        border: 1px solid #1e3a5a;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }
    .status-safe   { border-left: 4px solid #00ff88; }
    .status-warn   { border-left: 4px solid #ffaa00; }
    .status-danger { border-left: 4px solid #ff4444; }
    .status-idle   { border-left: 4px solid #4488aa; }

    /* Layer labels */
    .layer-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 1px;
        margin-right: 6px;
    }
    .l0-badge { background: #003322; color: #00ff88; border: 1px solid #00ff88; }
    .l1-badge { background: #332200; color: #ffaa00; border: 1px solid #ffaa00; }
    .l2-badge { background: #001133; color: #00bfff; border: 1px solid #00bfff; }

    /* Mineral result box */
    .mineral-result {
        background: #0a1628;
        border-radius: 10px;
        padding: 16px;
        margin-top: 10px;
        border: 1px solid #1e4060;
        text-align: center;
    }
    .mineral-name {
        font-size: 1.6rem;
        font-weight: 800;
        margin: 0;
    }
    .mineral-meta {
        color: #7ab3d4;
        font-size: 0.85rem;
        margin-top: 6px;
    }

    /* Section headers */
    .section-label {
        font-size: 0.7rem;
        letter-spacing: 3px;
        color: #4a7a9b;
        text-transform: uppercase;
        margin-bottom: 8px;
        font-weight: 600;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #1a4a7a, #0d2a4a);
        color: #00bfff;
        border: 1px solid #00bfff;
        border-radius: 8px;
        font-weight: 700;
        letter-spacing: 1px;
        padding: 10px 24px;
        width: 100%;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #0d2a4a, #1a4a7a);
        border-color: #00ffff;
        color: #00ffff;
    }

    /* 3D button — distinct gold accent */
    .btn-3d > button {
        background: linear-gradient(135deg, #2a1a00, #4a3000) !important;
        color: #FFD700 !important;
        border: 1px solid #FFD700 !important;
    }
    .btn-3d > button:hover {
        background: linear-gradient(135deg, #4a3000, #2a1a00) !important;
        border-color: #FFEE55 !important;
        color: #FFEE55 !important;
    }

    /* 3D modal overlay */
    .viz3d-panel {
        background: #060c18;
        border: 1px solid #1e4060;
        border-radius: 14px;
        padding: 16px;
        margin-top: 12px;
    }

    /* Hide streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Metric overrides */
    [data-testid="metric-container"] {
        background: #0d1b2a;
        border: 1px solid #1e3a5a;
        border-radius: 8px;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────

def init_session():
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        st.session_state.system = SystemState()
        st.session_state.model, st.session_state.scaler = load_model()
        st.session_state.scan_order = [
            (r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE)
        ]
        st.session_state.scan_index = 0
        st.session_state.results = {}       # (row,col) -> result dict
        st.session_state.current_cell = None
        st.session_state.current_scan_data = None
        st.session_state.last_l0 = None
        st.session_state.last_l1 = None
        st.session_state.demo_complete = False
        st.session_state.recharging = False
        st.session_state.log_messages = []
        st.session_state.show_3d = False    # 3D panel toggle


def reset_demo():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_session()
    st.rerun()


init_session()


# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def add_log(msg):
    st.session_state.log_messages.insert(0, msg)
    if len(st.session_state.log_messages) > 20:
        st.session_state.log_messages.pop()


def get_battery_color(pct):
    if pct > 50:
        return "#00ff88"
    elif pct > 20:
        return "#ffaa00"
    else:
        return "#ff4444"


def get_mineral_color(name):
    name_to_id = {
        "Water Ice": 1, "Ilmenite": 2,
        "Pyroxene": 3, "Regolith": 0
    }
    mid = name_to_id.get(name, 0)
    return MINERAL_COLORS.get(mid, "#888888")


# ─────────────────────────────────────────────
# BUILD 3D SCAN LOG
# Convert session results → format visualization_3d expects
# ─────────────────────────────────────────────

def build_scan_log_for_3d():
    """Convert dashboard's results dict into the scan_log list
    that build_3d_figure() expects."""
    name_to_code = {
        "Water Ice": "Wi",
        "Ilmenite":  "Il",
        "Pyroxene":  "Py",
        "Regolith":  "Re",
        "Obstacle":  "OB",
        "Skipped":   "Re",
    }
    log = []
    for (row, col), r in st.session_state.results.items():
        mineral_name = r.get("mineral_name", "Regolith")
        code   = name_to_code.get(mineral_name, "Re")
        status = "obstacle" if mineral_name == "Obstacle" else \
                 "low_power" if mineral_name == "Skipped" else "scanned"
        log.append({
            "row":        row,
            "col":        col,
            "mineral":    code,
            "confidence": r.get("confidence", 0.0),
            "depth_m":    r.get("depth_m", 0.5),
            "status":     status,
        })
    return log


def build_3d_figure_compat(scan_log, system_state, show_gpr_beam,
                           current_row, current_col, scan_index,
                           scan_order, last_l0, last_l1):
    """Call the 3D builder with backward-compatible argument handling."""
    sig = inspect.signature(build_3d_figure)
    params = sig.parameters

    call_kwargs = {}
    if 'scan_log' in params:
        call_kwargs['scan_log'] = scan_log
    if 'system_state' in params:
        call_kwargs['system_state'] = system_state
    if 'show_gpr_beam' in params:
        call_kwargs['show_gpr_beam'] = show_gpr_beam

    # Older builds may use row/col, newer builds use current_row/current_col.
    if 'current_row' in params:
        call_kwargs['current_row'] = current_row
    elif 'row' in params:
        call_kwargs['row'] = current_row

    if 'current_col' in params:
        call_kwargs['current_col'] = current_col
    elif 'col' in params:
        call_kwargs['col'] = current_col

    if 'scan_index' in params:
        call_kwargs['scan_index'] = scan_index
    if 'scan_order' in params:
        call_kwargs['scan_order'] = scan_order
    if 'last_l0' in params:
        call_kwargs['last_l0'] = last_l0
    if 'last_l1' in params:
        call_kwargs['last_l1'] = last_l1

    return build_3d_figure(**call_kwargs)


# ─────────────────────────────────────────────
# GRID RENDERER
# ─────────────────────────────────────────────

def render_mineral_map():
    """Render the 6x6 mineral probability map using Plotly."""
    z = np.zeros((GRID_SIZE, GRID_SIZE))
    text = [["" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    colors = [["#1a2a3a" for _ in range(GRID_SIZE)]
               for _ in range(GRID_SIZE)]

    color_map = {
        "Water Ice": "#00BFFF",
        "Ilmenite": "#FF8C00",
        "Pyroxene": "#32CD32",
        "Regolith": "#888888",
        "Obstacle": "#FF4444",
    }

    current = st.session_state.current_cell

    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            key = (row, col)
            if key in st.session_state.results:
                r = st.session_state.results[key]
                name = r.get("mineral_name", "Unknown")
                colors[row][col] = color_map.get(name, "#888888")
                if name == "Obstacle":
                    text[row][col] = "⛔"
                else:
                    short = {
                        "Water Ice": "ICE",
                        "Ilmenite": "ILM",
                        "Pyroxene": "PYR",
                        "Regolith": "REG"
                    }.get(name, name[:3])
                    conf = r.get("confidence", 0)
                    text[row][col] = f"{short}\n{conf*100:.0f}%"
            elif current and current == key:
                colors[row][col] = "#FFD700"
                text[row][col] = "🛸"
            else:
                text[row][col] = f"{row},{col}"

    fig = go.Figure()

    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            key = (row, col)
            is_current = current and current == key
            border_color = "#FFD700" if is_current else "#1e3a5a"
            border_width = 3 if is_current else 1

            fig.add_shape(
                type="rect",
                x0=col - 0.45, y0=row - 0.45,
                x1=col + 0.45, y1=row + 0.45,
                fillcolor=colors[row][col],
                line=dict(color=border_color, width=border_width),
                opacity=0.85
            )

            fig.add_annotation(
                x=col, y=row,
                text=text[row][col],
                showarrow=False,
                font=dict(size=9, color="white", family="monospace"),
                align="center"
            )

    fig.update_layout(
        xaxis=dict(
            showgrid=False, zeroline=False, showticklabels=False,
            range=[-0.6, GRID_SIZE - 0.4]
        ),
        yaxis=dict(
            showgrid=False, zeroline=False, showticklabels=False,
            range=[-0.6, GRID_SIZE - 0.4],
            scaleanchor="x"
        ),
        plot_bgcolor="#050a14",
        paper_bgcolor="#050a14",
        margin=dict(l=10, r=10, t=10, b=10),
        height=320,
    )

    return fig


# ─────────────────────────────────────────────
# SENSOR PLOTS
# ─────────────────────────────────────────────

def render_gpr_plot(bscan, depth_m):
    """Render GPR B-scan using Plotly."""
    fig = go.Figure()
    fig.add_trace(go.Heatmap(
        z=bscan,
        colorscale="RdBu_r",
        zmin=-1, zmax=1,
        showscale=False,
        x=np.linspace(0, 5, bscan.shape[1]),
        y=np.linspace(0, 3, bscan.shape[0]),
    ))
    fig.add_hline(
        y=depth_m,
        line=dict(color="#FFD700", width=2, dash="dash"),
        annotation_text=f"  Layer @ {depth_m}m",
        annotation_font_color="#FFD700",
        annotation_font_size=11
    )
    fig.update_layout(
        xaxis=dict(title="Distance (m)", color="#7ab3d4",
                   tickfont=dict(color="#7ab3d4", size=9)),
        yaxis=dict(title="Depth (m)", color="#7ab3d4",
                   tickfont=dict(color="#7ab3d4", size=9),
                   autorange="reversed"),
        plot_bgcolor="#0a0a1a",
        paper_bgcolor="#0d1b2a",
        margin=dict(l=50, r=10, t=10, b=40),
        height=200,
    )
    return fig


def render_spectrometer_plot(wavelengths, reflectance, mineral_name):
    """Render spectrometer reading using Plotly."""
    color = get_mineral_color(mineral_name)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=wavelengths,
        y=reflectance,
        mode='lines',
        line=dict(color=color, width=2),
        fill='tozeroy',
        fillcolor="rgba(0, 191, 255, 0.15)",
        name=mineral_name
    ))

    # Mark key absorption bands
    bands = {
        "Water Ice": [1.5, 2.0],
        "Pyroxene": [1.0, 2.0]
    }
    if mineral_name in bands:
        for wl in bands[mineral_name]:
            fig.add_vline(
                x=wl,
                line=dict(color="#FFD700", width=1.5, dash="dot"),
                annotation_text=f"{wl}μm",
                annotation_font_color="#FFD700",
                annotation_font_size=9
            )

    fig.update_layout(
        xaxis=dict(title="Wavelength (μm)", color="#7ab3d4",
                   tickfont=dict(color="#7ab3d4", size=9)),
        yaxis=dict(title="Reflectance", color="#7ab3d4",
                   tickfont=dict(color="#7ab3d4", size=9),
                   range=[0, 1]),
        plot_bgcolor="#0a0a1a",
        paper_bgcolor="#0d1b2a",
        margin=dict(l=50, r=10, t=10, b=40),
        height=200,
        showlegend=False
    )
    return fig


# ─────────────────────────────────────────────
# SCAN LOGIC
# ─────────────────────────────────────────────

def do_scan():
    """Execute one scan step."""
    state = st.session_state.system
    idx = st.session_state.scan_index
    scan_order = st.session_state.scan_order

    if idx >= len(scan_order):
        st.session_state.demo_complete = True
        return

    row, col = scan_order[idx]
    st.session_state.current_cell = (row, col)
    st.session_state.scan_index += 1

    # Run L0 + L1
    decision = process_cell(row, col, state)
    st.session_state.last_l0 = decision["l0"]
    st.session_state.last_l1 = decision["l1"]

    if not decision["proceed_to_l2"]:
        reason = decision["skip_reason"]
        if decision["l0"] and not decision["l0"]["safe"]:
            # Obstacle
            st.session_state.results[(row, col)] = {
                "mineral_name": "Obstacle",
                "mineral_id": -1,
                "confidence": 0.0,
                "depth_m": 0.0,
                "row": row, "col": col,
                "skipped": True,
                "skip_reason": reason
            }
            add_log(f"⛔ ({row},{col}) Obstacle detected — L0 blocked")
        else:
            # Low power
            st.session_state.results[(row, col)] = {
                "mineral_name": "Skipped",
                "mineral_id": -2,
                "confidence": 0.0,
                "depth_m": 0.0,
                "row": row, "col": col,
                "skipped": True,
                "skip_reason": reason
            }
            st.session_state.recharging = True
            add_log(f"⚡ ({row},{col}) Low power — L1 paused science")
        st.session_state.current_scan_data = None
        return

    # L2 — Run science scan
    st.session_state.recharging = False
    cell_data = scan_cell(row, col)
    result = predict_mineral(
        cell_data["features"], row, col,
        st.session_state.model,
        st.session_state.scaler
    )
    result["bscan"] = cell_data["bscan"]
    result["wavelengths"] = cell_data["wavelengths"]
    result["reflectance"] = cell_data["reflectance"]
    result["row"] = row
    result["col"] = col
    result["skipped"] = False

    st.session_state.results[(row, col)] = result
    st.session_state.current_scan_data = result

    add_log(
        f"✅ ({row},{col}) {result['mineral_name']} | "
        f"{result['confidence_pct']} | {result['depth_m']}m"
    )


# ─────────────────────────────────────────────
# MAIN LAYOUT
# ─────────────────────────────────────────────

# ── Header ──
st.markdown("""
<div class="lminer-header">
    <p class="lminer-title">⬡ L-MINER</p>
    <p class="lminer-subtitle">
        LUNAR MINERAL DETECTION SYSTEM &nbsp;|&nbsp;
        MOON SOUTH POLE SURVEY &nbsp;|&nbsp;
        IST ISLAMABAD — ISSSP 2026
    </p>
</div>
""", unsafe_allow_html=True)

# ── 3D Toggle Button — top right corner ──
_, btn_col = st.columns([5, 1])
with btn_col:
    btn_label = "🌑 Close 3D" if st.session_state.show_3d else "🌑 3D View"
    st.markdown('<div class="btn-3d">', unsafe_allow_html=True)
    if st.button(btn_label, key="toggle_3d"):
        st.session_state.show_3d = not st.session_state.show_3d
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ── 3D Panel (shown when toggled) ──
if st.session_state.show_3d:
    st.markdown('<div class="viz3d-panel">', unsafe_allow_html=True)

    st.markdown(
        '<p style="color:#FFD700;font-size:0.72rem;letter-spacing:3px;'
        'text-transform:uppercase;margin-bottom:6px">'
        '🌑 3D Terrain Visualization — Lunar South Pole Survey</p>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<p style="color:#4a7a9b;font-size:0.78rem;margin-bottom:10px">'
        '🖱️ <b style="color:#7ab3d4">Drag</b> to rotate &nbsp;·&nbsp; '
        '<b style="color:#7ab3d4">Scroll</b> to zoom &nbsp;·&nbsp; '
        '<b style="color:#7ab3d4">Double-click</b> to reset &nbsp;·&nbsp; '
        'Coloured spheres = detected mineral deposits at subsurface depth</p>',
        unsafe_allow_html=True
    )

    # Pull rover position from current cell
    pos = st.session_state.current_cell
    cur_row = pos[0] if pos else 0
    cur_col = pos[1] if pos else 0

    fig_3d = build_3d_figure_compat(
        scan_log=build_scan_log_for_3d(),
        system_state=st.session_state.system,
        show_gpr_beam=(st.session_state.current_scan_data is not None),
        current_row=cur_row,
        current_col=cur_col,
        scan_index=st.session_state.scan_index,
        scan_order=st.session_state.scan_order,
        last_l0=st.session_state.last_l0,
        last_l1=st.session_state.last_l1,
    )
    st.plotly_chart(fig_3d, use_container_width=True,
                    config={"displayModeBar": True,
                            "modeBarButtonsToRemove": ["toImage"],
                            "displaylogo": False},
                    key="3d_terrain")

    # Context cards below the 3D — explain each AI layer
    c1, c2, c3 = st.columns(3)
    c1.markdown("""
    <div class="status-card status-safe" style="font-size:0.78rem">
        <span class="layer-badge l0-badge">L0</span>
        <b style="color:#00FF88">SAFETY LAYER</b><br>
        <span style="color:#7ab3d4">
        Green fan = stereo camera field-of-view scanning the next cell for
        obstacles. Red pillars = cells L0 has flagged unsafe — rover will
        never enter them. Green halo = all-clear to proceed.
        </span>
    </div>
    """, unsafe_allow_html=True)
    c2.markdown("""
    <div class="status-card status-warn" style="font-size:0.78rem">
        <span class="layer-badge l1-badge">L1</span>
        <b style="color:#FFAA00">RESOURCE MANAGER</b><br>
        <span style="color:#7ab3d4">
        Coloured pillar beside rover = battery level (green→amber→red).
        Glowing sphere on mast = thermal sensor (blue=cool, red=hot).
        Halo turns amber/red when L1 blocks scanning due to low power
        or temperature limits.
        </span>
    </div>
    """, unsafe_allow_html=True)
    c3.markdown("""
    <div class="status-card status-idle" style="font-size:0.78rem">
        <span class="layer-badge l2-badge">L2</span>
        <b style="color:#00BFFF">SCIENCE LAYER</b><br>
        <span style="color:#7ab3d4">
        Gold dotted beam = GPR pulse fired only when L0 + L1 both green.
        Coloured spheres = detected minerals at true subsurface depth.
        Sphere size ∝ confidence. Blue=Ice · Amber=Ilmenite · Green=Pyroxene.
        </span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    st.divider()

# ── Main columns ──
col_left, col_center, col_right = st.columns([1.1, 1.6, 1.3])

state = st.session_state.system

# ────────────────────────
# LEFT — Rover Status
# ────────────────────────
with col_left:
    st.markdown('<p class="section-label">🛸 Rover Status</p>',
                unsafe_allow_html=True)

    # Current position
    pos = st.session_state.current_cell
    pos_str = f"({pos[0]}, {pos[1]})" if pos else "Standby"
    scanned = len([r for r in st.session_state.results.values()
                   if not r.get("skipped")])
    total = GRID_SIZE * GRID_SIZE

    c1, c2 = st.columns(2)
    c1.metric("Position", pos_str)
    c2.metric("Scanned", f"{scanned}/{total}")

    # Battery
    batt = state.battery
    batt_color = get_battery_color(batt)
    st.markdown(f"""
    <div class="status-card {'status-danger' if batt < 20 else 'status-safe'}">
        <span style="font-size:0.75rem;color:#7ab3d4;letter-spacing:2px">
            BATTERY
        </span><br>
        <span style="font-size:1.5rem;font-weight:800;color:{batt_color}">
            {batt:.1f}%
        </span>
        <div style="background:#1a2a3a;border-radius:4px;
                    height:6px;margin-top:6px">
            <div style="background:{batt_color};width:{batt}%;
                        height:6px;border-radius:4px"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Temperature
    temp = state.temperature
    st.markdown(f"""
    <div class="status-card status-idle">
        <span style="font-size:0.75rem;color:#7ab3d4;letter-spacing:2px">
            TEMPERATURE
        </span><br>
        <span style="font-size:1.2rem;font-weight:700;color:#aaccee">
            {temp:.1f}°C
        </span>
    </div>
    """, unsafe_allow_html=True)

    # AI Layer Status
    st.markdown('<p class="section-label" style="margin-top:12px">🧠 AI Hierarchy</p>',
                unsafe_allow_html=True)

    l0 = st.session_state.last_l0
    l1 = st.session_state.last_l1

    l0_status = l0["status"] if l0 else "STANDBY"
    l0_ok = l0["safe"] if l0 else True
    l1_status = l1["status"] if l1 else "STANDBY"
    l1_ok = l1["can_scan"] if l1 else True
    l2_active = (st.session_state.current_scan_data is not None)

    for layer, label, ok, status_txt in [
        ("L0", "SAFETY", l0_ok, l0_status),
        ("L1", "RESOURCES", l1_ok, l1_status),
        ("L2", "SCIENCE", l2_active, "ACTIVE" if l2_active else "STANDBY"),
    ]:
        if layer == "L0":
            icon = "✅" if ok else "⛔"
            card_class = "status-safe" if ok else "status-danger"
        elif layer == "L1":
            icon = "✅" if ok else "⚡"
            card_class = "status-safe" if ok else "status-warn"
        else:
            icon = "🔬" if ok else "💤"
            card_class = "status-safe" if ok else "status-idle"

        st.markdown(f"""
        <div class="status-card {card_class}">
            <span class="layer-badge l{layer.lower()}-badge">{layer}</span>
            <span style="font-size:0.8rem;color:#aaccee">{label}</span>
            <span style="float:right;font-size:1rem">{icon}</span>
        </div>
        """, unsafe_allow_html=True)

    # Recharge button
    if st.session_state.recharging:
        st.warning("⚡ Low Power Mode — Recharge before scanning")
        if st.button("☀️ Recharge"):
            recharge(st.session_state.system)
            st.session_state.recharging = False
            add_log("☀️ Recharged — resuming mission")
            st.rerun()

    # Stats
    st.markdown('<p class="section-label" style="margin-top:12px">📊 Mission Stats</p>',
                unsafe_allow_html=True)
    s = state
    st.markdown(f"""
    <div class="status-card status-idle">
        <div style="font-size:0.8rem;color:#aaccee;line-height:1.8">
            Total Scans: <b style="color:white">{s.total_scans}</b><br>
            Obstacles: <b style="color:#ff6666">{s.obstacles_detected}</b><br>
            Low Power Events: <b style="color:#ffaa00">{s.low_power_events}</b><br>
            Recharge Cycles: <b style="color:#00bfff">{s.recharge_cycles}</b>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ────────────────────────
# CENTER — Sensor Data
# ────────────────────────
with col_center:
    st.markdown('<p class="section-label">📡 Live Sensor Feed</p>',
                unsafe_allow_html=True)

    scan_data = st.session_state.current_scan_data

    if scan_data:
        # GPR
        st.markdown("**Ground Penetrating Radar (GPR)**",
                    unsafe_allow_html=False)
        gpr_fig = render_gpr_plot(
            scan_data["bscan"], scan_data["depth_m"]
        )
        st.plotly_chart(gpr_fig, use_container_width=True,
                        config={"displayModeBar": False})

        # Spectrometer
        st.markdown("**Spectrometer**")
        spec_fig = render_spectrometer_plot(
            scan_data["wavelengths"],
            scan_data["reflectance"],
            scan_data["mineral_name"]
        )
        st.plotly_chart(spec_fig, use_container_width=True,
                        config={"displayModeBar": False})

        # Result card
        mineral = scan_data["mineral_name"]
        conf = scan_data["confidence_pct"]
        depth = scan_data["depth_m"]
        mcolor = get_mineral_color(mineral)

        st.markdown(f"""
        <div class="mineral-result" style="border-color:{mcolor}40">
            <p class="mineral-name" style="color:{mcolor}">{mineral}</p>
            <p class="mineral-meta">
                Confidence: <b style="color:white">{conf}</b> &nbsp;|&nbsp;
                Depth: <b style="color:white">{depth}m</b>
            </p>
            <div style="display:flex;justify-content:center;
                        gap:8px;margin-top:10px;flex-wrap:wrap">
        """, unsafe_allow_html=True)

        # Probability bars for all classes
        prob_html = ""
        for mname, prob in scan_data["all_probs"].items():
            pcolor = get_mineral_color(mname)
            prob_html += f"""
            <div style="text-align:center;min-width:70px">
                <div style="font-size:0.65rem;color:#7ab3d4">{mname}</div>
                <div style="font-size:0.9rem;font-weight:700;
                            color:{pcolor}">{prob*100:.0f}%</div>
                <div style="background:#1a2a3a;border-radius:3px;
                            height:4px;margin-top:3px;width:60px">
                    <div style="background:{pcolor};width:{prob*60}px;
                                height:4px;border-radius:3px"></div>
                </div>
            </div>
            """
        st.markdown(
            f'<div style="display:flex;justify-content:center;gap:12px;margin-top:10px">'
            f'{prob_html}</div></div>',
            unsafe_allow_html=True
        )

    else:
        # Idle state
        st.markdown("""
        <div style="background:#0d1b2a;border:1px dashed #1e3a5a;
                    border-radius:10px;padding:60px;text-align:center;
                    color:#4a7a9b;margin:20px 0">
            <div style="font-size:3rem">📡</div>
            <div style="font-size:1rem;margin-top:10px;letter-spacing:2px">
                AWAITING SCAN
            </div>
            <div style="font-size:0.75rem;margin-top:8px;color:#2a5a7a">
                Press "Scan Next Location" to begin
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Activity Log
    st.markdown('<p class="section-label" style="margin-top:16px">📋 Mission Log</p>',
                unsafe_allow_html=True)
    log_html = ""
    for msg in st.session_state.log_messages[:8]:
        log_html += f'<div style="font-size:0.75rem;color:#7ab3d4;padding:3px 0;border-bottom:1px solid #0d1b2a">{msg}</div>'
    if not log_html:
        log_html = '<div style="font-size:0.75rem;color:#2a5a7a">No activity yet</div>'
    st.markdown(
        f'<div style="background:#0a1628;border-radius:8px;padding:10px">'
        f'{log_html}</div>',
        unsafe_allow_html=True
    )


# ────────────────────────
# RIGHT — Mineral Map
# ────────────────────────
with col_right:
    st.markdown('<p class="section-label">🗺️ Mineral Map</p>',
                unsafe_allow_html=True)

    map_fig = render_mineral_map()
    st.plotly_chart(map_fig, use_container_width=True,
                    config={"displayModeBar": False})

    # Summary (after demo complete)
    if st.session_state.demo_complete or len(st.session_state.results) > 0:
        counts = {"Water Ice": 0, "Ilmenite": 0,
                  "Pyroxene": 0, "Regolith": 0, "Obstacle": 0}
        for r in st.session_state.results.values():
            name = r.get("mineral_name", "")
            if name in counts:
                counts[name] += 1

        st.markdown('<p class="section-label">📊 Survey Summary</p>',
                    unsafe_allow_html=True)
        for name, count in counts.items():
            if count == 0:
                continue
            color = get_mineral_color(name)
            pct = count / total * 100
            st.markdown(textwrap.dedent(f"""
                <div style="display:flex;align-items:center;
                            gap:8px;margin-bottom:5px">
                    <span style="color:{color};font-size:0.8rem;
                                 min-width:80px">{name}</span>
                    <div style="flex:1;background:#1a2a3a;
                                border-radius:3px;height:5px">
                        <div style="background:{color};
                                    width:{pct*3}px;
                                    max-width:100%;height:5px;
                                    border-radius:3px"></div>
                    </div>
                    <span style="color:#7ab3d4;font-size:0.8rem;
                                 min-width:20px">{count}</span>
                </div>
            """), unsafe_allow_html=True)

        if st.session_state.demo_complete:
            ice_cells = [
                (r["row"], r["col"])
                for r in st.session_state.results.values()
                if r.get("mineral_name") == "Water Ice"
            ]
            if ice_cells:
                st.markdown(textwrap.dedent(f"""
                    <div style="background:#001a0d;border:1px solid #00ff88;
                                border-radius:8px;padding:10px;margin-top:8px;
                                text-align:center">
                        <div style="color:#00ff88;font-size:0.75rem;
                                    letter-spacing:2px">EXTRACTION ZONE</div>
                        <div style="color:white;font-size:0.9rem;
                                    font-weight:700;margin-top:4px">
                            {len(ice_cells)} Water Ice Deposits Found
                        </div>
                        <div style="color:#7ab3d4;font-size:0.7rem;margin-top:4px">
                            Recommended for ISRU operations
                        </div>
                    </div>
                """), unsafe_allow_html=True)

    # Control buttons
    st.markdown('<p class="section-label" style="margin-top:16px">🎮 Mission Control</p>',
                unsafe_allow_html=True)

    remaining = GRID_SIZE * GRID_SIZE - st.session_state.scan_index
    demo_done = st.session_state.demo_complete

    if not demo_done and remaining > 0:
        b1, b2 = st.columns(2)
        with b1:
            if st.button("▶ Scan Next", disabled=st.session_state.recharging):
                do_scan()
                st.rerun()
        with b2:
            if st.button("⏩ Auto Run"):
                while (st.session_state.scan_index < GRID_SIZE * GRID_SIZE
                       and not st.session_state.recharging):
                    do_scan()
                    if st.session_state.recharging:
                        break
                if st.session_state.scan_index >= GRID_SIZE * GRID_SIZE:
                    st.session_state.demo_complete = True
                st.rerun()
    else:
        if demo_done:
            st.success("✅ Survey Complete!")
        if st.button("🔄 Reset Demo"):
            reset_demo()
