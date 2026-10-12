# 🌙 L-MINER Mk-II: Autonomous Lunar South Pole Mineral Detection & ISRU Prospecting Payload System

> **Built for ISSSP 2026 (Track 3: Lunar Surface Robotics & Autonomous Systems)**  
> **Institution:** Department of Space Science & Aeronautics, Institute of Space Technology (IST), Islamabad  
> **Faculty Advisor:** Dr. Sajid Ghuffar, Institute of Space Technology  
> **Team Roster:** Led by **Haider Taqveen**, with **Hajra**, **Abdul Wasay**, **Saad**, **Mohsin**, and **Adan**  
> • **Haider Taqveen** — Physical Sensor Modeling & GPR/Spectrometer Payload Lead  
> • **Abdul Wasay** — Machine Learning & Edge Mineral Classifier Lead  
> • **Saad** — Payload Autonomy (L0 Safety Reflex & L1 Resource Management) Lead  
> • **Hajra** — Human-Machine Interface, Streamlit HUD & Communications Specialist  

---

## 🏆 Finals Scoring Rules (Track 3) & Competition Deliverables

All official deliverables for **Table 6: Finals Scoring Rules of Track 3 (100 Points Total)** are compiled and available in the [`Finals_Track3_Deliverables/`](./Finals_Track3_Deliverables/) directory:

| Item | Criteria | Points | Deliverable Word Document | Deliverable PDF Document |
| :---: | :--- | :---: | :--- | :--- |
| **1** | **Community Building** (Until 31st Oct) | **10** | [`1_Community_Building_Guide.docx`](./Finals_Track3_Deliverables/1_Community_Building_Guide.docx) | [`1_Community_Building_Guide.pdf`](./Finals_Track3_Deliverables/1_Community_Building_Guide.pdf) |
| **2** | **Poster Blueprint** (Until 31st Oct) | **10** | [`2_Poster_Specification_and_Blueprint.docx`](./Finals_Track3_Deliverables/2_Poster_Specification_and_Blueprint.docx) | [`2_Poster_Specification_and_Blueprint.pdf`](./Finals_Track3_Deliverables/2_Poster_Specification_and_Blueprint.pdf) |
| **3 & 4** | **Topic Selection (10 Pts) & Research Program (30 Pts)** | **40** | [`3_Technical_Research_Paper_and_Program.docx`](./Finals_Track3_Deliverables/3_Technical_Research_Paper_and_Program.docx) | [`3_Technical_Research_Paper_and_Program.pdf`](./Finals_Track3_Deliverables/3_Technical_Research_Paper_and_Program.pdf) |
| **5, 6 & 7**| **Work Display (25 Pts), PPT Pitch (10 Pts) & Artistry (5 Pts)** | **40** | [`4_Presentation_Script_and_Simulation_Guide.docx`](./Finals_Track3_Deliverables/4_Presentation_Script_and_Simulation_Guide.docx) | [`4_Presentation_Script_and_Simulation_Guide.pdf`](./Finals_Track3_Deliverables/4_Presentation_Script_and_Simulation_Guide.pdf) |
| **TOTAL** | **Comprehensive Finals Package** | **100** | *4 Complete Word Documents* | *4 Publication-Grade PDFs* |

---

## 🛰️ System Architecture

L-MINER Mk-II operates on a **3-tier decoupled hierarchical autonomy pipeline**:

```
                       ┌────────────────────────────────────────────────────────┐
                       │          L0: SAFETY REFLEX (10 Hz Execution)           │
                       │   HazCam stereo obstacle scoring (H >= 0.75 halt)     │
                       └──────────────────────────┬─────────────────────────────┘
                                                  │ Safe
                                                  ▼
                       ┌────────────────────────────────────────────────────────┐
                       │        L1: RESOURCE & THERMAL MANAGER (1 Hz)           │
                       │   Battery SoC (<30% recharge) & Avionics Temp (<50°C) │
                       └──────────────────────────┬─────────────────────────────┘
                                                  │ Nominal
                                                  ▼
                       ┌────────────────────────────────────────────────────────┐
                       │           L2: COGNITIVE SCIENCE PROSPECTING            │
                       │   500 MHz GPR (0-3m) + 0.5-2.5 μm VNIR-SWIR Spectrometer│
                       │   10-D Feature Extraction (3,300x Compression)         │
                       │   Edge Random Forest Inference (<15 ms, 95.8% Acc)     │
                       └────────────────────────────────────────────────────────┘
```

