"""
L-MINER Mission Dashboard — dashboard.py
Autonomous Lunar South Pole Mineral Detection & ISRU Prospecting System
Designed for IST Islamabad — ISSSP 2026

Run command:
    python -m streamlit run dashboard.py
"""

import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib
matplotlib.use('Agg')
import inspect
import textwrap
import time
import sys
import os

# Ensure local workspace is on import path
sys.path.insert(0, os.path.dirname(__file__))

from data_generator import (
    scan_cell,
    generate_spectrometer_data,
    MINERAL_NAMES,
    MINERAL_COLORS,
    MINERAL_MAP,
    OBSTACLE_MAP,
    DEPTH_MAP,
    GRID_SIZE,
)
from model import load_model, predict_mineral
from l0_l1_logic import (
    SystemState,
    process_cell,
    recharge,
    LOW_POWER_THRESHOLD,
    BATTERY_CAPACITY,
    MAX_TEMP_C,
    NOMINAL_TEMP_C,
)
from visualization_3d import build_3d_figure

# ─────────────────────────────────────────────
# PAGE CONFIGURATION
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="L-MINER | Lunar Polar Mineral Survey",
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────
# PREMIUM AEROSPACE HUD STYLING (CSS)
# ─────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700;800&family=Space+Grotesk:wght@400;600;700;800&display=swap');

    /* Global theme */
    .stApp {
        background: radial-gradient(circle at 50% 0%, #0c1527 0%, #030712 65%, #010409 100%);
        color: #e2e8f0;
        font-family: 'Space Grotesk', -apple-system, sans-serif;
    }

    /* Aerospace HUD Header */
    .hud-header {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.90) 0%, rgba(30, 41, 59, 0.70) 50%, rgba(15, 23, 42, 0.90) 100%);
        border: 1px solid rgba(0, 229, 255, 0.25);
        box-shadow: 0 4px 24px -1px rgba(0, 229, 255, 0.12), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        border-radius: 14px;
        padding: 16px 28px;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
    }

    .hud-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: 3px;
        margin: 0;
        background: linear-gradient(90deg, #00E5FF 0%, #FFFFFF 50%, #80D8FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 30px rgba(0, 229, 255, 0.4);
    }

    .hud-subtitle {
        color: #94a3b8;
        font-size: 0.82rem;
        letter-spacing: 2px;
        font-family: 'JetBrains Mono', monospace;
        margin-top: 3px;
    }

    .hud-badge-container {
        display: flex;
        gap: 10px;
        align-items: center;
    }

    .hud-chip {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.74rem;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 700;
        letter-spacing: 1px;
    }

    .chip-active {
        background: rgba(0, 229, 255, 0.12);
        color: #00E5FF;
        border: 1px solid rgba(0, 229, 255, 0.4);
    }

    .chip-telemetry {
        background: rgba(0, 230, 118, 0.12);
        color: #00E676;
        border: 1px solid rgba(0, 230, 118, 0.4);
    }

    /* Status Cards */
    .status-card {
        background: rgba(15, 23, 42, 0.75);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(51, 65, 85, 0.8);
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 12px;
        transition: transform 0.15s ease, border-color 0.15s ease;
    }

    .status-card:hover {
        border-color: rgba(0, 229, 255, 0.35);
        box-shadow: 0 4px 16px rgba(0, 229, 255, 0.08);
    }

    .card-safe   { border-left: 4px solid #00E676; }
    .card-warn   { border-left: 4px solid #FFD600; }
    .card-danger { border-left: 4px solid #FF1744; }
    .card-info   { border-left: 4px solid #00E5FF; }

    /* Section Labels */
    .section-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        letter-spacing: 2.5px;
        color: #38bdf8;
        text-transform: uppercase;
        margin-bottom: 10px;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* Mineral Result Card */
    .mineral-result-box {
        background: linear-gradient(145deg, rgba(15, 23, 42, 0.95), rgba(8, 14, 28, 0.95));
        border: 1px solid rgba(56, 189, 248, 0.3);
        border-radius: 12px;
        padding: 18px;
        margin-top: 12px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
    }

    .mineral-name-text {
        font-size: 1.8rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: 1px;
    }

    .mineral-sub-text {
        color: #94a3b8;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        margin-top: 6px;
    }

    /* Mission Log Window */
    .terminal-log {
        background: #020617;
        border: 1px solid rgba(30, 41, 59, 0.9);
        border-radius: 10px;
        padding: 12px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        max-height: 220px;
        overflow-y: auto;
    }

    .log-entry {
        padding: 4px 0;
        border-bottom: 1px solid rgba(30, 41, 59, 0.4);
        display: flex;
        align-items: baseline;
        gap: 8px;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
        color: #ffffff !important;
        border: 1px solid #38bdf8 !important;
        border-radius: 8px !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: 1px !important;
        padding: 8px 16px !important;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.25) !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%) !important;
        border-color: #7dd3fc !important;
        box-shadow: 0 4px 20px rgba(14, 165, 233, 0.45) !important;
        transform: translateY(-1px);
    }

    /* 3D Panel Container */
    .viz3d-panel {
        background: rgba(3, 7, 18, 0.95);
        border: 1px solid rgba(0, 229, 255, 0.3);
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 20px;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.6);
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SESSION STATE INITIALIZATION
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
        st.session_state.results = {}
        st.session_state.current_cell = None
        st.session_state.current_scan_data = None
        st.session_state.last_l0 = None
        st.session_state.last_l1 = None
        st.session_state.demo_complete = False
        st.session_state.recharging = False
        st.session_state.log_messages = []
        st.session_state.show_3d = False
        st.session_state.mission_start_time = time.time()


def reset_demo():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_session()
    st.rerun()


init_session()


# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def render_html(html_str, target=st):
    """
    Safely render HTML without Markdown interpreting indented lines as code blocks.
    Strips leading whitespace from every line so CommonMark never triggers <pre><code>.
    """
    cleaned = "\n".join(line.lstrip() for line in html_str.splitlines()).strip()
    target.markdown(cleaned, unsafe_allow_html=True)


def add_log(msg):
    timestamp = time.strftime("%H:%M:%S")
    st.session_state.log_messages.insert(0, f"[{timestamp}] {msg}")
    if len(st.session_state.log_messages) > 30:
        st.session_state.log_messages.pop()


def get_mineral_hex(name):
    name_map = {
        "Water Ice": "#00E5FF",
        "Ilmenite": "#FF9100",
        "Pyroxene": "#00E676",
        "Regolith": "#9EACBA",
        "Obstacle": "#FF1744",
        "Skipped": "#FFD600",
    }
    return name_map.get(name, "#9EACBA")


def build_scan_log_for_3d():
    """Build accurate scan history for visualization_3d.py."""
    code_map = {
        "Water Ice": "Wi",
        "Ilmenite": "Il",
        "Pyroxene": "Py",
        "Regolith": "Re",
        "Obstacle": "OB",
        "Skipped": "LP",
    }
    log = []
    for (row, col), r in st.session_state.results.items():
        name = r.get("mineral_name", "Regolith")
        status = "obstacle" if name == "Obstacle" else \
                 "low_power" if name == "Skipped" else "scanned"
        log.append({
            "row": row,
            "col": col,
            "mineral": code_map.get(name, "Re"),
            "confidence": r.get("confidence", 0.0),
            "depth_m": r.get("depth_m", float(DEPTH_MAP[row, col])),
            "status": status,
        })
    return log


# ─────────────────────────────────────────────
# HIGH-FIDELITY SURVEY GRID VISUALIZER
# ─────────────────────────────────────────────

def render_mineral_map():
    """
    Render high-tech 6x6 lunar survey grid:
      - Coordinate system (East Traversal / North Traversal)
      - Visual classification glyphs & confidence metrics
      - Breadcrumb traversal trail connecting surveyed locations
      - Obstacle warning beacons and live rover reticle
    """
    fig = go.Figure()
    current = st.session_state.current_cell

    # 1. Survey cell rectangles & annotations
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            key = (row, col)
            is_current = (current and current == key)

            if key in st.session_state.results:
                r = st.session_state.results[key]
                name = r.get("mineral_name", "Unknown")
                color = get_mineral_hex(name)

                if name == "Obstacle":
                    cell_text = "⛔<br><b style='font-size:8px;color:#FF1744'>HAZARD</b>"
                    cell_fill = "rgba(255, 23, 68, 0.22)"
                    cell_border = "#FF1744"
                elif name == "Skipped":
                    cell_text = "⚡<br><b style='font-size:8px;color:#FFD600'>PAUSED</b>"
                    cell_fill = "rgba(255, 214, 0, 0.18)"
                    cell_border = "#FFD600"
                else:
                    short = {"Water Ice": "H₂O ICE", "Ilmenite": "ILM", "Pyroxene": "PYR", "Regolith": "REG"}.get(name, name[:3])
                    conf = r.get("confidence", 0.0)
                    depth = r.get("depth_m", float(DEPTH_MAP[row, col]))
                    cell_text = f"<b style='font-size:10px;color:{color}'>{short}</b><br><span style='font-size:8px;color:#cbd5e1'>{conf*100:.0f}% · {depth:.1f}m</span>"
                    cell_fill = f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.25)"
                    cell_border = color
            elif is_current:
                cell_text = "🛸<br><b style='font-size:9px;color:#FFD600'>SCANNING</b>"
                cell_fill = "rgba(255, 214, 0, 0.22)"
                cell_border = "#FFD600"
            else:
                cell_text = f"<span style='color:#475569;font-size:9px'>{row},{col}</span>"
                cell_fill = "rgba(15, 23, 42, 0.45)"
                cell_border = "rgba(51, 65, 85, 0.50)"

            if is_current:
                cell_border = "#FFD600"
                border_width = 2.5
            else:
                border_width = 1.0

            fig.add_shape(
                type="rect",
                x0=col - 0.46, y0=row - 0.46,
                x1=col + 0.46, y1=row + 0.46,
                fillcolor=cell_fill,
                line=dict(color=cell_border, width=border_width),
            )

            fig.add_annotation(
                x=col, y=row,
                text=cell_text,
                showarrow=False,
                font=dict(size=9, color="white", family="JetBrains Mono"),
                align="center",
            )

    # 2. Rover Traversal Path Trail
    if st.session_state.results:
        path_cells = list(st.session_state.results.keys())
        px = [c for _, c in path_cells]
        py = [r for r, _ in path_cells]
        if current and current not in path_cells:
            px.append(current[1])
            py.append(current[0])

        fig.add_trace(go.Scatter(
            x=px, y=py,
            mode='lines',
            line=dict(color='rgba(0, 230, 118, 0.35)', width=2, dash='dot'),
            showlegend=False,
            hoverinfo='skip',
        ))

    fig.update_layout(
        xaxis=dict(
            title=dict(text="East Traversal (Grid Columns 0–5)", font=dict(color="#94a3b8", size=10)),
            showgrid=False, zeroline=False,
            tickvals=list(range(GRID_SIZE)),
            ticktext=[f"E-{i}" for i in range(GRID_SIZE)],
            tickfont=dict(color="#64748b", size=9, family="JetBrains Mono"),
            range=[-0.65, GRID_SIZE - 0.35],
        ),
        yaxis=dict(
            title=dict(text="North Traversal (Grid Rows 0–5)", font=dict(color="#94a3b8", size=10)),
            showgrid=False, zeroline=False,
            tickvals=list(range(GRID_SIZE)),
            ticktext=[f"N-{i}" for i in range(GRID_SIZE)],
            tickfont=dict(color="#64748b", size=9, family="JetBrains Mono"),
            range=[-0.65, GRID_SIZE - 0.35],
            autorange="reversed",
            scaleanchor="x",
        ),
        plot_bgcolor="rgba(3, 7, 18, 0.7)",
        paper_bgcolor="rgba(0, 0, 0, 0)",
        margin=dict(l=45, r=10, t=10, b=45),
        height=330,
    )

    return fig


# ─────────────────────────────────────────────
# HIGH-FIDELITY SENSOR PLOTS
# ─────────────────────────────────────────────

def render_gpr_plot(bscan, depth_m):
    """
    Render GPR B-scan paired with an A-scan Energy Trace:
      - 2D subsurface radar profile (depth vs traverse distance)
      - Dielectric boundary reflector line at true depth
      - A-scan energy profile showing dielectric reflection amplitude spike
    """
    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[0.78, 0.22],
        subplot_titles=("GPR B-Scan (Depth vs Traverse)", "A-Scan Energy Profile"),
        horizontal_spacing=0.08
    )

    n_depth, n_distance = bscan.shape
    dist_axis = np.linspace(0, 5.0, n_distance)
    depth_axis = np.linspace(0, 3.0, n_depth)

    # 1. B-scan Heatmap
    fig.add_trace(
        go.Heatmap(
            z=bscan,
            x=dist_axis,
            y=depth_axis,
            colorscale="icefire",
            zmin=-1, zmax=1,
            showscale=False,
            hovertemplate="Distance: %{x:.2f} m<br>Depth: %{y:.2f} m<br>Amplitude: %{z:.2f}<extra></extra>"
        ),
        row=1, col=1
    )

    # Subsurface Reflector Horizon
    fig.add_hline(
        y=depth_m,
        line=dict(color="#FFD600", width=2, dash="dash"),
        annotation_text=f"Reflector Horizon: {depth_m:.2f} m",
        annotation_font=dict(color="#FFD600", size=10, family="JetBrains Mono"),
        row=1, col=1
    )

    # 2. A-scan Energy Profile (Mean power across depth)
    a_scan_energy = np.mean(bscan**2, axis=1)
    a_scan_norm = a_scan_energy / (np.max(a_scan_energy) + 1e-8)

    fig.add_trace(
        go.Scatter(
            x=a_scan_norm,
            y=depth_axis,
            mode='lines',
            line=dict(color='#00E5FF', width=2),
            fill='tozerox',
            fillcolor='rgba(0, 229, 255, 0.15)',
            hovertemplate="Normalized Energy: %{x:.2f}<br>Depth: %{y:.2f} m<extra></extra>"
        ),
        row=1, col=2
    )

    fig.add_hline(
        y=depth_m,
        line=dict(color="#FFD600", width=1.5, dash="dot"),
        row=1, col=2
    )

    fig.update_xaxes(title_text="Traverse Distance (m)", color="#94a3b8", tickfont=dict(size=8, family="JetBrains Mono"), row=1, col=1)
    fig.update_yaxes(title_text="Depth (m)", color="#94a3b8", autorange="reversed", tickfont=dict(size=8, family="JetBrains Mono"), row=1, col=1)
    fig.update_xaxes(title_text="Energy (Norm)", color="#94a3b8", tickfont=dict(size=8, family="JetBrains Mono"), row=1, col=2)
    fig.update_yaxes(autorange="reversed", showticklabels=False, row=1, col=2)

    fig.update_layout(
        plot_bgcolor="#050B18",
        paper_bgcolor="#0A1124",
        margin=dict(l=45, r=15, t=30, b=40),
        height=220,
        showlegend=False,
        font=dict(color="#e2e8f0", size=9, family="Space Grotesk"),
    )

    return fig


