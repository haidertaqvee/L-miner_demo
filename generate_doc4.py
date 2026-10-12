"""
Generator for Deliverable 4: Presentation Script, Simulation Guide & Artistry
Table 6 Scoring Rules: Item 5 (Work Display/Simulation - 25 Pts), Item 6 (PPT Presentation - 10 Pts), Item 7 (Artistry - 5 Pts)
Total: 40 Points out of 100
Generates both .docx and .pdf files.
"""

import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        if self._pageNumber > 1:
            self.drawString(54, 842 - 36, "L-MINER Mk-II | Presentation Script & Simulation Guide (Track 3)")
            self.drawRightString(595 - 54, 842 - 36, "ISSSP 2026 — Track 3 Finals")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 842 - 42, 595 - 54, 842 - 42)

        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 48, 595 - 54, 48)
        self.drawString(54, 34, "IST Islamabad | Track 3 Finals Scoring Items 5, 6 & 7 (40 Points Total)")
        self.drawRightString(595 - 54, 34, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def set_cell_background(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def add_docx_callout(doc, text, title=None, border_color="00A8E8", bg_color="F0F9FF"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, bg_color)
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
    
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="none"/>'
        f'<w:left w:val="single" w:sz="36" w:space="0" w:color="{border_color}"/>'
        f'<w:bottom w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    if title:
        run_title = p.add_run(f"{title}\n")
        run_title.bold = True
        run_title.font.name = "Segoe UI"
        run_title.font.size = Pt(10)
        run_title.font.color.rgb = RGBColor(11, 37, 69)
    run_text = p.add_run(text)
    run_text.font.name = "Segoe UI"
    run_text.font.size = Pt(9.5)
    run_text.font.color.rgb = RGBColor(30, 41, 59)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


# ─────────────────────────────────────────────────────────────
# BUILD DOCX: DELIVERABLE 4
# ─────────────────────────────────────────────────────────────
def build_doc4_docx(filepath):
    doc = docx.Document()
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.85)
        section.right_margin = Inches(0.85)

    PRIMARY = RGBColor(11, 37, 69)
    SECONDARY = RGBColor(19, 64, 116)
    ACCENT = RGBColor(0, 168, 232)
    DARK_TEXT = RGBColor(30, 41, 59)
    MUTED_TEXT = RGBColor(100, 116, 139)

    footer = doc.sections[0].footer
    f_p = footer.paragraphs[0]
    f_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    f_run = f_p.add_run("L-MINER Mk-II | Presentation & Simulation Guide (Track 3) · IST Islamabad")
    f_run.font.size = Pt(8)
    f_run.font.color.rgb = MUTED_TEXT

    p_meta = doc.add_paragraph()
    r_tag = p_meta.add_run("ISSSP 2026 — TRACK 3 FINALS: ITEMS 5, 6 & 7 (WORK DISPLAY, PPT & ARTISTRY — 40 POINTS)\n")
    r_tag.font.name = "Segoe UI"; r_tag.font.size = Pt(9); r_tag.font.bold = True; r_tag.font.color.rgb = ACCENT

    r_title = p_meta.add_run("Presentation Script, Work Display & Simulation Guide")
    r_title.font.name = "Segoe UI"; r_title.font.size = Pt(21); r_title.font.bold = True; r_title.font.color.rgb = PRIMARY

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_after = Pt(12)
    r_sub = p_sub.add_run(
        "Complete 14-Slide Deck Blueprint, Word-for-Word 10-Minute Presentation Script, "
        "Judge Q&A Defense, Live HUD/3D Demonstration Walkthrough, and Artistry Aesthetics Guide"
    )
    r_sub.font.name = "Segoe UI"; r_sub.font.size = Pt(11); r_sub.font.color.rgb = SECONDARY

    # Meta Table
    tbl_meta = doc.add_table(rows=2, cols=2)
    tbl_meta.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_data = [
        ("Project:", "L-MINER Mk-II Lunar Prospector",
         "Institution:", "Institute of Space Technology (IST), Islamabad"),
        ("Scoring Focus:", "Item 5 (Work Display: 25 Pts) + Item 6 (PPT: 10 Pts) + Item 7 (Artistry: 5 Pts)",
         "Presentation Duration:", "10 Minutes Presentation + 5 Minutes Judge Q&A Defense")
    ]
    for r_idx, (k1, v1, k2, v2) in enumerate(meta_data):
        row = tbl_meta.rows[r_idx]
        c1, c2 = row.cells[0], row.cells[1]
        set_cell_background(c1, "F8FAFC"); set_cell_background(c2, "F8FAFC")
        set_cell_margins(c1, 80, 80, 100, 100); set_cell_margins(c2, 80, 80, 100, 100)
        p1 = c1.paragraphs[0]; r = p1.add_run(f"{k1} "); r.bold = True; r.font.size = Pt(8.5); r.font.color.rgb = PRIMARY
        r2 = p1.add_run(v1); r2.font.size = Pt(8.5); r2.font.color.rgb = DARK_TEXT
        p2 = c2.paragraphs[0]; r = p2.add_run(f"{k2} "); r.bold = True; r.font.size = Pt(8.5); r.font.color.rgb = PRIMARY
        r2 = p2.add_run(v2); r2.font.size = Pt(8.5); r2.font.color.rgb = DARK_TEXT

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # ── Part I: Work Display & Simulation Architecture (25 Pts) ──
    h1 = doc.add_heading("Part I: Work Display & Simulation Architecture (25 Points)", level=1)
    h1.paragraph_format.space_before = Pt(14); h1.paragraph_format.space_after = Pt(6)

    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.add_run(
        "Table 6 awards 25 points for 'Work display / simulation design'. L-MINER fulfills this criterion through a dual-interface cyber-physical environment:\n"
        "1. Interactive Streamlit Mission Control HUD (dashboard.py): A real-time, aerospace telemetry workstation providing live sensor traces, "
        "GPR B-scan and A-scan energy subplots, USGS laboratory reflectance benchmarks, autonomy state badges, and survey controls.\n"
        "2. High-Fidelity 3D WebGL Digital Twin (visualization_3d.py & 3d_test.html): A high-density 96 x 96 lunar polar crater terrain mesh "
        "featuring a detailed 6-wheel rocker-bogie rover mesh (gold MLI chassis, silicon solar deck, HazCam mast, parabolic dish), "
        "dynamic terrain slope adaptation (pitch/roll), underground borehole core columns, and volumetric deposit spheres sized by ML confidence."
    )

    doc.add_heading("Step-by-Step Live Demonstration Walkthrough Script (For Judges)", level=2)
    demo_steps = [
        ("Step 1: System Boot & Standby Status",
         "Launch the Streamlit Mission HUD (http://localhost:8501). Point out the aerospace HUD header, nominal avionics temperature (28°C), "
         "100% battery State-of-Charge, and standby state of GPR/Spectrometer instruments awaiting traversal initiation."),

        ("Step 2: Single Cell Survey Execution (▶ Scan Next)",
         "Click '▶ Scan Next'. The rover advances to Cell (0, 1). Demonstrate real-time multi-sensor sounding:\n"
         "• GPR Subplot: Crisp yellow dielectric horizon at 1.20 m depth paired with sharp A-scan energy spike.\n"
         "• Spectrometer Subplot: Measured reflectance curve tracing USGS laboratory ice benchmark with diagnostic dips at 1.25, 1.50, and 2.00 μm.\n"
         "• L2 Classifier Card: Displays 'WATER ICE' with 98.4% confidence and multiclass probability meters."),

        ("Step 3: L0 Reflex Hazard Intervention & Avoidance",
         "Advance the rover toward an obstacle cell (e.g., Cell (0, 3) with hazard score 0.80). Demonstrate safety autonomy:\n"
         "• L0 Autonomy Badge shifts to 'HAZARD BLOCKED'.\n"
         "• Rover logs '⛔ (0,3) L0 HAZARD DETECTED: Obstacle score 0.80 > 0.75 threshold. Mobility protected.'\n"
         "• Cell is marked red in the 2D survey grid; L2 science sounding is safely skipped."),

        ("Step 4: L1 Low-Power Preservation & Solar Recharge",
         "As consecutive scans drain power below 30%, demonstrate L1 resource management:\n"
         "• Battery card turns red/amber with warning: '⚡ Low-Power Hold Active'.\n"
         "• Click '☀️ Deploy Solar Panels (Recharge +25%)'. Telemetry shows battery replenishment and electronics cooling back to 28°C."),

        ("Step 5: Full 3D Digital Twin Inspection (View 3D Digital Twin)",
         "Click '🌑 View 3D Digital Twin'. Rotate the 3D scene in real time:\n"
         "• Show the low-angle 3° polar solar lighting and deep shadow inside the crater floor.\n"
         "• Inspect the rocker-bogie rover mesh conforming to local terrain tilt.\n"
         "• Point to the subsurface colored spheres and vertical borehole columns displaying identified minerals at exact depths."),

        ("Step 6: Autonomous Auto-Survey & Mission Completion",
         "Click '⏩ Auto-Survey'. The rover autonomously traverses remaining cells in real time, bypassing hazards and mapping all 36 cells.\n"
         "Highlight the final ISRU summary: 7 Water Ice deposits confirmed (~57.8 Tonnes pure H₂O equivalent to ~51.4 Tonnes LOX propellant).")
    ]
    for s_title, s_desc in demo_steps:
        doc.add_heading(s_title, level=3)
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.15
        p.add_run(s_desc)

    # ── Part II: PPT Presentation Deck & Speaker Script (10 Pts) ──
    h2 = doc.add_heading("Part II: PPT Presentation Deck Structure & Speaker Script (10 Points)", level=1)
    h2.paragraph_format.space_before = Pt(14); h2.paragraph_format.space_after = Pt(6)

    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.add_run(
        "Table 6 awards 10 points for 'PPT Presentation'. The presentation is structured as a tightly rehearsed 14-slide deck "
        "designed for a strict 10-minute presentation followed by a 5-minute Q&A defense. "
        "Speaking roles rotate among all four team members to demonstrate complete interdisciplinary command."
    )

    slides_data = [
        ("Slide 1: Title & Mission Vision\n(0:00 - 0:45 | Speaker: Haider)",
         "Visual: High-contrast render of L-MINER on lunar crater rim with glowing cyan sensor beam.\n"
         "Script: 'Honorable judges and organizing committee, good morning. We are Team L-MINER from the Institute of Space Technology, "
         "Islamabad. Today, we present L-MINER Mk-II: an autonomous multi-tier rover engineered for subsurface volatile prospecting "
         "and mineral classification in the cryogenic cold traps of the lunar South Pole.'"),

        ("Slide 2: The Planetary Challenge\n(0:45 - 1:30 | Speaker: Haider)",
         "Visual: Temperature and illumination map of the lunar South Pole showing Shackleton Crater at 40 K.\n"
         "Script: 'Sustainable human exploration under Artemis and the ILRS hinges on water ice. Trapped in Permanently Shadowed Regions "
         "at 40 Kelvin, these volatiles hold the key to life support and rocket propellant. But orbital remote sensing leaves a critical "
         "Ground-Truth Gap: optical sensors only see the top 10 microns of space-weathered dust, and communication shadows prevent teleoperation.'"),

        ("Slide 3: System Innovation & Topic Scope\n(1:30 - 2:15 | Speaker: Haider)",
         "Visual: Exploded 3D CAD render of the rover highlighting underbelly GPR radome and robotic arm spectrometer.\n"
         "Script: 'L-MINER bridges this gap through dual-modality sensing: an underbelly 500 MHz Ground Penetrating Radar that sounds "
         "the subsurface down to 3 meters, and a 0.5 to 2.5 micron VNIR-SWIR spectrometer on an articulated arm that confirms crystal chemistry.'"),

        ("Slide 4: Decoupled Hierarchical Autonomy\n(2:15 - 3:00 | Speaker: Saad)",
         "Visual: 3-tier autonomy architecture pyramid (L0 Reflex, L1 Resource, L2 Science).\n"
         "Script: 'To survive without Earth teleoperation, we designed a decoupled 3-tier autonomy architecture. "
         "L0 operates at 10 Hz: it reads HazCam stereo disparity to halt rover drive if obstacles exceed 0.75 hazard score. "
         "L1 operates at 1 Hz: it safeguards the battery State-of-Charge and electronics temperatures, autonomously initiating solar recharge cycles. "
         "L2 executes on-demand: activating sensors and running machine learning only when safe coordinates are reached.'"),

        ("Slide 5: Sensor Physics I: 500 MHz GPR\n(3:00 - 3:45 | Speaker: Haider)",
         "Visual: GPR wave propagation diagram, Fresnel reflection coefficient formula, and synthetic B-scan comparison.\n"
         "Script: 'Our synthetic sensor generation is mathematically anchored in planetary electromagnetic theory. "
         "At 500 MHz, radar waves penetrate lossy regolith down to 3 meters. Sharp dielectric contrast between porous regolith and dense ice "
         "produces a high-amplitude reflection coefficient of 0.85, whereas basaltic pyroxene reflects at 0.65, and conductive ilmenite attenuates the beam.'"),

        ("Slide 6: Sensor Physics II: VNIR-SWIR\n(3:45 - 4:30 | Speaker: Haider)",
         "Visual: 4 mineral reflectance spectra overlaid with USGS splib07 benchmarks and diagnostic absorption bands.\n"
         "Script: 'For surface mineralogy, our spectrometer operates across 200 channels from 0.5 to 2.5 microns. "
         "Because polar craters are pitch black, an active halogen illuminator illuminates the target. "
         "Water ice is diagnosed via fundamental vibrational O-H dips at 1.25, 1.5, and 2.0 microns—matching Chandrayaan-1 M³ observations. "
         "Pyroxene reveals Fe²⁺ crystal field bands at 1.0 and 2.0 microns, while ilmenite shows a flat 7% albedo from Fe-Ti charge transfer.'"),

        ("Slide 7: Edge Feature Extraction (10-D Vector)\n(4:30 - 5:15 | Speaker: Wasay)",
         "Visual: Data compression flowchart: 32,968 raw floats compressed into 10 scalar values.\n"
         "Script: 'Deep space lunar rovers cannot downlink gigabytes of raw data. We developed an onboard digital signal processing pipeline "
         "that reduces 32,968 raw sensor values into a 10-dimensional feature vector—achieving a 3,300-fold data reduction. "
         "Four features capture GPR amplitude, energy, contrast, and depth, while six features capture broadband albedo, diagnostic band depths, and spectral slope.'"),

        ("Slide 8: Edge Machine Learning Classifier\n(5:15 - 6:00 | Speaker: Wasay)",
         "Visual: Confusion matrix, ROC curves, and decision tree ensemble diagram showing 95.8% accuracy.\n"
         "Script: 'These 10 features feed an edge Random Forest classifier with 100 decision trees. "
         "Random Forest was selected for its sub-15 ms inference latency, mathematical explainability, and immunity to sensor white noise. "
         "Trained on Apollo 11 and 12 sample distributions, the model achieves 95.8% overall multiclass accuracy, with water ice recognized at 99.2% precision.'"),

        ("Slide 9: LIVE DEMO: Mission HUD & 3D Twin\n(6:00 - 7:30 | Speakers: Hajra & Saad)",
         "Visual: Live screen-switch to interactive Streamlit Mission Control HUD and 3D WebGL Digital Twin.\n"
         "Script: [Hajra] 'Let us examine the live system in operation. Here on our Mission HUD, you see the real-time avionics telemetry. "
         "When we command a scan, our dual GPR and spectrometer plots immediately generate measured curves against laboratory standards.'\n"
         "[Saad] 'Opening the 3D Digital Twin, judges can observe the 96x96 polar terrain under 3-degree low-angle solar lighting. "
         "As the rover moves, subterranean deposit ellipsoids appear at their exact classified depths, scaled by machine learning confidence.'"),

        ("Slide 10: In-Situ Resource Utilization (ISRU)\n(7:30 - 8:15 | Speaker: Hajra)",
         "Visual: Resource breakdown map, 57.8 Tonnes water ice yield, LOX/LH2 propellant production infographic.\n"
         "Script: 'The ultimate purpose of L-MINER is resource prospecting. Across our surveyed 60x60 meter grid, the system localized "
         "7 confirmed water ice deposits at an average depth of 0.88 meters. This equates to 57.8 Tonnes of pure water ice. "
         "Through cryogenic electrolysis, this yields 51.4 Tonnes of Liquid Oxygen and 6.4 Tonnes of Liquid Hydrogen—enough to fully refuel "
         "two lunar ascent stages and save over $180 million in Earth launch mass.'"),

        ("Slide 11: Performance Benchmarking\n(8:15 - 8:45 | Speaker: Wasay)",
         "Visual: Comparative benchmark table: L-MINER vs. Traditional Teleoperated Rovers.\n"
         "Script: 'Comparing L-MINER against conventional space rovers demonstrates a 14x increase in survey throughput, "
         "zero Earth-operator latency bottlenecks, and 100% mission survivability across 36 test cells.'"),

        ("Slide 12: Team Roster & Collaborative Workflow\n(8:45 - 9:15 | Speaker: Hajra)",
         "Visual: Photo collage of the four engineers at IST Islamabad, GitHub commit chart, and Trello board.\n"
         "Script: 'This system was conceived, engineered, and verified collaboratively at IST Islamabad. "
         "Haider modeled sensor physics, Wasay developed the ML classifier, Saad engineered autonomy and safety, and I built the telemetry HUD. "
         "Our daily Agile standups and version-controlled architecture enabled seamless integration.'"),

        ("Slide 13: Future Maturation Roadmap (TRL 4 -> 6)\n(9:15 - 9:45 | Speaker: Haider)",
         "Visual: Gantt chart and milestone roadmap showing cryo-vacuum testing and flight software porting.\n"
         "Script: 'Looking forward, our roadmap advances L-MINER from TRL 4 to TRL 6 by late 2027. "
         "We plan to validate physical 500 MHz antennas in a cryogenic JSC-1A lunar simulant bed and port our autonomy code to NASA Core Flight System on radiation-tolerant RTG4 FPGAs.'"),

        ("Slide 14: Conclusion & Q&A Defense\n(9:45 - 10:00 | Speaker: Haider)",
         "Visual: Mission summary takeaway slide with team contact information and project QR code.\n"
         "Script: 'In conclusion, L-MINER Mk-II proves that autonomous multi-tier rovers can unlock the resources of the lunar South Pole. "
         "Thank you, honorable judges. We are now ready for your questions.'")
    ]

    for s_title, s_content in slides_data:
        doc.add_heading(s_title, level=2)
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.15
        p.add_run(s_content)

    doc.add_heading("Anticipated Judges' Questions & Rehearsed Expert Answers", level=2)
    qa_list = [
        ("Judge Q1: How do you differentiate between water ice and high-porosity regolith voids in GPR data?",
         "Haider: 'Excellent question. A regolith void creates a dielectric transition from regolith (ε_r ≈ 2.6) to vacuum (ε_r = 1.0), "
         "which reverses the phase of the reflected electromagnetic wave. In contrast, ice permafrost (ε_r ≈ 3.1) exhibits a forward phase step. "
         "Crucially, our system does not rely on GPR alone—the robotic-arm spectrometer concurrently tests for molecular O-H vibrational absorption "
         "at 1.5 and 2.0 microns. Dual-modality sensor fusion eliminates false positives.'"),

        ("Judge Q2: In Permanently Shadowed Regions, there is no sunlight. How does L-MINER recharge?",
         "Saad: 'L-MINER operates on an opportunistic traverse strategy along crater rim corridors (such as Shackleton or Malapert Mountain). "
         "The rover dips into cold traps for science sounding on battery power, and our L1 autonomy monitors reserves. "
         "Before the battery drops below 30%, L1 commands an ascent back to the crater rim's Peaks of Eternal Light to deploy solar arrays and recharge.'"),

        ("Judge Q3: Why choose a Random Forest model instead of a Convolutional Neural Network (CNN)?",
         "Wasay: 'While deep CNNs excel on high-power GPUs, spaceflight processors (like the BAE RAD750 or RTG4 FPGA) have stringent power budgets (<10 W). "
         "Our 10-D feature extraction accomplishes 3,300x data compression, allowing Random Forest to run in under 15 milliseconds on a lightweight CPU. "
         "Furthermore, Random Forest does not overfit on sparse extraterrestrial training data and provides transparent, explainable decision trees essential for mission-critical aerospace flight certification.'")
    ]
    for q, a in qa_list:
        doc.add_heading(q, level=3)
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.15
        p.add_run(a)

    # ── Part III: Artistry & Visual Aesthetics (5 Pts) ──
    h3 = doc.add_heading("Part III: Artistry, Aesthetics & Visual Identity (5 Points)", level=1)
    h3.paragraph_format.space_before = Pt(14); h3.paragraph_format.space_after = Pt(6)

    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.add_run(
        "Table 6 awards 5 points for 'Artistry'. L-MINER achieves visual excellence through a cohesive, aerospace-inspired design language:\n\n"
        "1. Aerospace Mission Control Dark Theme: The interface avoids generic web themes, adopting a deep space radial background "
        "(#0C1527 to #010409) that mirrors NASA and ESA mission control consoles. This maximizes contrast and minimizes glare during low-light demonstrations.\n\n"
        "2. Functional Color Semantics: Every color conveys instant operational meaning:\n"
        "   • Electric Cyan (#00E5FF): Primary telemetry, water ice deposits, and GPR wavefronts.\n"
        "   • Safety Emerald (#00E676): L0 nominal clearance and Pyroxene signatures.\n"
        "   • Titanium Amber (#FF9100): Ilmenite classification and L1 resource warnings.\n"
        "   • Hazard Crimson (#FF1744): Terrain obstacle barriers and low-power holds.\n\n"
        "3. Technical Typography Pairing: 'Space Grotesk' is utilized for bold, authoritative headers, while 'JetBrains Mono' "
        "is used for telemetry readouts, coordinate matrices, and sensor metrics, creating a professional scientific aesthetic.\n\n"
        "4. 3D Cyber-Physical Realism: The 3D Digital Twin avoids abstract wireframes. It features realistic 3-degree low-angle polar lighting, "
        "a gold multi-layer insulation (MLI) rover chassis, silicon solar panels, and semi-transparent subsurface volumetric deposits."
    )

    doc.save(filepath)
    print(f"[SUCCESS] Saved DOCX: {filepath}")


# ─────────────────────────────────────────────────────────────
# BUILD PDF: DELIVERABLE 4
# ─────────────────────────────────────────────────────────────
def build_doc4_pdf(filepath):
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    styles = getSampleStyleSheet()

    style_meta = ParagraphStyle('MetaTag', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.HexColor("#00A8E8"), spaceAfter=3)
    style_title = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=colors.HexColor("#0B2545"), spaceAfter=5)
    style_subtitle = ParagraphStyle('DocSub', parent=styles['Normal'], fontName='Helvetica', fontSize=9.5, leading=13, textColor=colors.HexColor("#134074"), spaceAfter=10)
    style_h1 = ParagraphStyle('Heading1_Custom', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=11.5, leading=14, textColor=colors.HexColor("#0B2545"), spaceBefore=9, spaceAfter=4, keepWithNext=True)
    style_h2 = ParagraphStyle('Heading2_Custom', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=9, leading=11.5, textColor=colors.HexColor("#134074"), spaceBefore=6, spaceAfter=3, keepWithNext=True)
    style_body = ParagraphStyle('Body_Custom', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=10.5, textColor=colors.HexColor("#1E293B"), spaceAfter=4)
    style_bullet = ParagraphStyle('Bullet_Custom', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=10.5, textColor=colors.HexColor("#1E293B"), leftIndent=10, firstLineIndent=-7, spaceAfter=2)
    style_callout = ParagraphStyle('Callout_Text', parent=styles['Normal'], fontName='Helvetica', fontSize=7, leading=9.5, textColor=colors.HexColor("#1E293B"))
    style_tbl_cell = ParagraphStyle('Tbl_Cell', parent=styles['Normal'], fontName='Helvetica', fontSize=6.5, leading=8.5, textColor=colors.HexColor("#1E293B"))
    style_tbl_hdr = ParagraphStyle('Tbl_Hdr', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7, leading=9, textColor=colors.white)

    elements = []

    elements.append(Paragraph("ISSSP 2026 — TRACK 3 FINALS: ITEMS 5, 6 & 7 (WORK DISPLAY, PPT & ARTISTRY — 40 POINTS)", style_meta))
    elements.append(Paragraph("Presentation Script, Work Display & Simulation Guide", style_title))
    elements.append(Paragraph(
        "Complete 14-Slide Deck Blueprint, Word-for-Word 10-Minute Presentation Script, "
        "Judge Q&A Defense, Live HUD/3D Demonstration Walkthrough, and Artistry Aesthetics Guide",
        style_subtitle
    ))

    # Meta Table
    meta_data = [
        [Paragraph("<b>Project:</b> L-MINER Mk-II Lunar Prospector", style_tbl_cell), Paragraph("<b>Institution:</b> Institute of Space Technology (IST), Islamabad", style_tbl_cell)],
        [Paragraph("<b>Scoring Focus:</b> Items 5 (25 Pts), 6 (10 Pts), 7 (5 Pts)", style_tbl_cell), Paragraph("<b>Duration:</b> 10 Min Pitch + 5 Min Q&A Defense", style_tbl_cell)]
    ]
    t_meta = Table(meta_data, colWidths=[240, 247])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5), ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(t_meta)
    elements.append(Spacer(1, 6))

    # Part I: Work Display (25 Pts)
    elements.append(Paragraph("Part I: Work Display & Simulation Architecture (25 Points)", style_h1))
    elements.append(Paragraph(
        "Table 6 awards 25 points for 'Work display / simulation design'. L-MINER demonstrates a dual-interface cyber-physical environment:<br/>"
        "<b>1. Interactive Mission Control HUD (dashboard.py):</b> Real-time aerospace telemetry cards, dual GPR B-scan + A-scan energy traces, "
        "USGS laboratory benchmark overlay curves, autonomy state indicators, and survey sequence buttons.<br/>"
        "<b>2. High-Fidelity 3D WebGL Digital Twin (visualization_3d.py):</b> 96x96 crater terrain mesh with 3° polar solar illumination, "
        "6-wheel rocker-bogie rover mesh, terrain-following slope adaptation, and subterranean deposit ellipsoids sized by ML confidence.",
        style_body
    ))

    # Demo Steps Table
    demo_data = [
        [Paragraph("Step", style_tbl_hdr), Paragraph("Simulation Action", style_tbl_hdr), Paragraph("Demonstration Focus for Judges", style_tbl_hdr)],
        [Paragraph("<b>1. Boot</b>", style_tbl_cell), Paragraph("Launch HUD (:8501)", style_tbl_cell), Paragraph("Avionics nominal (28°C), 100% battery, instruments standby.", style_tbl_cell)],
        [Paragraph("<b>2. Scan</b>", style_tbl_cell), Paragraph("Click '▶ Scan Next'", style_tbl_cell), Paragraph("Cell (0,1): GPR B-scan yellow horizon at 1.2 m, spectrometer ice dips at 1.25/1.5/2.0 μm, ML classifies Water Ice (98.4%).", style_tbl_cell)],
        [Paragraph("<b>3. Hazard</b>", style_tbl_cell), Paragraph("Encounter (0,3)", style_tbl_cell), Paragraph("Obstacle score 0.80 >= 0.75 triggers L0 halt. Mobility safely protected.", style_tbl_cell)],
        [Paragraph("<b>4. Power</b>", style_tbl_cell), Paragraph("Battery drops <30%", style_tbl_cell), Paragraph("L1 low-power hold engaged. Deploy solar panels for +25% recharge.", style_tbl_cell)],
        [Paragraph("<b>5. 3D Twin</b>", style_tbl_cell), Paragraph("Toggle 3D View", style_tbl_cell), Paragraph("Rotate 3D scene: 3° polar shadows, rocker-bogie tilt, subterranean spheres.", style_tbl_cell)],
        [Paragraph("<b>6. Auto</b>", style_tbl_cell), Paragraph("Click '⏩ Auto-Survey'", style_tbl_cell), Paragraph("Autonomous completion of 36 cells. Final summary: ~57.8 Tonnes Water Ice.", style_tbl_cell)]
    ]
    t_demo = Table(demo_data, colWidths=[50, 110, 327])
    t_demo.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0B2545")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#F8FAFC"), colors.white]),
        ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_demo)
    elements.append(Spacer(1, 6))

    # Part II: PPT Presentation & Script (10 Pts)
    elements.append(Paragraph("Part II: PPT Presentation Deck Structure & Speaker Script (10 Points)", style_h1))
    elements.append(Paragraph(
        "Structured as a 14-slide presentation deck timed for exactly 10 minutes (plus 5 minutes for judge Q&A). Speaking roles rotate among all four team members:",
        style_body
    ))

    slides_summary = [
        [Paragraph("Slide & Timing", style_tbl_hdr), Paragraph("Speaker", style_tbl_hdr), Paragraph("Core Message & Technical Content", style_tbl_hdr)],
        [Paragraph("<b>1. Title & Vision</b> (0:00-0:45)", style_tbl_cell), Paragraph("Haider", style_tbl_cell), Paragraph("Introduction to L-MINER Mk-II: Autonomous lunar polar volatile prospecting.", style_tbl_cell)],
        [Paragraph("<b>2. Cold Traps</b> (0:45-1:30)", style_tbl_cell), Paragraph("Haider", style_tbl_cell), Paragraph("The Ground-Truth Gap: Why orbital sensors cannot resolve subsurface ice volume.", style_tbl_cell)],
        [Paragraph("<b>3. System Concept</b> (1:30-2:15)", style_tbl_cell), Paragraph("Haider", style_tbl_cell), Paragraph("Dual-modality payload: 500 MHz GPR (depth) + VNIR-SWIR Spectrometer (chemistry).", style_tbl_cell)],
        [Paragraph("<b>4. 3-Tier Autonomy</b> (2:15-3:00)", style_tbl_cell), Paragraph("Saad", style_tbl_cell), Paragraph("L0 Safety Reflex (10 Hz), L1 Resource Manager (1 Hz), L2 Cognitive Science Layer.", style_tbl_cell)],
        [Paragraph("<b>5. Radar Physics</b> (3:00-3:45)", style_tbl_cell), Paragraph("Haider", style_tbl_cell), Paragraph("500 MHz GPR wave propagation, dielectric contrast (Γ=0.85 for ice), B-scans.", style_tbl_cell)],
        [Paragraph("<b>6. Spectroscopy</b> (3:45-4:30)", style_tbl_cell), Paragraph("Haider", style_tbl_cell), Paragraph("0.5–2.5 μm active spectrometry, USGS splib07 validation, diagnostic ice bands.", style_tbl_cell)],
        [Paragraph("<b>7. 10-D Features</b> (4:30-5:15)", style_tbl_cell), Paragraph("Wasay", style_tbl_cell), Paragraph("3,300x edge compression: 32,968 raw floats reduced to 10 scalar features.", style_tbl_cell)],
        [Paragraph("<b>8. ML Engine</b> (5:15-6:00)", style_tbl_cell), Paragraph("Wasay", style_tbl_cell), Paragraph("Random Forest (100 trees), 95.8% accuracy, sub-15 ms inference latency.", style_tbl_cell)],
        [Paragraph("<b>9. LIVE DEMO</b> (6:00-7:30)", style_tbl_cell), Paragraph("Hajra/Saad", style_tbl_cell), Paragraph("Live demonstration of Mission Control HUD and 3D WebGL Digital Twin.", style_tbl_cell)],
        [Paragraph("<b>10. ISRU Yield</b> (7:30-8:15)", style_tbl_cell), Paragraph("Hajra", style_tbl_cell), Paragraph("~57.8 Tonnes Water Ice localized; yields 51.4 T LOX + 6.4 T LH2 propellant.", style_tbl_cell)],
        [Paragraph("<b>11. Benchmarking</b> (8:15-8:45)", style_tbl_cell), Paragraph("Wasay", style_tbl_cell), Paragraph("14x faster throughput vs. teleoperated rovers, zero latency bottlenecks.", style_tbl_cell)],
        [Paragraph("<b>12. Team & Agile</b> (8:45-9:15)", style_tbl_cell), Paragraph("Hajra", style_tbl_cell), Paragraph("Interdisciplinary collaboration at IST Islamabad, daily standups, Git PRs.", style_tbl_cell)],
        [Paragraph("<b>13. Roadmap</b> (9:15-9:45)", style_tbl_cell), Paragraph("Haider", style_tbl_cell), Paragraph("TRL 4 -> 6: Cryo-vacuum simulant bed testing, NASA Core Flight System port.", style_tbl_cell)],
        [Paragraph("<b>14. Conclusion</b> (9:45-10:00)", style_tbl_cell), Paragraph("Haider", style_tbl_cell), Paragraph("Final mission summary & transition to 5-minute Judge Q&A Defense.", style_tbl_cell)]
    ]
    t_slides = Table(slides_summary, colWidths=[95, 60, 332])
    t_slides.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#134074")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#F8FAFC"), colors.white]),
        ('TOPPADDING', (0,0), (-1,-1), 2.5), ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_slides)
    elements.append(Spacer(1, 6))

    # Judge Q&A Defense
    elements.append(Paragraph("Anticipated Judge Q&A Defense", style_h2))
    qa_pdf_data = [
        [Paragraph("Judge Question", style_tbl_hdr), Paragraph("Team Defense Answer", style_tbl_hdr)],
        [Paragraph("<b>Q1: Void vs. Ice in GPR?</b>", style_tbl_cell), 
         Paragraph("<b>Haider:</b> A void creates a dielectric transition to vacuum (ε_r=1.0) with phase inversion. Ice permafrost (ε_r=3.1) exhibits a forward phase step. Crucially, the spectrometer concurrently tests for molecular O-H absorption at 1.5/2.0 μm, eliminating false positives.", style_tbl_cell)],
        [Paragraph("<b>Q2: Recharging in PSR darkness?</b>", style_tbl_cell), 
         Paragraph("<b>Saad:</b> Opportunistic crater-corridor traverse. The rover dips into cold traps for science sounding on battery power. Before SoC drops <30%, L1 commands ascent back to crater rim 'Peaks of Eternal Light' to deploy solar arrays.", style_tbl_cell)],
        [Paragraph("<b>Q3: Why Random Forest over CNN?</b>", style_tbl_cell), 
         Paragraph("<b>Wasay:</b> Spaceflight CPUs have strict <10W power budgets. Our 10-D feature reduction runs Random Forest in <15 ms, resists overfitting on sparse extraterrestrial training data, and provides explainable decision trees essential for flight qualification.", style_tbl_cell)]
    ]
    t_qa = Table(qa_pdf_data, colWidths=[120, 367])
    t_qa.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0B2545")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#F8FAFC"), colors.white]),
        ('TOPPADDING', (0,0), (-1,-1), 2.5), ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_qa)
    elements.append(Spacer(1, 6))

    # Part III: Artistry (5 Pts)
    elements.append(Paragraph("Part III: Artistry, Aesthetics & Visual Identity (5 Points)", style_h1))
    elements.append(Paragraph(
        "<b>1. Mission Control Dark Theme:</b> Deep space background (#0C1527 to #010409) creates an authoritative aerospace command center look, minimizing eye fatigue during dark-room judging.<br/>"
        "<b>2. Functional Semantic Colors:</b> Cyan (#00E5FF) for water ice and GPR radar; Emerald (#00E676) for nominal status; Amber (#FF9100) for ilmenite and power alerts; Crimson (#FF1744) for obstacle hazards.<br/>"
        "<b>3. Technical Typography:</b> 'Space Grotesk' for bold mission titles paired with 'JetBrains Mono' for telemetry readouts.<br/>"
        "<b>4. 3D Visual Polish:</b> Rocker-bogie mesh with gold MLI foil, silicon panels, 3° polar shadows, and confidence-scaled subsurface deposit ellipsoids.",
        style_body
    ))

    doc.build(elements, canvasmaker=NumberedCanvas)
    print(f"[SUCCESS] Saved PDF: {filepath}")


if __name__ == "__main__":
    out_dir = r"E:\L-miner directory\Finals_Track3_Deliverables"
    os.makedirs(out_dir, exist_ok=True)
    docx_path = os.path.join(out_dir, "4_Presentation_Script_and_Simulation_Guide.docx")
    pdf_path = os.path.join(out_dir, "4_Presentation_Script_and_Simulation_Guide.pdf")
    build_doc4_docx(docx_path)
    build_doc4_pdf(pdf_path)
