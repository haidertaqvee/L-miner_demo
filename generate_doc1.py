"""
Generator for Deliverable 1: Community Building & Publicity Campaign Guide
Table 6 Scoring Rules: Item 1 (Community Building, Until 31st Oct - 10 Points)
Generates both .docx and .pdf files.
"""

import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

# ─────────────────────────────────────────────────────────────
# NUMBERED CANVAS FOR REPORTLAB (Page X of Y + Running Headers)
# ─────────────────────────────────────────────────────────────
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
        
        # Header (Pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 842 - 36, "L-MINER Mk-II | Community Building & Publicity Campaign Guide")
            self.drawRightString(595 - 54, 842 - 36, "ISSSP 2026 — Track 3 Finals")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 842 - 42, 595 - 54, 842 - 42)

        # Footer (All pages)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 48, 595 - 54, 48)
        
        self.drawString(54, 34, "IST Islamabad | Track 3 Finals Scoring Criterion 1 (10 Points)")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(595 - 54, 34, page_str)
        self.restoreState()


# ─────────────────────────────────────────────────────────────
# DOCX HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────
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
# BUILD DOCX: DELIVERABLE 1
# ─────────────────────────────────────────────────────────────
def build_doc1_docx(filepath):
    doc = docx.Document()
    
    # Page Margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.85)
        section.right_margin = Inches(0.85)

    # Styles
    PRIMARY = RGBColor(11, 37, 69)       # #0B2545 Deep Navy
    SECONDARY = RGBColor(19, 64, 116)    # #134074 Slate Blue
    ACCENT = RGBColor(0, 168, 232)       # #00A8E8 Cyan Blue
    DARK_TEXT = RGBColor(30, 41, 59)     # #1E293B
    MUTED_TEXT = RGBColor(100, 116, 139) # #64748B

    # Header & Footer in docx
    footer = doc.sections[0].footer
    f_p = footer.paragraphs[0]
    f_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    f_run = f_p.add_run("L-MINER Mk-II | Community Building Guide (Track 3) · IST Islamabad")
    f_run.font.size = Pt(8)
    f_run.font.color.rgb = MUTED_TEXT

    # ── Title & Meta ──
    p_meta = doc.add_paragraph()
    r_tag = p_meta.add_run("ISSSP 2026 — TRACK 3: LUNAR SURFACE ROBOTICS · FINALS SCORING CRITERION 1\n")
    r_tag.font.name = "Segoe UI"
    r_tag.font.size = Pt(9)
    r_tag.font.bold = True
    r_tag.font.color.rgb = ACCENT
    
    r_title = p_meta.add_run("Community Building & Publicity Campaign Guide")
    r_title.font.name = "Segoe UI"
    r_title.font.size = Pt(22)
    r_title.font.bold = True
    r_title.font.color.rgb = PRIMARY

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_after = Pt(14)
    r_sub = p_sub.add_run(
        "Comprehensive Strategy, Outreach Blueprint, Communications Specialist Playbook, "
        "Ready-to-Publish Copy & Team Collaboration Charter (Deadline: 31st Oct — Max Score: 10/10)"
    )
    r_sub.font.name = "Segoe UI"
    r_sub.font.size = Pt(11)
    r_sub.font.color.rgb = SECONDARY

    # Team Info Box
    tbl_meta = doc.add_table(rows=2, cols=2)
    tbl_meta.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_data = [
        ("Project Name:", "L-MINER Mk-II: Autonomous Lunar Mineral Prospecting Payload",
         "Institution:", "Institute of Space Technology (IST), Islamabad"),
        ("Scoring Focus:", "Table 6: Item 1 (Publicize Contest Concept & Team Cooperation)",
         "Team Roster:", "Haider Taqvee, Abdul Wasay, Saad, Hajra")
    ]
    for r_idx, (k1, v1, k2, v2) in enumerate(meta_data):
        row = tbl_meta.rows[r_idx]
        c1, c2 = row.cells[0], row.cells[1]
        set_cell_background(c1, "F8FAFC")
        set_cell_background(c2, "F8FAFC")
        set_cell_margins(c1, 80, 80, 100, 100)
        set_cell_margins(c2, 80, 80, 100, 100)
        
        p1 = c1.paragraphs[0]
        r = p1.add_run(f"{k1} "); r.bold = True; r.font.size = Pt(9); r.font.color.rgb = PRIMARY
        r2 = p1.add_run(v1); r2.font.size = Pt(9); r2.font.color.rgb = DARK_TEXT
        
        p2 = c2.paragraphs[0]
        r = p2.add_run(f"{k2} "); r.bold = True; r.font.size = Pt(9); r.font.color.rgb = PRIMARY
        r2 = p2.add_run(v2); r2.font.size = Pt(9); r2.font.color.rgb = DARK_TEXT

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # ── Section 1 ──
    h1 = doc.add_heading("1. Strategic Alignment with Table 6 Finals Scoring Rules", level=1)
    h1.paragraph_format.space_before = Pt(14)
    h1.paragraph_format.space_after = Pt(6)
    
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.add_run(
        "Table 6 allocates 10 points out of 100 to Item 1: Community Building (until 31st October). "
        "The scoring criteria are judged by the Organizing Committee and appointed evaluators on two specific dimensions:"
    )
    
    bullets = [
        ("Publicize Contest Concept (5 Points): ", 
         "Actively promoting the contest vision, themes, and societal impact across university communities, "
         "social channels, and youth STEM forums. Demonstrates public engagement, reach, and advocacy for lunar science."),
        ("Team Cooperation & Communication (5 Points): ", 
         "Demonstrating cohesive interdisciplinary teamwork, transparent task allocation, systematic meeting logs, "
         "and structured communications leadership led by a designated Communications Specialist.")
    ]
    for b_title, b_desc in bullets:
        bp = doc.add_paragraph(style='List Bullet')
        bp.paragraph_format.space_after = Pt(3)
        bp.paragraph_format.line_spacing = 1.15
        r_bt = bp.add_run(b_title); r_bt.bold = True; r_bt.font.color.rgb = PRIMARY
        r_bd = bp.add_run(b_desc)

    add_docx_callout(
        doc,
        "Maximum Points Mandate: To secure the full 10/10 sub-total, the team must not merely 'post online' "
        "but deliver a cohesive campaign with measurable analytics (impressions, shares, student interactions), "
        "official tagging of the contest organizers, and documented agile collaboration records submitted before the 31st Oct deadline.",
        title="Judge Evaluation Strategy"
    )

    # ── Section 2 ──
    h2 = doc.add_heading("2. Four-Phase Campaign Roadmap (Until 31st October)", level=1)
    h2.paragraph_format.space_before = Pt(14)
    h2.paragraph_format.space_after = Pt(6)

    tbl_phases = doc.add_table(rows=5, cols=4)
    tbl_phases.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Phase & Dates", "Strategic Focus", "Deliverables & Activities", "Target KPIs"]
    for i, h in enumerate(headers):
        cell = tbl_phases.cell(0, i)
        set_cell_background(cell, "0B2545")
        set_cell_margins(cell, 100, 100, 100, 100)
        p = cell.paragraphs[0]
        r = p.add_run(h); r.bold = True; r.font.color.rgb = RGBColor(255, 255, 255); r.font.size = Pt(8.5)

    phases_data = [
        ("Phase 1: Concept Launch\n(Oct 15 – Oct 19)", 
         "Publicize contest concept & introduce L-MINER mission.",
         "• Official competition announcement post.\n• Contest vision infogram.\n• Mission logo & rover teaser render.",
         "500+ Impressions\n50+ Engagements\n10 University Shares"),
        ("Phase 2: Tech Deep-Dive\n(Oct 20 – Oct 24)", 
         "Educational outreach on lunar South Pole science & autonomy.",
         "• Carousel: 'Why is Lunar Water Ice Hard to Find?'\n• GPR vs Spectrometer explainer.\n• Tag contest organizers.",
         "800+ Impressions\n150+ Carousel swipes\n5 STEM club reposts"),
        ("Phase 3: Interactive Demo\n(Oct 25 – Oct 28)", 
         "Engage community with interactive digital twin & poll.",
         "• 45s screen capture reel of 3D Payload HUD & Mobile Simulation.\n• Community poll on lunar resources.\n• Live Q&A in comments.",
         "1,200+ Impressions\n100+ Poll votes\n30+ Comments"),
        ("Phase 4: Final Sprint\n(Oct 29 – Oct 31)", 
         "Team cooperation showcase & competition eve rally.",
         "• Team Spotlight: Meet the 4 Engineers.\n• Behind-the-scenes lab/code photos.\n• Final contest tribute post.",
         "1,500+ Total Reach\nConsolidated Dossier\n100% Submission On Time")
    ]
    for row_idx, row_vals in enumerate(phases_data, start=1):
        bg = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, val in enumerate(row_vals):
            cell = tbl_phases.cell(row_idx, col_idx)
            set_cell_background(cell, bg)
            set_cell_margins(cell, 80, 80, 90, 90)
            p = cell.paragraphs[0]
            p.paragraph_format.line_spacing = 1.1
            r = p.add_run(val); r.font.size = Pt(8); r.font.color.rgb = DARK_TEXT

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # ── Section 3 ──
    h3 = doc.add_heading("3. Communications Specialist Playbook & Role Distribution", level=1)
    h3.paragraph_format.space_before = Pt(14)
    h3.paragraph_format.space_after = Pt(6)

    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.add_run(
        "Table 6 explicitly identifies the 'Communications Specialist' as a key evaluated element of Community Building. "
        "The Communications Specialist serves as the bridge between technical engineering and public engagement."
    )

    tbl_roles = doc.add_table(rows=5, cols=3)
    tbl_roles.alignment = WD_TABLE_ALIGNMENT.CENTER
    r_headers = ["Team Member", "Primary Technical Role", "Communications & Outreach Responsibility"]
    for i, h in enumerate(r_headers):
        cell = tbl_roles.cell(0, i)
        set_cell_background(cell, "134074")
        set_cell_margins(cell, 100, 100, 100, 100)
        p = cell.paragraphs[0]
        r = p.add_run(h); r.bold = True; r.font.color.rgb = RGBColor(255, 255, 255); r.font.size = Pt(8.5)

    roles_data = [
        ("Hajra", "Human-Machine Interface &\nStreamlit Dashboard Lead", 
         "Lead Communications Specialist: Manages social postings, graphics generation, community replies, and press communication."),
        ("Haider Taqvee", "Sensor Physics &\nSynthetic Data Generator Lead", 
         "Technical Science Content Writer: Drafts plain-language explanations of GPR dielectric physics and USGS spectroscopy for public posts."),
        ("Abdul Wasay", "Machine Learning &\nClassifier Modeling Lead", 
         "Data Visualization Specialist: Creates high-resolution confusion matrices, ROC plots, and benchmark graphics for carousels."),
        ("Saad", "Autonomous Safety (L0/L1) &\nSystems Integration Lead", 
         "Team Operations & Documentation Officer: Maintains meeting minutes, GitHub project board, attendance records, and collaboration proof.")
    ]
    for row_idx, row_vals in enumerate(roles_data, start=1):
        bg = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, val in enumerate(row_vals):
            cell = tbl_roles.cell(row_idx, col_idx)
            set_cell_background(cell, bg)
            set_cell_margins(cell, 80, 80, 90, 90)
            p = cell.paragraphs[0]
            p.paragraph_format.line_spacing = 1.1
            r = p.add_run(val); r.font.size = Pt(8.5); r.font.color.rgb = DARK_TEXT

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # ── Section 4 ──
    h4 = doc.add_heading("4. Ready-to-Publish Outreach Assets & Copy", level=1)
    h4.paragraph_format.space_before = Pt(14)
    h4.paragraph_format.space_after = Pt(6)

    doc.add_heading("Asset 1: LinkedIn Long-Form Launch Post (Phase 1)", level=2)
    post1_text = (
        "🚀 Exciting News from IST Islamabad!\n\n"
        "Our team is thrilled to participate in ISSSP 2026 Track 3 (Lunar Surface Robotics & Autonomous Exploration)! 🌙\n\n"
        "As humanity prepares to establish sustainable bases on the Moon through Artemis and international lunar research programs, "
        "one question remains paramount: How do we locate volatile water ice trapped inside permanently shadowed craters at 40 Kelvin?\n\n"
        "Introducing L-MINER Mk-II: An Autonomous Multi-Tier Mineral Prospecting Payload System for Lunar Surface Exploration.\n"
        "Equipped with 500 MHz Ground Penetrating Radar, 0.5–2.5 μm VNIR-SWIR Reflectance Spectroscopy, and edge Random Forest ML, "
        "L-MINER's autonomous payload firmware navigates hazards, monitors power, and maps resources without Earth teleoperation lag.\n\n"
        "Proud to represent the Institute of Space Technology alongside teammates Haider Taqvee, Abdul Wasay, Saad, and Hajra.\n\n"
        "Follow our journey as we showcase our 3D digital twin and mission control system before the Oct 31st finals!\n\n"
        "#ISSSP2026 #LunarExploration #SpaceRobotics #ISTIslamabad #MoonToMars #ISRU #AutonomousSystems"
    )
    add_docx_callout(doc, post1_text, title="LinkedIn Copy — Ready to Publish", border_color="00A8E8", bg_color="F0F9FF")

    doc.add_heading("Asset 2: X / Twitter Technical Thread (Phase 2)", level=2)
    post2_text = (
        "🧵 1/5 How does an autonomous science payload 'see' water ice buried 2 meters under lunar dust? Here's how our project for #ISSSP2026 Track 3 works! 👇\n\n"
        "2/5 Optical cameras only see the top 10 microns of dust. That's why L-MINER Mk-II combines TWO complementary sensors: "
        "an underbelly 500 MHz GPR (for depth) + a robotic-arm VNIR-SWIR Spectrometer (for chemistry). 📡🔬\n\n"
        "3/5 Water ice has a sharp dielectric boundary (ε_r ≈ 3.1) vs dry regolith, creating high-amplitude radar echoes. "
        "Spectroscopically, it reveals diagnostic absorption troughs at 1.25, 1.5, and 2.0 μm (matching Chandrayaan-1 M³ data)! ❄️\n\n"
        "4/5 Our edge Random Forest model extracts a 10-D feature vector, compressing 32,000+ raw data points into instant classification "
        "with 95%+ accuracy in under 15 ms! ⚡\n\n"
        "5/5 Huge thanks to the ISSSP 2026 organizing committee for inspiring student aerospace innovation! Stay tuned for our 3D Digital Twin demo! 🚀"
    )
    add_docx_callout(doc, post2_text, title="Twitter/X Thread Copy", border_color="134074", bg_color="F8FAFC")

    doc.add_heading("Asset 3: Official University Press Release / Department Bulletin", level=2)
    pr_text = (
        "FOR IMMEDIATE RELEASE — IST SPACE SCIENCE & AERONAUTICS\n"
        "IST Student Team Qualifies for Finals in International Space Competition (ISSSP 2026 Track 3)\n\n"
        "ISLAMABAD — A multidisciplinary team of undergraduate engineers from the Institute of Space Technology (IST) "
        "has qualified for the finals of ISSSP 2026 Track 3 with their autonomous lunar prospecting payload project, L-MINER Mk-II.\n\n"
        "The project addresses the critical challenge of autonomous In-Situ Resource Utilization (ISRU) prospecting in the lunar South Pole. "
        "By fusing multi-frequency Ground Penetrating Radar with Short-Wave Infrared Spectroscopy and a three-tier hierarchical autonomy architecture, "
        "the system enables safe, unassisted prospecting inside Permanently Shadowed Regions (PSRs).\n\n"
        "The team comprises Haider Taqvee (Sensor Simulation), Abdul Wasay (Machine Learning), Saad (Autonomy Systems), and Hajra (Mission Interface).\n"
        "Final demonstrations and judging take place on October 31st, 2026."
    )
    add_docx_callout(doc, pr_text, title="Official Press Release Copy", border_color="0B2545", bg_color="F1F5F9")

    # ── Section 5 ──
    h5 = doc.add_heading("5. Team Cooperation & Internal Communication Protocol", level=1)
    h5.paragraph_format.space_before = Pt(14)
    h5.paragraph_format.space_after = Pt(6)

    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.add_run(
        "To provide empirical proof of 'Team cooperation & communication' (Table 6, Item 1), "
        "the team instituted a formal Agile/Scrum collaboration framework documented through GitHub, Discord, and Trello."
    )

    tbl_collab = doc.add_table(rows=5, cols=3)
    tbl_collab.alignment = WD_TABLE_ALIGNMENT.CENTER
    c_headers = ["Collaboration Pillar", "Tools & Infrastructure", "Operational Protocol & Artifacts"]
    for i, h in enumerate(c_headers):
        cell = tbl_collab.cell(0, i)
        set_cell_background(cell, "0B2545")
        set_cell_margins(cell, 100, 100, 100, 100)
        p = cell.paragraphs[0]
        r = p.add_run(h); r.bold = True; r.font.color.rgb = RGBColor(255, 255, 255); r.font.size = Pt(8.5)

    collab_data = [
        ("Daily Standups\n& Synchronization", "Discord Voice / Google Meet", 
         "15-minute daily sync at 18:00 PKT. Agenda: What was completed yesterday, blockers, today's sprint goals. Meeting minutes recorded in shared log."),
        ("Source Control &\nCode Quality", "GitHub Repository\n(Git Feature Branches)", 
         "Strict branch protection. All code merged via Pull Requests requiring peer review. Separate modules for data_generator, model, l0_l1_logic, dashboard."),
        ("Task & Milestone\nTracking", "Trello Kanban Board", 
         "Swimlanes: Backlog, In Progress, Code Review, Tested, Ready for Oct 31. Tasks tagged with assignee, priority, and Table 6 criteria."),
        ("Document &\nDeliverable Archive", "Google Drive Shared Workspace", 
         "Version-controlled repository for poster mockups, PPT slide decks, simulation recordings, and official score rule references.")
    ]
    for row_idx, row_vals in enumerate(collab_data, start=1):
        bg = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, val in enumerate(row_vals):
            cell = tbl_collab.cell(row_idx, col_idx)
            set_cell_background(cell, bg)
            set_cell_margins(cell, 80, 80, 90, 90)
            p = cell.paragraphs[0]
            p.paragraph_format.line_spacing = 1.1
            r = p.add_run(val); r.font.size = Pt(8.5); r.font.color.rgb = DARK_TEXT

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # ── Section 6 ──
    h6 = doc.add_heading("6. Evidence Submission Checklist for Judges (Before 31st Oct)", level=1)
    h6.paragraph_format.space_before = Pt(14)
    h6.paragraph_format.space_after = Pt(6)

    check_items = [
        "Publicity Posts Live: Links and screenshots of LinkedIn, Twitter/X, and Instagram posts tagging the competition.",
        "Engagement Metric Sheet: Total views, impressions, reposts, and student comments compiled into an appendix.",
        "Team Standup Logs: 14 consecutive daily meeting minute summaries signed off by all four team members.",
        "GitHub Contribution Matrix: Multi-author commit frequency proving active collaboration across all modules.",
        "Official Submission Package: Uploaded to the competition portal prior to 23:59 PKT on 31st October 2026."
    ]
    for item in check_items:
        cp = doc.add_paragraph(style='List Bullet')
        cp.paragraph_format.space_after = Pt(3)
        cp.paragraph_format.line_spacing = 1.15
        r_box = cp.add_run("[X]  "); r_box.bold = True; r_box.font.color.rgb = ACCENT
        r_txt = cp.add_run(item)

    doc.save(filepath)
    print(f"[SUCCESS] Saved DOCX: {filepath}")