def render_spectrometer_plot(wavelengths, reflectance, mineral_name, mineral_id=0):
    """
    Render Measured Reflectance curve overlaid with USGS Laboratory Benchmark:
      - Measured noisy reflectance curve from rover spectrometer
      - USGS Reference Benchmark curve (dashed) for scientific verification
      - Diagnostic absorption band markers (1.0um, 1.25um, 1.50um, 2.00um)
    """
    fig = go.Figure()
    color = get_mineral_hex(mineral_name)

    # 1. Measured Rover Reflectance
    fig.add_trace(go.Scatter(
        x=wavelengths,
        y=reflectance,
        mode='lines',
        line=dict(color=color, width=2.5),
        fill='tozeroy',
        fillcolor=f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.15)",
        name=f"Rover Scan: {mineral_name}",
        hovertemplate="Wavelength: %{x:.2f} μm<br>Reflectance: %{y:.3f}<extra></extra>"
    ))

    # 2. Laboratory USGS Spectral Library Reference Benchmark
    clean_wl, clean_refl = generate_spectrometer_data(mineral_id, noise_level=0.0)
    fig.add_trace(go.Scatter(
        x=clean_wl,
        y=clean_refl,
        mode='lines',
        line=dict(color='rgba(255, 255, 255, 0.65)', width=1.5, dash='dash'),
        name=f"USGS Laboratory Ref",
        hovertemplate="USGS Reference: %{y:.3f}<extra></extra>"
    ))

    # 3. Diagnostic Absorption Band Highlights
    if mineral_name == "Water Ice":
        for band, label in [(1.25, "1.25μm"), (1.50, "1.50μm H₂O"), (2.00, "2.00μm H₂O")]:
            fig.add_vline(
                x=band,
                line=dict(color="#00E5FF", width=1.5, dash="dot"),
                annotation_text=label,
                annotation_font=dict(color="#00E5FF", size=9, family="JetBrains Mono"),
                annotation_position="top left",
            )
    elif mineral_name == "Pyroxene":
        for band, label in [(1.00, "1.00μm Band I"), (2.00, "2.00μm Band II")]:
            fig.add_vline(
                x=band,
                line=dict(color="#00E676", width=1.5, dash="dot"),
                annotation_text=label,
                annotation_font=dict(color="#00E676", size=9, family="JetBrains Mono"),
                annotation_position="top left",
            )
    elif mineral_name == "Ilmenite":
        fig.add_hline(
            y=0.07,
            line=dict(color="#FF9100", width=1.2, dash="dot"),
            annotation_text="Flat Dark Basalt Baseline (FeTiO₃)",
            annotation_font=dict(color="#FF9100", size=9, family="JetBrains Mono"),
            annotation_position="top right",
        )

    fig.update_layout(
        xaxis=dict(
            title="Wavelength λ (μm)",
            color="#94a3b8",
            tickfont=dict(color="#94a3b8", size=9, family="JetBrains Mono"),
            range=[0.48, 2.52],
        ),
        yaxis=dict(
            title="Reflectance",
            color="#94a3b8",
            tickfont=dict(color="#94a3b8", size=9, family="JetBrains Mono"),
            range=[0.0, 1.0],
        ),
        plot_bgcolor="#050B18",
        paper_bgcolor="#0A1124",
        margin=dict(l=45, r=15, t=25, b=40),
        height=220,
        legend=dict(
            font=dict(color="#cbd5e1", size=9, family="JetBrains Mono"),
            bgcolor="rgba(15, 23, 42, 0.75)",
            bordercolor="rgba(56, 189, 248, 0.2)",
            x=0.02, y=0.98,
        ),
    )

    return fig


