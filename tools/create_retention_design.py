#!/usr/bin/env python3
"""Create a graphical retention and assembly design document."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import create_scale_drawing as scale_drawing  # noqa: E402


PAGE_W, PAGE_H = landscape(A4)
INK = colors.HexColor("#263238")
MUTED = colors.HexColor("#607d8b")
BLUE = colors.HexColor("#1565c0")
LCD = colors.HexColor("#b3e5fc")
PCB = colors.HexColor("#a5d6a7")
PART = colors.HexColor("#eceff1")
RETAINER = colors.HexColor("#ffe0b2")
FIXED = colors.HexColor("#ffb74d")
FLEX = colors.HexColor("#ef9a9a")
STOP = colors.HexColor("#ce93d8")
WARN = colors.HexColor("#c62828")
REFERENCE = colors.HexColor("#ef6c00")
TOTAL_PAGES = 10


def u(value: float) -> float:
    return value * mm


def label(c: Canvas, x: float, y: float, text: str, size=7.0,
          color=INK, align="left", font="DejaVu") -> None:
    c.saveState()
    c.setFillColor(color)
    c.setFont(font, size)
    draw = {"left": c.drawString, "center": c.drawCentredString,
            "right": c.drawRightString}[align]
    draw(u(x), u(y), text)
    c.restoreState()


def line(c: Canvas, x0: float, y0: float, x1: float, y1: float,
         color=INK, width=0.4, dash=None) -> None:
    c.saveState()
    c.setStrokeColor(color)
    c.setLineWidth(width)
    if dash:
        c.setDash(*dash)
    c.line(u(x0), u(y0), u(x1), u(y1))
    c.restoreState()


def rect(c: Canvas, x: float, y: float, w: float, h: float,
         fill=None, stroke=INK, width=0.4, dash=None, radius=0.0) -> None:
    c.saveState()
    c.setStrokeColor(stroke)
    c.setLineWidth(width)
    if dash:
        c.setDash(*dash)
    if fill is not None:
        c.setFillColor(fill)
    if radius:
        c.roundRect(u(x), u(y), u(w), u(h), u(radius),
                    stroke=1, fill=int(fill is not None))
    else:
        c.rect(u(x), u(y), u(w), u(h), stroke=1, fill=int(fill is not None))
    c.restoreState()


def arrow(c: Canvas, x0: float, y0: float, x1: float, y1: float,
          color=BLUE, width=0.7) -> None:
    import math
    line(c, x0, y0, x1, y1, color, width)
    angle = math.atan2(y1 - y0, x1 - x0)
    for delta in (-0.5, 0.5):
        line(c, x1, y1, x1 - 2.5 * math.cos(angle + delta),
             y1 - 2.5 * math.sin(angle + delta), color, width)


def paragraph(c: Canvas, x: float, y: float, lines: tuple[str, ...],
              size=7.0, leading=5.5, color=INK) -> float:
    for index, text in enumerate(lines):
        label(c, x, y - index * leading, text, size, color)
    return y - len(lines) * leading


def header(c: Canvas, page: int, title: str, subtitle: str) -> None:
    rect(c, 7, 7, 283, 196, width=0.55)
    label(c, 12, 195.5, title, 14)
    label(c, 12, 189.5, subtitle, 7.2, MUTED)
    label(c, 285, 195.5, f"RETENTION DESIGN  REV 4  |  {page}/{TOTAL_PAGES}",
          7, INK, "right")
    line(c, 7, 185.5, 290, 185.5, INK, 0.55)
    label(c, 12, 10.2,
          "Tang Nano 9K: 70.00 x 26.00 mm | LCD reference: HT043DA-V.0 105.50 x 67.15 x 2.90 mm",
          6.5, MUTED)


def table(c: Canvas, x: float, y: float, widths: tuple[float, ...],
          rows: tuple[tuple[str, ...], ...], row_h=9.0) -> None:
    total_w = sum(widths)
    for r, row in enumerate(rows):
        top = y - r * row_h
        fill = INK if r == 0 else (colors.white if r % 2 else PART)
        rect(c, x, top - row_h, total_w, row_h, fill=fill,
             stroke=colors.HexColor("#90a4ae"), width=0.3)
        cursor = x
        for i, (cell, width) in enumerate(zip(row, widths)):
            if i:
                line(c, cursor, top - row_h, cursor, top,
                     colors.HexColor("#90a4ae"), 0.3)
            label(c, cursor + 2.0, top - 5.8, cell, 6.2,
                  colors.white if r == 0 else INK)
            cursor += width


def page_overview(c: Canvas) -> None:
    header(c, 1, "Retention system overview",
           "Each internal item remains retained when the rear cover is removed")

    # Exploded stack schematic.
    x, y = 18.0, 147.0
    rect(c, x, y, 116, 7, fill=PART)
    label(c, x + 58, y + 2.2, "FRONT CHASSIS", 6.5, align="center")
    arrow(c, x + 58, y - 2, x + 58, y - 12)
    rect(c, x + 6, y - 27, 104, 6, fill=LCD)
    label(c, x + 58, y - 24.8, "LCD", 6.5, align="center")
    arrow(c, x + 58, y - 31, x + 58, y - 41)
    rect(c, x + 5, y - 56, 106, 7, fill=RETAINER)
    for hx in (x + 5, x + 109):
        rect(c, hx, y - 53, 2, 10, fill=FIXED)
    label(c, x + 58, y - 53.8, "4-HOOK LCD RETAINER", 6.5, align="center")
    arrow(c, x + 58, y - 60, x + 58, y - 70)
    rect(c, x + 44, y - 89, 28, 14, fill=PCB, radius=1.5)
    label(c, x + 58, y - 83.8, "PCB", 6.5, align="center")
    rect(c, x + 2, y - 101, 112, 7, fill=PART)
    label(c, x + 58, y - 98.8, "REAR COVER + PCB CARRIER", 6.2, align="center")

    label(c, 158, 169, "REVISION 4 CONTENT", 9)
    paragraph(c, 158, 158, (
        "1. LCD retainer snaps directly into chassis at four points.",
        "2. Rear-cover pressure posts are removed.",
        "3. PCB uses a fixed guide on one edge and two flex clips on the other.",
        "4. Four axial stops resist USB-C and HDMI insertion loads.",
        "5. Rear cover, PCB carrier, LCD retainer, and panel clips are independent.",
        "6. Exact STL-derived A-A to E-E assembly sections are included.",
        "7. HDMI-end two-hole M2 bosses and 20/30 mm deep covers are added.",
    ), 6.7, 7.0)

    table(c, 151, 101, (43, 46, 43), (
        ("ITEM", "PRIMARY RETENTION", "STATE WITH COVER OFF"),
        ("LCD", "4 retainer hooks", "Retained"),
        ("Tang Nano 9K", "fixed guide + 2 clips", "Retained on cover"),
        ("Rear cover", "4 chassis latches", "Removed as one unit"),
        ("Panel case", "4 panel snap arms", "Retained in panel"),
    ), 10.0)

    label(c, 151, 41, "DESIGN INTENT", 8)
    paragraph(c, 151, 32, (
        "No loose internal part is allowed after each assembly stage.",
        "Connector service loads must be reacted by printed stops, not only solder joints.",
        "Snap features are serviceable from the rear without pulling the LCD FPC.",
    ), 6.6, 6.3)
    c.showPage()


def page_lcd(c: Canvas) -> None:
    header(c, 2, "LCD retainer fixation",
           "Four independent cantilever hooks engage chassis side-wall windows")

    # Rear view, approximately 1:1.
    x, y = 18.0, 84.0
    rect(c, x, y, 107.6, 70.6, fill=RETAINER)
    rect(c, x + 5.3, y + 7.3, 97.0, 56.0, fill=colors.white)
    rect(c, x + 41.3, y + 63.3, 25, 7.5, fill=colors.white)
    for cy in (12.0, 58.0):
        rect(c, x - 0.6, y + cy - 3, 1.8, 6, fill=FIXED)
        rect(c, x + 106.4, y + cy - 3, 1.8, 6, fill=FIXED)
    label(c, x + 53.8, y + 34, "RETAINER REAR VIEW", 7, align="center")
    label(c, x + 53.8, y - 7, "107.60 x 70.60 mm", 6.5, BLUE, "center")

    # Enlarged hook section.
    label(c, 154, 166, "HOOK SECTION - 4:1 SCHEMATIC", 8)
    base_x, base_y = 164.0, 91.0
    rect(c, base_x, base_y, 8, 50, fill=RETAINER)
    # Three-step head.
    rect(c, base_x - 4, base_y + 29, 12, 6, fill=FIXED)
    rect(c, base_x - 8, base_y + 35, 16, 6, fill=FIXED)
    rect(c, base_x - 12, base_y + 41, 20, 6, fill=FIXED)
    rect(c, base_x - 14, base_y + 37, 6, 14, fill=PART, stroke=MUTED)
    label(c, base_x - 11, base_y + 53, "CHASSIS WINDOW", 6.2, MUTED)
    arrow(c, base_x - 24, base_y + 22, base_x - 4, base_y + 22)
    label(c, base_x - 25, base_y + 15, "DEFLECT INWARD", 6.2, BLUE)

    table(c, 205, 155, (40, 35), (
        ("FEATURE", "VALUE"),
        ("Arm thickness", "1.20 mm"),
        ("Arm width", "6.00 mm"),
        ("Overall height", "6.50 mm"),
        ("Free length", "about 4.50 mm"),
        ("Max engagement", "0.60 mm"),
        ("Hook count", "4"),
    ), 9.0)

    label(c, 151, 66, "ASSEMBLY", 8)
    paragraph(c, 151, 57, (
        "- Place LCD with the display toward the bezel and FPC toward the relief.",
        "- Push the retainer forward until all four hooks click into the windows.",
        "- Confirm the retainer remains installed without the rear cover.",
        "- To remove, press both hooks on one side inward and lift that edge.",
    ), 6.7, 7.0)

    label(c, 151, 24, "LOAD LIMIT", 8, WARN)
    label(c, 151, 16.5,
          "The retainer contacts only the LCD perimeter. Do not preload the active area.",
          6.6, WARN)
    c.showPage()


def draw_board_carrier(c: Canvas, x: float, y: float, scale=1.0) -> None:
    w, h = 111.6 * scale, 74.6 * scale
    rect(c, x, y, w, h, fill=PART)
    bx = x + (111.6 - 26.0) / 2 * scale
    by = y + (74.6 - 70.0) / 2 * scale
    bw, bh = 26.0 * scale, 70.0 * scale
    rect(c, bx, by, bw, bh, fill=PCB, radius=1.5 * scale)
    for y0, y1 in ((by + 9 * scale, by + 28 * scale),
                   (by + 42 * scale, by + 61 * scale)):
        rect(c, bx - 1.0 * scale, y0, 1.8 * scale, y1 - y0, fill=FIXED)
        rect(c, bx + bw - 0.8 * scale, y0, 2.0 * scale, y1 - y0, fill=FLEX)
    for sx in (bx + 4.5 * scale, bx + 18.5 * scale):
        rect(c, sx, by - 0.6 * scale, 3 * scale, 0.6 * scale, fill=STOP)
        rect(c, sx, by + bh, 3 * scale, 0.6 * scale, fill=STOP)
    label(c, bx + bw / 2, by + bh + 3, "HDMI", 5.8, align="center")
    label(c, bx + bw / 2, by - 5, "USB-C", 5.8, align="center")


def page_pcb(c: Canvas) -> None:
    header(c, 3, "Tang Nano 9K carrier",
           "Fixed-edge insertion, two snap clips, and axial connector-load stops")
    draw_board_carrier(c, 18, 87, 1.0)
    label(c, 18, 169, "REAR COVER - INBOARD VIEW", 8)
    label(c, 18, 78, "Orange: fixed guide | Red: flex clips | Purple: axial stops", 6.5)

    label(c, 151, 169, "INSTALLATION SEQUENCE", 8)
    # Cross-section stages.
    for index, (title, angle) in enumerate((("1  INSERT FIXED EDGE", True),
                                             ("2  PRESS SNAP EDGE", False))):
        y = 127 - index * 53
        rect(c, 160, y, 90, 8, fill=PART)
        rect(c, 170, y + 8, 8, 30, fill=FIXED)
        rect(c, 232, y + 8, 8, 30, fill=FLEX)
        if angle:
            c.saveState()
            c.translate(u(179), u(y + 18))
            c.rotate(-8)
            c.setFillColor(PCB)
            c.setStrokeColor(INK)
            c.rect(0, 0, u(54), u(5), stroke=1, fill=1)
            c.restoreState()
            arrow(c, 218, y + 34, 228, y + 20)
        else:
            rect(c, 178, y + 18, 54, 5, fill=PCB)
            arrow(c, 229, y + 37, 229, y + 25)
        label(c, 255, y + 20, title, 6.5)

    table(c, 18, 65, (50, 38, 42), (
        ("FEATURE", "VALUE", "PURPOSE"),
        ("Side clearance", "0.25 mm/side", "FDM fit allowance"),
        ("Axial clearance", "0.30 mm/end", "prevents rattle"),
        ("Support height", "7.00 mm", "component clearance"),
        ("Clip thickness", "1.20 mm", "serviceable flexure"),
        ("Clip engagement", "0.55 mm max", "vertical retention"),
        ("End-stop count", "2 per end", "connector load path"),
    ), 8.0)
    label(c, 151, 43, "REMOVAL", 8)
    paragraph(c, 151, 34, (
        "Deflect both red clips outward, lift the right PCB edge, then slide the left",
        "edge out from under the fixed lips. Do not lever against the HDMI or USB-C shell.",
    ), 6.6, 6.2)
    c.showPage()


def step_box(c: Canvas, x: float, y: float, number: str, title: str,
             details: tuple[str, ...], accent) -> None:
    rect(c, x, y, 128, 68, fill=colors.white,
         stroke=colors.HexColor("#90a4ae"), width=0.5)
    rect(c, x, y + 56, 128, 12, fill=accent, stroke=accent)
    label(c, x + 5, y + 60, f"{number}  {title}", 8)
    paragraph(c, x + 6, y + 47, details, 6.6, 7.0)


def page_assembly(c: Canvas) -> None:
    header(c, 4, "Assembly and service sequence",
           "Every stage ends with all installed parts positively retained")
    step_box(c, 14, 108, "1", "PANEL + LCD", (
        "Select the chassis variant matching panel thickness.",
        "Install chassis into the panel cutout.",
        "Place LCD with FPC toward the bottom relief.",
    ), PART)
    step_box(c, 155, 108, "2", "LOCK LCD RETAINER", (
        "Align the retainer FPC relief.",
        "Press until all four side hooks click.",
        "Invert gently: LCD and retainer must remain installed.",
    ), RETAINER)
    step_box(c, 14, 31, "3", "LOCK PCB TO COVER", (
        "Insert left PCB edge under the fixed orange lips.",
        "Press the right edge below both red snap clips.",
        "Confirm both ends sit between the purple stops.",
    ), PCB)
    step_box(c, 155, 31, "4", "CONNECT + CLOSE", (
        "Connect the LCD FPC without twisting it.",
        "Orient HDMI top and USB-C bottom.",
        "Engage all four rear-cover latches.",
        "Removal is the reverse order; release clips before pulling.",
    ), colors.HexColor("#cfd8dc"))
    arrow(c, 142, 142, 153, 142)
    arrow(c, 155, 108, 142, 99)
    arrow(c, 142, 65, 153, 65)
    c.showPage()


def page_validation(c: Canvas) -> None:
    header(c, 5, "Tolerance, material, and validation",
           "Prototype verification is required before permanent panel machining")

    table(c, 14, 169, (55, 55, 62, 85), (
        ("TEST", "METHOD", "PASS CRITERION", "RATIONALE"),
        ("LCD retention", "invert without cover", "no release or movement", "retainer is independently locked"),
        ("PCB retention", "invert cover only", "no release or movement", "carrier retains PCB during service"),
        ("Rattle", "manual shake", "no impact sound", "clearances and stops are effective"),
        ("USB-C cycling", "10 insert/remove cycles", "no clip or PCB shift", "end stops carry service load"),
        ("HDMI cycling", "10 insert/remove cycles", "no clip or PCB shift", "end stops carry service load"),
        ("Cover cycling", "5 open/close cycles", "all 4 latches retain", "serviceability check"),
        ("FPC inspection", "open after cycling", "no crease or pinch marks", "cable routing remains safe"),
    ), 10.5)

    label(c, 14, 68, "PRINT BASELINE", 8)
    paragraph(c, 14, 59, (
        "Material: PETG preferred | Nozzle: 0.4 mm | Layer: 0.20 mm | Perimeters: 4",
        "PLA is acceptable for a fit prototype but not recommended for repeated snap cycling.",
        "Calibrate elephant-foot and horizontal-hole compensation before changing CAD clearances.",
    ), 6.7, 7.0)

    label(c, 151, 68, "UNVERIFIED HARDWARE VALUES", 8, WARN)
    paragraph(c, 151, 59, (
        "- USB-C and HDMI shell projection and maximum assembled component height",
        "- LCD FPC tail geometry if the module is not HT043DA-V.0",
        "- Effective snap force for the user's printer, material, and print orientation",
        "The first print is a fit prototype. Do not machine the final panel before this check.",
    ), 6.7, 7.0, WARN)
    c.showPage()


def page_section_index(c: Canvas) -> None:
    header(c, 6, "Exact assembly section index",
           "Five cuts intentionally cross the connector, PCB clip, LCD hook, microSD aperture, and M2 bosses")
    x0, y0 = 20.0, 84.0
    scale_drawing.draw_front_chassis(c, x0, y0)
    board_x = x0 + (118.0 - 26.0) / 2.0
    rect(c, board_x, y0 + 5.5, 26.0, 70.0,
         stroke=MUTED, dash=(3, 2), radius=2.0)
    ax = x0 + 53.20
    line(c, ax, y0 - 4.0, ax, y0 + 85.0, WARN, 0.7, (5, 2))
    label(c, ax, y0 + 87.0, "A", 7, WARN, "center", "Helvetica")
    label(c, ax, y0 - 7.0, "A", 7, WARN, "center", "Helvetica")
    for code, yy in (("C", 17.20), ("B", 25.00), ("D", 40.50), ("E", 72.90)):
        sy = y0 + yy
        line(c, x0 - 4.0, sy, x0 + 122.0, sy, BLUE, 0.65, (5, 2))
        label(c, x0 - 6.0, sy - 1.0, code, 7, BLUE, "center", "Helvetica")
        label(c, x0 + 124.0, sy - 1.0, code, 7, BLUE, "center", "Helvetica")

    label(c, 164.0, 169.0, "CUT DEFINITIONS", 9)
    descriptions = (
        ("A-A @ X=53.20", "connector openings + PCB end stops + FPC route"),
        ("B-B @ Y=25.00", "PCB support shelves + fixed lip + flex clip"),
        ("C-C @ Y=17.20", "four-hook pair plane + chassis engagement windows"),
        ("D-D @ Y=40.50", "microSD service aperture + rear clearance"),
        ("E-E @ Y=72.90", "two HDMI-end M2 bosses + pilot bores"),
    )
    for index, (name, detail) in enumerate(descriptions):
        yy = 154.0 - index * 20.0
        label(c, 164.0, yy, name, 7.0, WARN if index == 0 else BLUE,
              font="Helvetica")
        label(c, 164.0, yy - 7.0, detail, 6.1, MUTED, font="Helvetica")
    label(c, 164.0, 55.0, "DRAWING CONTRACT", 8)
    paragraph(c, 164.0, 45.0, (
        "Filled section cells come from the same rectilinear CSG as the STL meshes.",
        "Dashed orange outlines are electronics reference envelopes, not CAD-certified parts.",
        "A blank area can be a deliberate display, latch, connector, or service opening.",
    ), 6.3, 7.0)
    c.showPage()


def page_expanded_covers(c: Canvas) -> None:
    header(c, 9, "20 mm and 30 mm expansion covers",
           "E-E crosses both HDMI-end screw bosses while PCB and connector planes remain fixed")
    x20, y20 = 18.0, 118.0
    scale_drawing.draw_exact_section(
        c, "E-E", x20, y20, rear_clearance=20.0
    )
    label(c, x20 + 59.0, y20 + 48.0,
          "20 mm REAR CLEARANCE / OVERALL DEPTH 42.00 / SCALE 1:1",
          7, align="center", font="Helvetica")

    x30, y30 = 18.0, 32.0
    scale_drawing.draw_exact_section(
        c, "E-E", x30, y30, rear_clearance=30.0
    )
    label(c, x30 + 59.0, y30 + 58.0,
          "30 mm REAR CLEARANCE / OVERALL DEPTH 52.00 / SCALE 1:1",
          7, align="center", font="Helvetica")

    label(c, 154.0, 169.0, "INVARIANT DATUMS", 8)
    paragraph(c, 154.0, 159.0, (
        "PCB front/rear surfaces remain z=18.40/20.00 mm.",
        "USB-C and HDMI openings remain at the original chassis locations.",
        "Only the rear shell, carrier columns, and cover plate move rearward.",
        "This preserves connector alignment for both expansion variants.",
    ), 6.3, 7.0)
    label(c, 154.0, 119.0, "M2 FIXATION", 8)
    paragraph(c, 154.0, 109.0, (
        "Two bosses align with the two Tang Nano 9K holes at the HDMI end.",
        "The snap lips and clips remain, so screws are optional.",
        "Recommended: M2x8 self-tapping screw, tightened without PCB bowing.",
        "Blue dashed shafts are hardware references; grey features are STL geometry.",
    ), 6.3, 7.0)
    label(c, 154.0, 67.0, "EXPANSION HOLD POINTS", 8, WARN)
    paragraph(c, 154.0, 57.0, (
        "Verify daughterboard outline, pin-header height, FPC bend radius,",
        "and connector cable bend space before selecting the 20 or 30 mm cover.",
    ), 6.3, 7.0, WARN)
    c.showPage()


def page_m2_layout(c: Canvas) -> None:
    header(c, 10, "Tang Nano 9K two-hole mounting specification",
           "Only the HDMI-end hole pair is used; no USB-C-end mounting holes are assumed")
    x0, y0 = 23.0, 88.0
    rect(c, x0, y0, 111.6, 74.6, fill=PART)
    bx = x0 + (111.6 - 26.0) / 2.0
    by = y0 + (74.6 - 70.0) / 2.0
    hole_y = by + 70.0 - 2.6
    hole_xs = (bx + 2.6, bx + 26.0 - 2.6)
    for hx in hole_xs:
        rect(c, hx - 3.0, hole_y - 3.0, 6.0, 6.0,
             fill=colors.HexColor("#bbdefb"), stroke=BLUE)
    rect(c, bx, by, 26.0, 70.0, stroke=colors.HexColor("#2e7d32"),
         dash=(4, 2), radius=2.0)
    c.saveState()
    c.setStrokeColor(INK)
    c.setFillColor(colors.white)
    for hx in hole_xs:
        c.circle(u(hx), u(hole_y), u(1.1), stroke=1, fill=1)
    c.restoreState()
    label(c, x0 + 55.8, 169.0, "REAR-COVER INBOARD VIEW / SCALE 1:1",
          7, align="center", font="Helvetica")
    label(c, x0 + 55.8, 79.0,
          "Blue: 6 mm bosses | Green dashed: PCB | HDMI end at top",
          6.3, align="center")

    table(c, 154.0, 169.0, (57.0, 61.0), (
        ("FEATURE", "VALUE"),
        ("PCB mounting holes", "2 at HDMI end"),
        ("Hole diameter ref.", "2.20 mm"),
        ("Hole-centre spacing", "20.80 mm"),
        ("Hole edge offset", "2.60 mm"),
        ("Printed boss", "6.00 x 6.00 mm"),
        ("Pilot bore", "1.70 x 1.70 mm"),
        ("Thread depth", "6.00 mm"),
        ("Screw", "M2x8 self-tapping"),
    ), 9.0)

    label(c, 154.0, 75.0, "ASSEMBLY CHECK", 8)
    paragraph(c, 154.0, 65.0, (
        "1. Seat the PCB under both fixed lips and flex clips.",
        "2. Check both hole centres against the printed pilots.",
        "3. Install both M2 screws evenly; stop before the PCB bends.",
        "4. Confirm the daughterboard does not contact the rear plate.",
    ), 6.3, 7.0)
    label(c, 154.0, 30.0,
          "Do not substitute a longer screw without checking remaining pilot depth.",
          6.3, WARN)
    c.showPage()


def page_sections_ab(c: Canvas) -> None:
    header(c, 7, "Exact sections A-A and B-B",
           "A-A resolves connectors/end stops; B-B proves that the PCB is supported and clipped")
    ax, ay = 20.0, 128.0
    scale_drawing.draw_exact_section(c, "A-A", ax, ay)
    label(c, ax + 40.5, ay + 33.0, "A-A  Y-Z  SCALE 1:1", 7,
          align="center", font="Helvetica")
    label(c, 113.0, 161.0, "A-A passes through:", 7.2)
    paragraph(c, 113.0, 151.0, (
        "- USB-C and HDMI chassis openings",
        "- one pair of axial PCB end stops",
        "- LCD / retainer / PCB / rear-cover stack",
        "- dashed component and connector reference envelopes",
        "- dashed FPC route corridor",
    ), 6.2, 7.0)
    scale_drawing.section_legend(c, 213.0, 158.0)

    bx, by = 20.0, 48.0
    scale_drawing.draw_exact_section(c, "B-B", bx, by)
    label(c, bx + 59.0, by + 33.0, "B-B  X-Z  SCALE 1:1", 7,
          align="center", font="Helvetica")
    label(c, 154.0, 75.0, "PCB support condition", 7.2)
    paragraph(c, 154.0, 65.0, (
        "The PCB bottom face sits at z=18.40 on four shelves.",
        "The left edge is below a fixed 0.55 mm lip.",
        "The right edge is retained by two 1.20 mm cantilevers.",
        "Therefore the green PCB section is not suspended in free space.",
    ), 6.3, 7.0)
    c.showPage()


def page_sections_cd(c: Canvas) -> None:
    header(c, 8, "Exact sections C-C and D-D",
           "C-C resolves the retainer hooks; D-D resolves the intentional microSD service opening")
    cx, cy = 18.0, 130.0
    scale_drawing.draw_exact_section(c, "C-C", cx, cy)
    label(c, cx + 59.0, cy + 33.0, "C-C  X-Z  SCALE 1:1", 7,
          align="center", font="Helvetica")
    zx, zy = 164.0, 119.0
    scale_drawing.draw_exact_section(c, "C-C", zx, zy, scale=4.0,
                                     clip_h=(0.0, 14.0), clip_z=(4.0, 15.0),
                                     show_reference_envelopes=False)
    label(c, zx + 28.0, zy + 48.0, "HOOK DETAIL 4:1", 7,
          align="center", font="Helvetica")
    label(c, zx, zy - 7.0, "Hook head z=10.60..12.40", 5.8)
    label(c, zx, zy - 13.0, "Window z=11.70..12.50", 5.8)

    dx, dy = 18.0, 49.0
    scale_drawing.draw_exact_section(c, "D-D", dx, dy)
    label(c, dx + 59.0, dy + 33.0, "D-D  X-Z  SCALE 1:1", 7,
          align="center", font="Helvetica")
    label(c, 153.0, 74.0, "The missing rear-cover plate below the PCB is intentional:", 6.5)
    label(c, 153.0, 66.0, "it is the 19.00 x 46.00 mm microSD service aperture.", 6.5)
    label(c, 153.0, 56.0, "The dashed socket outline is a reference envelope.", 6.4,
          REFERENCE)
    label(c, 153.0, 48.0, "Measure the physical socket before production printing.", 6.4,
          REFERENCE)
    c.showPage()


def create_pdf(output: Path) -> None:
    pdfmetrics.registerFont(TTFont(
        "DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    output.parent.mkdir(parents=True, exist_ok=True)
    c = Canvas(
        str(output), pagesize=landscape(A4), pageCompression=1, invariant=1
    )
    c.setTitle("Tang Nano 9K Panel Case Retention Design")
    c.setAuthor("OpenAI Codex")
    c.setSubject("Revision 4 M2 bosses, deep covers, exact sections, and snap retention")
    for page in (page_overview, page_lcd, page_pcb, page_assembly,
                 page_validation, page_section_index, page_sections_ab,
                 page_sections_cd, page_expanded_covers, page_m2_layout):
        page(c)
    c.save()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path,
                        default=Path("output/pdf/tang-nano-9k-panel-case-retention-design.pdf"))
    args = parser.parse_args()
    create_pdf(args.output)
    print(args.output)


if __name__ == "__main__":
    main()