# ─────────────────────────────────────────────────────────────
# BUILD PDF: DELIVERABLE 1
# ─────────────────────────────────────────────────────────────
def build_doc1_pdf(filepath):
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Custom Styles
    style_meta = ParagraphStyle(
        'MetaTag',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#00A8E8"),
        spaceAfter=4
    )
    style_title = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0B2545"),
        spaceAfter=6
    )
    style_subtitle = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#134074"),
        spaceAfter=12
    )
    style_h1 = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#0B2545"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    style_h2 = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=13,
        textColor=colors.HexColor("#134074"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )
    style_body = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=5
    )
    style_bullet = ParagraphStyle(
        'Bullet_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1E293B"),
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=3
    )
    style_callout = ParagraphStyle(
        'Callout_Text',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#1E293B")
    )
    style_tbl_cell = ParagraphStyle(
        'Tbl_Cell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#1E293B")
    )
    style_tbl_hdr = ParagraphStyle(
        'Tbl_Hdr',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10.5,
        textColor=colors.white
    )

    elements = []

    # Title & Header
    elements.append(Paragraph("ISSSP 2026 — TRACK 3: LUNAR SURFACE ROBOTICS · FINALS SCORING CRITERION 1", style_meta))
    elements.append(Paragraph("Community Building & Publicity Campaign Guide", style_title))
    elements.append(Paragraph(
        "Comprehensive Strategy, Outreach Blueprint, Communications Specialist Playbook, "
        "Ready-to-Publish Copy & Team Collaboration Charter (Deadline: 31st Oct — Max Score: 10/10)",
        style_subtitle
    ))

    # Meta Table
    meta_table_data = [
        [Paragraph("<b>Project:</b> L-MINER Mk-II Autonomous Payload", style_tbl_cell),
         Paragraph("<b>Institution:</b> IST Islamabad", style_tbl_cell)],
        [Paragraph("<b>Scoring Item:</b> Item 1: Community Building (10 Pts)", style_tbl_cell),
         Paragraph("<b>Team:</b> Haider, Wasay, Saad, Hajra", style_tbl_cell)]
    ]
    t_meta = Table(meta_table_data, colWidths=[240, 247])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(t_meta)
    elements.append(Spacer(1, 10))

    # Section 1
    elements.append(Paragraph("1. Strategic Alignment with Table 6 Finals Scoring Rules", style_h1))
    elements.append(Paragraph(
        "Table 6 allocates 10 points out of 100 to Item 1: Community Building (until 31st October). "
        "The scoring criteria are judged by the Organizing Committee and appointed evaluators on two specific dimensions:",
        style_body
    ))
    elements.append(Paragraph("• <b>Publicize Contest Concept (5 Points):</b> Actively promoting the contest vision, themes, and societal impact across university communities, social channels, and youth STEM forums. Demonstrates public engagement, reach, and advocacy for lunar science.", style_bullet))
    elements.append(Paragraph("• <b>Team Cooperation & Communication (5 Points):</b> Demonstrating cohesive interdisciplinary teamwork, transparent task allocation, systematic meeting logs, and structured communications leadership led by a designated Communications Specialist.", style_bullet))

    # Callout 1
    callout_data = [[
        Paragraph("<b>Judge Evaluation Mandate:</b> To secure the maximum 10/10 score, the team must provide empirical evidence of outreach reach (impressions, shares, comments), active tagging of the organizing committee, and structured agile collaboration records submitted before the 31st October deadline.", style_callout)
    ]]
    t_call1 = Table(callout_data, colWidths=[487])
    t_call1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0F9FF")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#BAE6FD")),
        ('LINELEFT', (0,0), (0,-1), 3, colors.HexColor("#00A8E8")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(Spacer(1, 4))
    elements.append(t_call1)
    elements.append(Spacer(1, 8))

    # Section 2
    elements.append(Paragraph("2. Four-Phase Campaign Roadmap (Until 31st October)", style_h1))
    phase_table_data = [
        [Paragraph("Phase & Dates", style_tbl_hdr), Paragraph("Strategic Focus", style_tbl_hdr), Paragraph("Deliverables & Activities", style_tbl_hdr), Paragraph("Target KPIs", style_tbl_hdr)],
        [Paragraph("<b>Phase 1: Concept Launch</b><br/>(Oct 15 – Oct 19)", style_tbl_cell),
         Paragraph("Publicize contest concept & mission debut.", style_tbl_cell),
         Paragraph("• Official competition announcement<br/>• Contest vision infogram<br/>• Mission logo & rover teaser render", style_tbl_cell),
         Paragraph("500+ Impressions<br/>50+ Engagements<br/>10 University Shares", style_tbl_cell)],
        [Paragraph("<b>Phase 2: Tech Deep-Dive</b><br/>(Oct 20 – Oct 24)", style_tbl_cell),
         Paragraph("Lunar South Pole science & autonomy outreach.", style_tbl_cell),
         Paragraph("• Carousel: 'Why is Lunar Ice Hard to Find?'<br/>• GPR vs Spectrometer explainer<br/>• Tag contest organizers", style_tbl_cell),
         Paragraph("800+ Impressions<br/>150+ Swipes<br/>5 Club Reposts", style_tbl_cell)],
        [Paragraph("<b>Phase 3: Interactive Demo</b><br/>(Oct 25 – Oct 28)", style_tbl_cell),
         Paragraph("Community engagement with 3D digital twin.", style_tbl_cell),
         Paragraph("• 45s screen capture reel of 3D Payload HUD & Mobile Simulation<br/>• Community poll on lunar resources<br/>• Live Q&A in comments", style_tbl_cell),
         Paragraph("1,200+ Impressions<br/>100+ Poll votes<br/>30+ Comments", style_tbl_cell)],
        [Paragraph("<b>Phase 4: Final Sprint</b><br/>(Oct 29 – Oct 31)", style_tbl_cell),
         Paragraph("Team cooperation showcase & competition eve.", style_tbl_cell),
         Paragraph("• Team Spotlight: Meet the 4 Engineers<br/>• Behind-the-scenes lab/code photos<br/>• Final contest tribute post", style_tbl_cell),
         Paragraph("1,500+ Total Reach<br/>Complete Dossier<br/>100% On-Time", style_tbl_cell)]
    ]
    t_phase = Table(phase_table_data, colWidths=[100, 115, 162, 110])
    t_phase.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0B2545")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#F8FAFC"), colors.white]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(t_phase)
    elements.append(Spacer(1, 10))

    # Section 3
    elements.append(Paragraph("3. Communications Specialist Playbook & Role Distribution", style_h1))
    elements.append(Paragraph(
        "Table 6 explicitly identifies the 'Communications Specialist' as a key evaluated element. "
        "The Communications Specialist leads external dissemination while each team member contributes domain copy.",
        style_body
    ))
    roles_table_data = [
        [Paragraph("Team Member", style_tbl_hdr), Paragraph("Primary Technical Role", style_tbl_hdr), Paragraph("Outreach & Communications Responsibility", style_tbl_hdr)],
        [Paragraph("<b>Hajra</b>", style_tbl_cell), Paragraph("UI / Dashboard Lead", style_tbl_cell), Paragraph("<b>Lead Communications Specialist:</b> Manages social postings, graphics generation, community replies, and press communication.", style_tbl_cell)],
        [Paragraph("<b>Haider Taqvee</b>", style_tbl_cell), Paragraph("Sensor Physics Lead", style_tbl_cell), Paragraph("<b>Science Writer:</b> Drafts plain-language explanations of GPR dielectric physics and USGS spectroscopy for public posts.", style_tbl_cell)],
        [Paragraph("<b>Abdul Wasay</b>", style_tbl_cell), Paragraph("Machine Learning Lead", style_tbl_cell), Paragraph("<b>Data Viz Lead:</b> Generates high-resolution confusion matrices, ROC plots, and benchmark graphics for carousels.", style_tbl_cell)],
        [Paragraph("<b>Saad</b>", style_tbl_cell), Paragraph("Autonomy Systems Lead", style_tbl_cell), Paragraph("<b>Documentation Officer:</b> Maintains meeting minutes, GitHub project board, attendance records, and collaboration proof.", style_tbl_cell)]
    ]
    t_roles = Table(roles_table_data, colWidths=[90, 110, 287])
    t_roles.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#134074")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#F8FAFC"), colors.white]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(t_roles)
    elements.append(Spacer(1, 10))

    # Section 4: Ready Copy
    elements.append(Paragraph("4. Ready-to-Publish Outreach Assets & Copy", style_h1))
    
    # LinkedIn Post Callout
    elements.append(Paragraph("<b>Asset 1: LinkedIn Launch Post Copy (Phase 1)</b>", style_h2))
    p1 = (
        "<b>🚀 Exciting News from IST Islamabad!</b><br/>"
        "Our team is thrilled to participate in ISSSP 2026 Track 3 (Lunar Surface Robotics & Autonomous Exploration)! 🌙<br/><br/>"
        "As humanity prepares to establish sustainable bases on the Moon through Artemis and international lunar research programs, "
        "one question remains paramount: How do we locate volatile water ice trapped inside permanently shadowed craters at 40 Kelvin?<br/><br/>"
        "Introducing <b>L-MINER Mk-II:</b> An Autonomous Multi-Tier Rover for Subsurface Lunar Mineral Classification.<br/>"
        "Equipped with 500 MHz Ground Penetrating Radar, 0.5–2.5 μm VNIR-SWIR Reflectance Spectroscopy, and edge Random Forest ML, "
        "L-MINER's autonomous payload firmware navigates hazards, monitors power, and maps resources without Earth teleoperation lag.<br/><br/>"
        "Proud to represent IST alongside teammates Haider Taqvee, Abdul Wasay, Saad, and Hajra. Follow our journey before Oct 31st!<br/>"
        "<i>#ISSSP2026 #LunarExploration #SpaceRobotics #ISTIslamabad #MoonToMars #ISRU #AutonomousSystems</i>"
    )
    t_p1 = Table([[Paragraph(p1, style_callout)]], colWidths=[487])
    t_p1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0F9FF")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#BAE6FD")),
        ('LINELEFT', (0,0), (0,-1), 3, colors.HexColor("#00A8E8")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(t_p1)
    elements.append(Spacer(1, 8))

    # Twitter Thread Callout
    elements.append(Paragraph("<b>Asset 2: Twitter/X Technical Explainer Thread (Phase 2)</b>", style_h2))
    p2 = (
        "🧵 <b>1/5</b> How does an autonomous science payload 'see' water ice buried 2 meters under lunar dust? Here's how our project for #ISSSP2026 Track 3 works! 👇<br/>"
        "<b>2/5</b> Optical cameras only see the top 10 microns of dust. That's why L-MINER Mk-II combines TWO complementary sensors: "
        "an underbelly 500 MHz GPR (for depth) + a robotic-arm VNIR-SWIR Spectrometer (for chemistry). 📡🔬<br/>"
        "<b>3/5</b> Water ice has a sharp dielectric boundary (ε_r ≈ 3.1) vs dry regolith, creating high-amplitude radar echoes. "
        "Spectroscopically, it reveals diagnostic absorption troughs at 1.25, 1.5, and 2.0 μm (matching Chandrayaan-1 M³ data)! ❄️<br/>"
        "<b>4/5</b> Our edge Random Forest model extracts a 10-D feature vector, compressing 32,000+ raw data points into instant classification "
        "with 95%+ accuracy in under 15 ms! ⚡<br/>"
        "<b>5/5</b> Huge thanks to the ISSSP 2026 organizing committee for inspiring student aerospace innovation! Stay tuned for our 3D Digital Twin demo! 🚀"
    )
    t_p2 = Table([[Paragraph(p2, style_callout)]], colWidths=[487])
    t_p2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('LINELEFT', (0,0), (0,-1), 3, colors.HexColor("#134074")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(t_p2)
    elements.append(Spacer(1, 10))

    # Section 5: Team Cooperation Protocol
    elements.append(Paragraph("5. Team Cooperation & Internal Communication Protocol", style_h1))
    elements.append(Paragraph(
        "To provide empirical proof of 'Team cooperation & communication' (Table 6, Item 1), "
        "the team instituted a formal Agile/Scrum collaboration framework documented through GitHub, Discord, and Trello.",
        style_body
    ))
    collab_table_data = [
        [Paragraph("Pillar", style_tbl_hdr), Paragraph("Tools Used", style_tbl_hdr), Paragraph("Operational Protocol & Artifacts", style_tbl_hdr)],
        [Paragraph("<b>Daily Standups</b>", style_tbl_cell), Paragraph("Discord / Meet", style_tbl_cell), Paragraph("15-minute daily sync at 18:00 PKT. Agenda: Completed items, blockers, next sprint tasks. Minutes logged.", style_tbl_cell)],
        [Paragraph("<b>Version Control</b>", style_tbl_cell), Paragraph("GitHub Repo", style_tbl_cell), Paragraph("Strict PR reviews. Dedicated modules for data_generator, model, l0_l1_logic, and dashboard.", style_tbl_cell)],
        [Paragraph("<b>Sprint Tracking</b>", style_tbl_cell), Paragraph("Trello Board", style_tbl_cell), Paragraph("Kanban swimlanes tied directly to Table 6 deliverables. Individual assignee tags.", style_tbl_cell)],
        [Paragraph("<b>Deliverable Archive</b>", style_tbl_cell), Paragraph("Google Drive", style_tbl_cell), Paragraph("Centralized repository for poster assets, slide decks, and code builds.", style_tbl_cell)]
    ]
    t_collab = Table(collab_table_data, colWidths=[90, 85, 312])
    t_collab.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0B2545")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#F8FAFC"), colors.white]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(t_collab)
    elements.append(Spacer(1, 10))

    # Section 6: Checklist
    elements.append(Paragraph("6. Evidence Submission Checklist for Judges (Before 31st Oct)", style_h1))
    checks = [
        "<b>[X] Publicity Posts Live:</b> Links and screenshots of LinkedIn, Twitter/X, and Instagram posts tagging the competition.",
        "<b>[X] Engagement Metric Sheet:</b> Total views, impressions, reposts, and student comments compiled into an appendix.",
        "<b>[X] Team Standup Logs:</b> 14 consecutive daily meeting minute summaries signed off by all four team members.",
        "<b>[X] GitHub Contribution Matrix:</b> Multi-author commit frequency proving active collaboration across all modules.",
        "<b>[X] Official Submission Package:</b> Uploaded to the competition portal prior to 23:59 PKT on 31st October 2026."
    ]
    for c in checks:
        elements.append(Paragraph(f"• {c}", style_bullet))

    doc.build(elements, canvasmaker=NumberedCanvas)
    print(f"[SUCCESS] Saved PDF: {filepath}")


if __name__ == "__main__":
    out_dir = r"E:\L-miner directory\Finals_Track3_Deliverables"
    os.makedirs(out_dir, exist_ok=True)
    docx_path = os.path.join(out_dir, "1_Community_Building_Guide.docx")
    pdf_path = os.path.join(out_dir, "1_Community_Building_Guide.pdf")
    build_doc1_docx(docx_path)
    build_doc1_pdf(pdf_path)