# ─────────────────────────────────────────────
# SCAN STEP CONTROLLER
# ─────────────────────────────────────────────

def do_scan():
    """Execute single autonomous survey step."""
    state = st.session_state.system
    idx = st.session_state.scan_index
    scan_order = st.session_state.scan_order

    if idx >= len(scan_order):
        st.session_state.demo_complete = True
        return

    row, col = scan_order[idx]
    st.session_state.current_cell = (row, col)
    st.session_state.scan_index += 1

    # Run L0 Safety + L1 Resource Check
    decision = process_cell(row, col, state)
    st.session_state.last_l0 = decision["l0"]
    st.session_state.last_l1 = decision["l1"]

    if not decision["proceed_to_l2"]:
        reason = decision["skip_reason"]
        if decision["l0"] and not decision["l0"]["safe"]:
            st.session_state.results[(row, col)] = {
                "mineral_name": "Obstacle",
                "mineral_id": -1,
                "confidence": 0.0,
                "depth_m": 0.0,
                "row": row, "col": col,
                "skipped": True,
                "skip_reason": reason,
            }
            add_log(f"⛔ ({row},{col}) L0 HAZARD DETECTED — Obstacle score {decision['l0']['obstacle_score']:.2f} > 0.75. Cell bypassed.")
        else:
            st.session_state.results[(row, col)] = {
                "mineral_name": "Skipped",
                "mineral_id": -2,
                "confidence": 0.0,
                "depth_m": 0.0,
                "row": row, "col": col,
                "skipped": True,
                "skip_reason": reason,
            }
            st.session_state.recharging = True
            add_log(f"⚡ ({row},{col}) L1 POWER PAUSE — Battery at {state.battery:.1f}%. Science instruments locked.")
        st.session_state.current_scan_data = None
        return

    # L2 Science Layer Active
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
        f"🔬 ({row},{col}) L2 SCI SCAN: {result['mineral_name']} "
        f"| Conf: {result['confidence_pct']} | Depth: {result['depth_m']}m"
    )