1. **L0 Reflex Layer (`l0_l1_logic.py`):** Real-time collision avoidance. Halts traversal if obstacle slope $>15^\circ$ or hazard score $\ge 0.75$.
2. **L1 Resource Manager (`l0_l1_logic.py`):** Tracks battery State-of-Charge and electronics temperature. Autonomously commands solar array deployment when power reserves drop below $30\%$.
3. **L2 Science Prospecting (`data_generator.py` & `model.py`):**
   - **500 MHz UHF Ground Penetrating Radar:** Synthesizes $128 \times 256$ B-scan dielectric stratigraphy profiles down to $3.0\text{ m}$.
   - **0.5–2.5 μm VNIR-SWIR Spectrometer:** Actively illuminated reflectance spectroscopy calibrated against Apollo 11/12 samples and USGS splib07 standards.
   - **10-D Feature Extraction:** Compresses 32,968 raw floating-point numbers into 10 scalar features ($3,300\times$ edge data reduction).
   - **Random Forest Classifier:** Classifies Water Ice, Ilmenite, Pyroxene, and Regolith with **95.8% accuracy** in **$<15\text{ ms}$**.

---

## 🚀 Quickstart: Running the Mission Dashboard

### 1. Requirements
Ensure Python 3.9+ is installed with the required scientific packages:
```bash
pip install streamlit plotly numpy scikit-learn matplotlib python-docx reportlab pymupdf
```

### 2. Launch the Interactive Mission HUD
```bash
python -m streamlit run dashboard.py
```
Open your browser to **`http://localhost:8501`** to interact with:
- Live GPR B-scan paired with A-scan energy trace.
- VNIR-SWIR reflectance curves with USGS benchmark overlays.
- Real-time L0/L1 autonomy telemetry.
- 3D interactive lunar polar digital twin with subterranean deposits.

---

## 📂 Repository File Structure

```
├── Finals_Track3_Deliverables/          # Official Competition Finals Package (Word & PDF)
│   ├── 1_Community_Building_Guide.docx  # Item 1: Social campaign, playbook, team charter
│   ├── 1_Community_Building_Guide.pdf
│   ├── 2_Poster_Specification_and_Blueprint.docx # Item 2: A0 Poster print copy & wireframe
│   ├── 2_Poster_Specification_and_Blueprint.pdf
│   ├── 3_Technical_Research_Paper_and_Program.docx # Items 3 & 4: Research paper (40 Pts)
│   ├── 3_Technical_Research_Paper_and_Program.pdf
│   ├── 4_Presentation_Script_and_Simulation_Guide.docx # Items 5, 6 & 7: Demo & 14-slide script
│   └── 4_Presentation_Script_and_Simulation_Guide.pdf
├── 3d_test.html                         # Standalone WebGL 3D Lunar Digital Twin (~718 KB)
├── dashboard.py                         # Streamlit Mission Control HUD & Telemetry Interface
├── data_generator.py                    # Physical GPR & Spectrometer Sensor Modeling
├── l0_l1_logic.py                       # Hierarchical Autonomy (Safety reflex & power management)
├── model.py                             # Random Forest Classifier & Feature Pipeline
├── visualization_3d.py                  # High-density 96x96 Lunar Terrain & 3D Rover Builder
├── lminer_model.pkl                     # Serialized Random Forest Model
├── lminer_scaler.pkl                    # Feature Standard Scaler
├── generate_doc1.py                     # Generator script for Deliverable 1
├── generate_doc2.py                     # Generator script for Deliverable 2
├── generate_doc3.py                     # Generator script for Deliverable 3
└── generate_doc4.py                     # Generator script for Deliverable 4
```

---

## 📜 Citations & Planetary References
- **Chandrayaan-1 $M^3$:** Pieters, C. M., et al. (Science 2009). Character and Spatial Distribution of OH/$H_2O$ on the Moon.
- **USGS Spectral Library:** Clark, R. N., et al. (2007). USGS Digital Spectral Library splib07a.
- **Chang'e-3/4 LPR:** Fang, G., et al. (2014). Lunar Penetrating Radar: System and Preliminary Results.
- **Perseverance RIMFAX:** Hamran, S. E., et al. (2020). Radar Imager for Mars' Subsurface Experiment.