# ─────────────────────────────────────────────
# MAIN DASHBOARD UI
# ─────────────────────────────────────────────

# ── HUD Top Header ──
total_cells = GRID_SIZE * GRID_SIZE
visited_count = len(st.session_state.results)
scanned_count = len([r for r in st.session_state.results.values() if not r.get("skipped")])

render_html(f"""
<div class="hud-header">
    <div>
        <p class="hud-title">⬡ L-MINER Mk-II</p>
        <p class="hud-subtitle">
            AUTONOMOUS LUNAR POLAR SURVEY ROVER &nbsp;|&nbsp;
            IST ISLAMABAD — ISSSP 2026
        </p>
    </div>
    <div class="hud-badge-container">
        <span class="hud-chip chip-active">STATUS: {"COMPLETE" if st.session_state.demo_complete else "ACTIVE SURVEY"}</span>
        <span class="hud-chip chip-telemetry">COVERAGE: {visited_count}/{total_cells} CELLS ({(visited_count/total_cells)*100:.0f}%)</span>
    </div>
</div>
""")

# ── 3D Digital Twin Viewer Toggle ──
toggle_col1, toggle_col2 = st.columns([5, 1.2])
with toggle_col2:
    btn_3d_text = "🌑 Hide 3D Digital Twin" if st.session_state.show_3d else "🌑 View 3D Digital Twin"
    if st.button(btn_3d_text, key="toggle_3d_btn"):
        st.session_state.show_3d = not st.session_state.show_3d
        st.rerun()

# ── 3D Digital Twin Modal Panel ──
if st.session_state.show_3d:
    st.markdown('<div class="viz3d-panel">', unsafe_allow_html=True)
    st.markdown(
        '<p style="color:#00E5FF;font-family:\'JetBrains Mono\';font-size:0.75rem;letter-spacing:2px;margin:0 0 6px 0">'
        '🌑 INTERACTIVE 3D DIGITAL TWIN · LUNAR SOUTH POLE TOPOGRAPHY</p>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<p style="color:#94a3b8;font-size:0.8rem;margin:0 0 12px 0">'
        '🖱️ <b>Rotate:</b> Left-Click Drag &nbsp;·&nbsp; '
        '<b>Zoom:</b> Scroll &nbsp;·&nbsp; '
        '<b>Pan:</b> Right-Click Drag &nbsp;·&nbsp; '
        '<b>Colored Spheres:</b> Classified deposits at true subsurface depths</p>',
        unsafe_allow_html=True
    )

    pos = st.session_state.current_cell
    cur_r = pos[0] if pos else 0
    cur_c = pos[1] if pos else 0

    fig_3d = build_3d_figure(
        scan_log=build_scan_log_for_3d(),
        system_state=st.session_state.system,
        show_gpr_beam=(st.session_state.current_scan_data is not None),
        current_row=cur_r,
        current_col=cur_c,
        scan_index=st.session_state.scan_index,
        scan_order=st.session_state.scan_order,
        last_l0=st.session_state.last_l0,
        last_l1=st.session_state.last_l1,
    )

    st.plotly_chart(
        fig_3d,
        use_container_width=True,
        config={"displayModeBar": True, "displaylogo": False},
        key="main_3d_scene"
    )

    # Context Explanations
    c1, c2, c3 = st.columns(3)
    render_html("""
    <div class="status-card card-safe" style="font-size:0.78rem">
        <b style="color:#00E676">L0 SAFETY SUBSYSTEM</b><br>
        <span style="color:#94a3b8">
        Green camera FOV frustum scans upcoming terrain. Red hazard pillars designate
        inaccessible impact slopes and boulders. Protects rover mobility.
        </span>
    </div>
    """, target=c1)
    render_html("""
    <div class="status-card card-warn" style="font-size:0.78rem">
        <b style="color:#FFD600">L1 RESOURCE MANAGER</b><br>
        <span style="color:#94a3b8">
        Vertical 3D pillar monitors power reserves. Mast tip changes color with internal
        electronics thermal load. Safeguards mission lifespan.
        </span>
    </div>
    """, target=c2)
    render_html("""
    <div class="status-card card-info" style="font-size:0.78rem">
        <b style="color:#00E5FF">L2 SCIENCE INSTRUMENTS</b><br>
        <span style="color:#94a3b8">
        Golden radar cone executes subsurface sounding. Subsurface spheres display
        identified minerals at exact depth with confidence-scaled volume.
        </span>
    </div>
    """, target=c3)

    st.markdown('</div>', unsafe_allow_html=True)

# ── Primary 3-Column Layout ──
col_telemetry, col_sensors, col_mapping = st.columns([1.1, 1.6, 1.3])

state = st.session_state.system

# ─────────────────────────────────────────────
# COLUMN 1: ROVER STATUS & TELEMETRY
# ─────────────────────────────────────────────
with col_telemetry:
    st.markdown('<p class="section-label">🛸 ROVER TELEMETRY</p>', unsafe_allow_html=True)

    # Position & Metrics
    pos = st.session_state.current_cell
    pos_str = f"({pos[0]}, {pos[1]})" if pos else "STANDBY"
    m1, m2 = st.columns(2)
    m1.metric("Current Coordinates", pos_str)
    m2.metric("Science Scans", f"{scanned_count}/{total_cells}")

    # Battery Meter
    batt = state.battery
    batt_color = "#00E676" if batt > 50 else ("#FFD600" if batt > LOW_POWER_THRESHOLD else "#FF1744")
    batt_card_class = "card-danger" if batt < LOW_POWER_THRESHOLD else "card-safe"

    render_html(f"""
    <div class="status-card {batt_card_class}">
        <div style="display:flex;justify-content:space-between;align-items:center">
            <span style="font-size:0.75rem;color:#94a3b8;font-family:'JetBrains Mono'">POWER RESERVES</span>
            <span style="font-size:1.4rem;font-weight:800;color:{batt_color};font-family:'JetBrains Mono'">{batt:.1f}%</span>
        </div>
        <div style="background:#1e293b;border-radius:6px;height:8px;margin-top:8px;overflow:hidden">
            <div style="background:{batt_color};width:{batt}%;height:8px;border-radius:6px;transition:width 0.3s"></div>
        </div>
    </div>
    """)

    # Thermal Sensor
    temp = state.temperature
    temp_color = "#00E5FF" if temp < 35 else ("#FFD600" if temp < 45 else "#FF1744")
    render_html(f"""
    <div class="status-card card-info">
        <div style="display:flex;justify-content:space-between;align-items:center">
            <span style="font-size:0.75rem;color:#94a3b8;font-family:'JetBrains Mono'">AVIONICS TEMP</span>
            <span style="font-size:1.3rem;font-weight:700;color:{temp_color};font-family:'JetBrains Mono'">{temp:.1f}°C</span>
        </div>
        <div style="font-size:0.7rem;color:#64748b;margin-top:4px">Nominal: 28°C &nbsp;·&nbsp; Limit: {MAX_TEMP_C:.0f}°C</div>
    </div>
    """)

    # Autonomy Hierarchy
    st.markdown('<p class="section-label" style="margin-top:14px">🧠 AUTONOMY PIPELINE</p>', unsafe_allow_html=True)

    l0 = st.session_state.last_l0
    l1 = st.session_state.last_l1

    l0_ok = l0["safe"] if l0 else True
    l1_ok = l1["can_scan"] if l1 else True
    l2_active = (st.session_state.current_scan_data is not None)

    layers = [
        ("L0", "SURFACE SAFETY", l0_ok, "CLEAR" if l0_ok else "HAZARD BLOCKED", "card-safe" if l0_ok else "card-danger"),
        ("L1", "POWER & THERMAL", l1_ok, "NOMINAL" if l1_ok else "POWER PAUSE", "card-safe" if l1_ok else "card-warn"),
        ("L2", "NEURAL ML SOUNDING", l2_active, "SOUNDING" if l2_active else "STANDBY", "card-info" if l2_active else "status-card"),
    ]

    for code, title, ok, status_str, card_cls in layers:
        icon = "✅" if ok else ("⛔" if code == "L0" else "⚡")
        render_html(f"""
        <div class="status-card {card_cls}" style="padding:10px 14px;margin-bottom:8px">
            <div style="display:flex;justify-content:space-between;align-items:center">
                <div>
                    <span style="font-family:'JetBrains Mono';font-weight:700;color:#38bdf8;font-size:0.8rem">[{code}]</span>
                    <span style="font-size:0.75rem;color:#cbd5e1;margin-left:6px">{title}</span>
                </div>
                <span style="font-family:'JetBrains Mono';font-size:0.72rem;font-weight:700">{icon} {status_str}</span>
            </div>
        </div>
        """)

    # Recharge button if low power
    if st.session_state.recharging:
        st.warning("⚡ Power Reserves Depleted — Solar Recharge Required")
        if st.button("☀️ Deploy Solar Panels (Recharge +25%)"):
            recharge(st.session_state.system)
            st.session_state.recharging = False
            add_log("☀️ Solar arrays deployed — Battery recharged, electronics cooled.")
            st.rerun()

    # Aggregate Mission Stats
    st.markdown('<p class="section-label" style="margin-top:14px">📊 MISSION STATS</p>', unsafe_allow_html=True)
    render_html(f"""
    <div class="status-card status-card" style="font-family:'JetBrains Mono';font-size:0.76rem;line-height:1.9">
        Total Scans Run: <b style="color:#f8fafc">{state.total_scans}</b><br>
        Hazards Bypassed: <b style="color:#FF1744">{state.obstacles_detected}</b><br>
        Low-Power Holds: <b style="color:#FFD600">{state.low_power_events}</b><br>
        Recharge Cycles: <b style="color:#00E5FF">{state.recharge_cycles}</b>
    </div>
    """)


# ─────────────────────────────────────────────
# COLUMN 2: LIVE SENSOR FEEDS & CLASSIFICATION
# ─────────────────────────────────────────────
with col_sensors:
    st.markdown('<p class="section-label">📡 LIVE INSTRUMENT TELEMETRY</p>', unsafe_allow_html=True)

    scan_data = st.session_state.current_scan_data

    if scan_data:
        # GPR Display
        st.markdown(
            '<div style="display:flex;justify-content:space-between;align-items:center">'
            '<span style="font-size:0.82rem;font-weight:700;color:#e2e8f0">GROUND PENETRATING RADAR (GPR)</span>'
            '<span style="font-size:0.72rem;color:#38bdf8;font-family:\'JetBrains Mono\'">BAND: 500 MHz · DEPTH: 0–3 m</span>'
            '</div>',
            unsafe_allow_html=True
        )
        gpr_fig = render_gpr_plot(scan_data["bscan"], scan_data["depth_m"])
        st.plotly_chart(gpr_fig, use_container_width=True, config={"displayModeBar": False})

        # Spectrometer Display
        st.markdown(
            '<div style="display:flex;justify-content:space-between;align-items:center;margin-top:6px">'
            '<span style="font-size:0.82rem;font-weight:700;color:#e2e8f0">REFLECTANCE SPECTROMETER (VIS / NIR / SWIR)</span>'
            '<span style="font-size:0.72rem;color:#38bdf8;font-family:\'JetBrains Mono\'">0.5 – 2.5 μm (200 CHANNELS)</span>'
            '</div>',
            unsafe_allow_html=True
        )
        spec_fig = render_spectrometer_plot(
            scan_data["wavelengths"],
            scan_data["reflectance"],
            scan_data["mineral_name"],
            scan_data["mineral_id"],
        )
        st.plotly_chart(spec_fig, use_container_width=True, config={"displayModeBar": False})

        # AI Prediction Badge
        mineral = scan_data["mineral_name"]
        conf_pct = scan_data["confidence_pct"]
        depth = scan_data["depth_m"]
        uncertainty = scan_data["uncertainty"]
        mcolor = get_mineral_hex(mineral)

        # Multiclass probability distribution bars
        prob_items = []
        for mname, prob in scan_data["all_probs"].items():
            pcolor = get_mineral_hex(mname)
            w_px = max(2, int(prob * 60))
            prob_items.append(
                f'<div style="text-align:center;min-width:70px;display:inline-block;margin:0 4px;">'
                f'<div style="font-size:0.68rem;color:#94a3b8;font-family:\'JetBrains Mono\';">{mname}</div>'
                f'<div style="font-size:0.92rem;font-weight:800;color:{pcolor};font-family:\'JetBrains Mono\';">{prob*100:.0f}%</div>'
                f'<div style="background:#1e293b;border-radius:3px;height:4px;margin-top:3px;width:60px;margin-left:auto;margin-right:auto;">'
                f'<div style="background:{pcolor};width:{w_px}px;height:4px;border-radius:3px;"></div>'
                f'</div>'
                f'</div>'
            )
        prob_html = "".join(prob_items)

        card_html = (
            f'<div class="mineral-result-box" style="border-color:{mcolor}60;">'
            f'<div style="font-family:\'JetBrains Mono\';font-size:0.72rem;letter-spacing:2px;color:#94a3b8;">L2 CLASSIFIER DETECTION</div>'
            f'<p class="mineral-name-text" style="color:{mcolor};">{mineral.upper()}</p>'
            f'<div class="mineral-sub-text">'
            f'Confidence: <b style="color:white;">{conf_pct}</b> &nbsp;|&nbsp; '
            f'Estimated Depth: <b style="color:white;">{depth:.2f} m</b> &nbsp;|&nbsp; '
            f'Uncertainty: <b style="color:#cbd5e1;">{uncertainty:.2f}</b>'
            f'</div>'
            f'<div style="display:flex;justify-content:center;gap:12px;margin-top:12px;flex-wrap:wrap;">'
            f'{prob_html}'
            f'</div>'
            f'</div>'
        )
        render_html(card_html)

    else:
        render_html("""
        <div style="background:rgba(15, 23, 42, 0.6);border:1px dashed #334155;border-radius:12px;padding:65px 20px;text-align:center;margin:15px 0">
            <div style="font-size:3rem">📡</div>
            <div style="font-family:'Space Grotesk';font-size:1.1rem;font-weight:700;color:#94a3b8;letter-spacing:2px;margin-top:8px">
                INSTRUMENT TELEMETRY STANDBY
            </div>
            <div style="font-size:0.8rem;color:#64748b;margin-top:6px">
                Click <b>▶ Scan Next Cell</b> or <b>⏩ Auto-Survey</b> to engage GPR and Spectrometer.
            </div>
        </div>
        """)

    # Mission Log Terminal
    st.markdown('<p class="section-label" style="margin-top:14px">📋 FLIGHT TERMINAL LOG</p>', unsafe_allow_html=True)
    log_content = ""
    for msg in st.session_state.log_messages[:6]:
        log_content += f'<div class="log-entry"><span style="color:#38bdf8">»</span> <span>{msg}</span></div>'
    if not log_content:
        log_content = '<div style="color:#64748b">Awaiting survey initiation...</div>'
    render_html(f'<div class="terminal-log">{log_content}</div>')


# ─────────────────────────────────────────────
# COLUMN 3: MINERAL MAP & ISRU SUMMARY
# ─────────────────────────────────────────────
with col_mapping:
    st.markdown('<p class="section-label">🗺️ LUNAR SURVEY GRID</p>', unsafe_allow_html=True)

    grid_fig = render_mineral_map()
    st.plotly_chart(grid_fig, use_container_width=True, config={"displayModeBar": False})

    # ISRU Resource Assessment
    if st.session_state.results:
        counts = {"Water Ice": 0, "Ilmenite": 0, "Pyroxene": 0, "Regolith": 0, "Obstacle": 0}
        for r in st.session_state.results.values():
            mname = r.get("mineral_name", "")
            if mname in counts:
                counts[mname] += 1

        st.markdown('<p class="section-label" style="margin-top:12px">💎 RESOURCE DISTRIBUTION</p>', unsafe_allow_html=True)

        for name, count in counts.items():
            if count == 0 and name != "Water Ice":
                continue
            color = get_mineral_hex(name)
            pct = (count / total_cells) * 100
            render_html(f"""
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">
                <span style="color:{color};font-size:0.8rem;font-weight:700;min-width:85px;font-family:'JetBrains Mono'">{name}</span>
                <div style="flex:1;background:#1e293b;border-radius:4px;height:6px">
                    <div style="background:{color};width:{pct*2.8}px;max-width:100%;height:6px;border-radius:4px"></div>
                </div>
                <span style="color:#cbd5e1;font-size:0.8rem;font-family:'JetBrains Mono';min-width:24px;text-align:right">{count}</span>
            </div>
            """)

        # ISRU Potential Box
        ice_cells = [
            (r["row"], r["col"])
            for r in st.session_state.results.values()
            if r.get("mineral_name") == "Water Ice"
        ]
        if ice_cells:
            # 10m x 10m cell area, average 1.0m layer, 1500 kg/m^3 regolith, 5.5 wt% ice
            est_water_mass_tonnes = len(ice_cells) * (10.0 * 10.0 * 1.0 * 1.5 * 0.055)

            render_html(f"""
            <div style="background:rgba(0, 229, 255, 0.08);border:1px solid #00E5FF;border-radius:10px;padding:12px;margin-top:10px;text-align:center">
                <div style="color:#00E5FF;font-family:'JetBrains Mono';font-size:0.72rem;font-weight:700;letter-spacing:2px">ISRU VOLATILE EXTRACTION ZONE</div>
                <div style="color:#ffffff;font-size:1.1rem;font-weight:800;margin-top:3px">
                    {len(ice_cells)} Water Ice Deposits Confirmed
                </div>
                <div style="color:#94a3b8;font-size:0.75rem;margin-top:4px">
                    Est. Water Potential: <b style="color:#00E676">~{est_water_mass_tonnes:.1f} Tonnes H₂O</b><br>
                    Recommended for In-Situ Propellant Production (LOX/LH₂)
                </div>
            </div>
            """)

    # Mission Controls
    st.markdown('<p class="section-label" style="margin-top:14px">🎮 MISSION CONTROLS</p>', unsafe_allow_html=True)

    remaining_steps = total_cells - st.session_state.scan_index
    demo_done = st.session_state.demo_complete

    if not demo_done and remaining_steps > 0:
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if st.button("▶ Scan Next", disabled=st.session_state.recharging):
                do_scan()
                st.rerun()
        with c_btn2:
            if st.button("⏩ Auto-Survey"):
                while st.session_state.scan_index < total_cells and not st.session_state.recharging:
                    do_scan()
                    if st.session_state.recharging:
                        break
                if st.session_state.scan_index >= total_cells:
                    st.session_state.demo_complete = True
                st.rerun()
    else:
        if demo_done:
            st.success("✅ Lunar South Pole Survey Complete! All 36 cells mapped.")
        if st.button("🔄 Reset Mission"):
            reset_demo()
