#!/usr/bin/env python3
"""Create rendered images, orthographic views, and a drawing PDF.

Inputs are the generated binary STL files.  Proxy solids for the LCD and PCB
are dimensionally derived from the same reference values as the case model and
are used only to explain the assembly.
"""

from __future__ import annotations

import argparse
import struct
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.platypus import Table, TableStyle


BEZEL_W = 118.0
BEZEL_H = 81.0
BEZEL_T = 3.0
BODY_W = 112.0
BODY_H = 75.0
BODY_D = 27.0
BODY_X = 3.0
BODY_Y = 3.0
WALL = 2.0

LCD_W = 105.5
LCD_H = 67.15
LCD_T = 2.9
LCD_ACTIVE_W = 95.04
LCD_ACTIVE_H = 53.856
LCD_ACTIVE_X = 5.18
LCD_ACTIVE_Y = 4.04

PCB_W = 26.0
PCB_H = 70.0
PCB_T = 1.6

WINDOW_MARGIN = 0.3
WINDOW_W = LCD_ACTIVE_W + WINDOW_MARGIN * 2
WINDOW_H = LCD_ACTIVE_H + WINDOW_MARGIN * 2
LCD_X = BODY_X + (BODY_W - LCD_W) / 2
LCD_Y = BODY_Y + (BODY_H - LCD_H) / 2
WINDOW_X = LCD_X + LCD_ACTIVE_X - WINDOW_MARGIN
WINDOW_Y = LCD_Y + LCD_ACTIVE_Y - WINDOW_MARGIN

PANEL_CUTOUT_W = 112.6
PANEL_CUTOUT_H = 75.6
# The rear cover is recessed into the 27 mm chassis envelope.  Its 2 mm plate
# occupies z=25..27 after assembly; it does not add another 2 mm externally.
TOTAL_DEPTH = 27.0


@dataclass
class SceneItem:
    triangles: np.ndarray
    color: str
    alpha: float
    label: str


def read_binary_stl(path: Path) -> np.ndarray:
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + count * 50:
        raise ValueError(f"invalid binary STL: {path}")
    mesh = np.empty((count, 3, 3), dtype=float)
    offset = 84
    for index in range(count):
        values = struct.unpack_from("<12fH", data, offset)
        mesh[index] = (values[3:6], values[6:9], values[9:12])
        offset += 50
    return mesh


def box_mesh(x0, y0, z0, x1, y1, z1) -> np.ndarray:
    vertices = np.array(
        [
            [x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],
            [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1],
        ],
        dtype=float,
    )
    faces = (
        (0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
        (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5),
        (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7),
    )
    return np.array([[vertices[i] for i in face] for face in faces])


def translate(mesh: np.ndarray, x=0.0, y=0.0, z=0.0) -> np.ndarray:
    return mesh + np.array([x, y, z])


def assembled_rear_cover(mesh: np.ndarray, extra_z=0.0) -> np.ndarray:
    result = mesh.copy()
    result[:, :, 0] += BODY_X + 0.2
    result[:, :, 1] += BODY_Y + 0.2
    result[:, :, 2] = BODY_D - result[:, :, 2] + extra_z
    return result


def lcd_proxy(z0=BEZEL_T) -> np.ndarray:
    return box_mesh(LCD_X, LCD_Y, z0, LCD_X + LCD_W, LCD_Y + LCD_H, z0 + LCD_T)


def pcb_proxy(z0=BODY_D - 8.6) -> np.ndarray:
    x0 = BEZEL_W / 2 - PCB_W / 2
    y0 = BODY_Y + WALL + 0.5
    return box_mesh(x0, y0, z0, x0 + PCB_W, y0 + PCB_H, z0 + PCB_T)


def render_scene(items: list[SceneItem], output: Path, title: str, elev=27, azim=-52) -> None:
    fig = plt.figure(figsize=(12, 8), dpi=220, facecolor="white")
    ax = fig.add_subplot(111, projection="3d")
    ax.set_proj_type("ortho")
    for item in items:
        poly = Poly3DCollection(
            item.triangles,
            facecolor=item.color,
            edgecolor="#263238",
            linewidth=0.08,
            alpha=item.alpha,
        )
        ax.add_collection3d(poly)

    points = np.concatenate([item.triangles.reshape(-1, 3) for item in items])
    lows = points.min(axis=0)
    highs = points.max(axis=0)
    centre = (lows + highs) / 2
    radius = max(highs - lows) / 2 * 1.05
    ax.set_xlim(centre[0] - radius, centre[0] + radius)
    ax.set_ylim(centre[1] - radius, centre[1] + radius)
    ax.set_zlim(centre[2] - radius, centre[2] + radius)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    ax.set_title(title, fontsize=18, color="#263238", pad=12)

    legend = [plt.Line2D([0], [0], color=item.color, lw=8, label=item.label)
              for item in items if item.label]
    if legend:
        ax.legend(handles=legend, loc="lower center", bbox_to_anchor=(0.5, -0.02),
                  ncol=min(5, len(legend)), frameon=False, fontsize=10)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def dimension_h(ax, x0, x1, y, source_y, text):
    color = "#1976d2"
    ax.annotate("", xy=(x1, y), xytext=(x0, y),
                arrowprops=dict(arrowstyle="<->", color=color, lw=1.0))
    ax.plot([x0, x0], [source_y, y], color=color, lw=0.7)
    ax.plot([x1, x1], [source_y, y], color=color, lw=0.7)
    ax.text((x0 + x1) / 2, y + 1.2, text, ha="center", va="bottom",
            color=color, fontsize=8)


def dimension_v(ax, y0, y1, x, source_x, text):
    color = "#1976d2"
    ax.annotate("", xy=(x, y1), xytext=(x, y0),
                arrowprops=dict(arrowstyle="<->", color=color, lw=1.0))
    ax.plot([source_x, x], [y0, y0], color=color, lw=0.7)
    ax.plot([source_x, x], [y1, y1], color=color, lw=0.7)
    ax.text(x - 1.2, (y0 + y1) / 2, text, ha="right", va="center",
            rotation=90, color=color, fontsize=8)


def setup_drawing_axis(ax, title):
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=12, fontweight="bold", color="#263238")
    ax.axis("off")


def create_three_view(output: Path) -> None:
    fig = plt.figure(figsize=(16, 10), dpi=220, facecolor="white")
    grid = fig.add_gridspec(2, 2, height_ratios=(1.25, 0.75), hspace=0.28, wspace=0.18)
    front = fig.add_subplot(grid[0, :])
    top = fig.add_subplot(grid[1, 0])
    side = fig.add_subplot(grid[1, 1])

    # Front view.
    setup_drawing_axis(front, "FRONT VIEW")
    front.add_patch(Rectangle((0, 0), BEZEL_W, BEZEL_H, fill=False, lw=2.0, color="#263238"))
    front.add_patch(Rectangle((WINDOW_X, WINDOW_Y), WINDOW_W, WINDOW_H,
                              fill=False, lw=1.8, color="#263238"))
    cut_x = (BEZEL_W - PANEL_CUTOUT_W) / 2
    cut_y = (BEZEL_H - PANEL_CUTOUT_H) / 2
    front.add_patch(Rectangle((cut_x, cut_y), PANEL_CUTOUT_W, PANEL_CUTOUT_H,
                              fill=False, lw=1.0, ls="--", color="#78909c"))
    dimension_h(front, 0, BEZEL_W, -9, 0, "118.0")
    dimension_v(front, 0, BEZEL_H, -11, 0, "81.0")
    dimension_h(front, WINDOW_X, WINDOW_X + WINDOW_W, WINDOW_Y - 5, WINDOW_Y,
                f"{WINDOW_W:.2f}")
    dimension_v(front, WINDOW_Y, WINDOW_Y + WINDOW_H, WINDOW_X - 5, WINDOW_X,
                f"{WINDOW_H:.2f}")
    front.text(BEZEL_W + 3, BEZEL_H - 2,
               f"Dashed: panel cutout\n{PANEL_CUTOUT_W:.1f} x {PANEL_CUTOUT_H:.1f}",
               va="top", fontsize=8, color="#546e7a")
    front.set_xlim(-16, BEZEL_W + 28)
    front.set_ylim(-13, BEZEL_H + 5)

    # Top view: X-Z.
    setup_drawing_axis(top, "TOP VIEW")
    top.add_patch(Rectangle((0, 0), BEZEL_W, BEZEL_T, fill=False, lw=2.0, color="#263238"))
    top.add_patch(Rectangle((BODY_X, BEZEL_T), BODY_W, BODY_D - BEZEL_T,
                            fill=False, lw=1.7, color="#263238"))
    top.add_patch(Rectangle((BODY_X + 0.2, BODY_D - 2.0), BODY_W - 0.4, 2.0,
                            fill=False, lw=1.7, color="#263238"))
    # HDMI opening on the top wall.
    top.add_patch(Rectangle((BEZEL_W / 2 - 8.2, 14.6), 16.4, 8.8,
                            fill=False, lw=1.2, color="#d84315"))
    dimension_h(top, 0, BEZEL_W, -8, 0, "118.0")
    dimension_v(top, 0, TOTAL_DEPTH, -10, 0, "29.0")
    top.text(BEZEL_W / 2, 24.5, "HDMI opening", ha="center", color="#d84315", fontsize=8)
    top.set_xlim(-15, BEZEL_W + 5)
    top.set_ylim(-11, TOTAL_DEPTH + 5)

    # Right side view: Z-Y.
    setup_drawing_axis(side, "RIGHT SIDE VIEW")
    side.add_patch(Rectangle((0, 0), BEZEL_T, BEZEL_H, fill=False, lw=2.0, color="#263238"))
    side.add_patch(Rectangle((BEZEL_T, BODY_Y), BODY_D - BEZEL_T, BODY_H,
                             fill=False, lw=1.7, color="#263238"))
    side.add_patch(Rectangle((BODY_D - 2.0, BODY_Y + 0.2), 2.0, BODY_H - 0.4,
                             fill=False, lw=1.7, color="#263238"))
    dimension_h(side, 0, TOTAL_DEPTH, -9, 0, "29.0")
    dimension_v(side, 0, BEZEL_H, -11, 0, "81.0")
    side.set_xlim(-16, TOTAL_DEPTH + 6)
    side.set_ylim(-12, BEZEL_H + 5)

    fig.suptitle("Tang Nano 9K + 4.3-inch LCD Panel Case - Orthographic Drawing",
                 fontsize=17, fontweight="bold", color="#263238", y=0.98)
    fig.text(0.5, 0.012,
             "Units: mm | Projection: orthographic | Scale: NTS | Reference panel: 4.3-inch 480 x 272",
             ha="center", fontsize=9, color="#546e7a")
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def create_pdf(pdf_path: Path, three_view: Path, assembly: Path, exploded: Path) -> None:
    font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    pdfmetrics.registerFont(TTFont("DejaVu", str(font_path)))
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    page_w, page_h = landscape(A4)
    canvas = pdf_canvas.Canvas(
        str(pdf_path), pagesize=(page_w, page_h), invariant=1
    )
    canvas.setTitle("Tang Nano 9K Panel Case Drawing")
    canvas.setAuthor("OpenAI Codex")

    def draw_fitted_image(path: Path, x, y, max_w, max_h):
        image = ImageReader(str(path))
        source_w, source_h = image.getSize()
        scale = min(max_w / source_w, max_h / source_h)
        draw_w, draw_h = source_w * scale, source_h * scale
        canvas.drawImage(image, x + (max_w - draw_w) / 2, y + (max_h - draw_h) / 2,
                         width=draw_w, height=draw_h, preserveAspectRatio=True, mask="auto")

    # Page 1: mechanical drawing. The PNG contains its own title and footer.
    draw_fitted_image(three_view, 10 * mm, 7 * mm, page_w - 20 * mm, page_h - 14 * mm)
    canvas.showPage()

    # Page 2: explanatory renders and dimensions.
    canvas.setFont("DejaVu", 18)
    canvas.setFillColor(colors.HexColor("#263238"))
    canvas.drawString(12 * mm, page_h - 14 * mm, "Assembly and exploded views")
    draw_fitted_image(assembly, 12 * mm, 100 * mm, 128 * mm, 86 * mm)
    draw_fitted_image(exploded, 151 * mm, 100 * mm, 128 * mm, 86 * mm)

    table = Table(
        [
            ["Item", "Nominal value"],
            ["LCD module", "105.50 x 67.15 x 2.90 mm"],
            ["PCB", "70.00 x 26.00 x 1.60 mm"],
            ["Front bezel", "118.00 x 81.00 mm"],
            ["Recommended panel cutout", "112.60 x 75.60 mm; trim after test fit"],
            ["Overall depth", "27.00 mm; rear cover is recessed"],
            ["Panel clip variants", "1.5 / 2.0 / 3.0 mm panel thickness"],
        ],
        colWidths=[75 * mm, 185 * mm],
        rowHeights=[7 * mm] * 7,
        style=TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "DejaVu"),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#263238")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#90a4ae")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eceff1")]),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2 * mm),
        ]),
    )
    table.wrapOn(canvas, 260 * mm, 49 * mm)
    table.drawOn(canvas, 18 * mm, 39 * mm)
    canvas.setFont("DejaVu", 8)
    canvas.setFillColor(colors.HexColor("#455a64"))
    canvas.drawString(12 * mm, 25 * mm,
                      "Design basis: Sipeed Tang Nano 9K and HT043DA-V.0 4.3-inch LCD.")
    canvas.drawString(12 * mm, 19 * mm,
                      "Verify connector height and clip fit on physical hardware before final panel machining.")
    canvas.save()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stl-dir", type=Path, default=Path("build"))
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    args = parser.parse_args()

    front = read_binary_stl(args.stl_dir / "front_chassis_panel_2p0mm.stl")
    retainer = read_binary_stl(args.stl_dir / "lcd_retainer.stl")
    cover = read_binary_stl(args.stl_dir / "rear_cover.stl")
    retainer_closed = translate(retainer, BODY_X + WALL + 0.2, BODY_Y + WALL + 0.2,
                                BEZEL_T + LCD_T)
    cover_closed = assembled_rear_cover(cover)

    image_dir = args.output_dir / "images"
    pdf_dir = args.output_dir / "pdf"
    assembly_path = image_dir / "assembly_render.png"
    exploded_path = image_dir / "exploded_render.png"
    three_view_path = image_dir / "orthographic_three_view.png"
    pdf_path = pdf_dir / "tang-nano-9k-panel-case-drawing.pdf"

    render_scene(
        [
            SceneItem(front, "#90a4ae", 0.23, "Front chassis"),
            SceneItem(lcd_proxy(), "#29b6f6", 0.82, "4.3-inch LCD"),
            SceneItem(retainer_closed, "#ffb74d", 0.82, "LCD retainer"),
            SceneItem(pcb_proxy(), "#43a047", 0.90, "Tang Nano 9K"),
            SceneItem(cover_closed, "#607d8b", 0.28, "Rear cover"),
        ],
        assembly_path,
        "Assembled cutaway render",
    )

    exploded_retainer = translate(retainer, BODY_X + WALL + 0.2, BODY_Y + WALL + 0.2, 43.0)
    exploded_lcd = lcd_proxy(34.0)
    exploded_pcb = pcb_proxy(52.0)
    exploded_cover = assembled_rear_cover(cover, extra_z=53.0)
    render_scene(
        [
            SceneItem(front, "#90a4ae", 0.42, "Front chassis"),
            SceneItem(exploded_lcd, "#29b6f6", 0.88, "4.3-inch LCD"),
            SceneItem(exploded_retainer, "#ffb74d", 0.90, "LCD retainer"),
            SceneItem(exploded_pcb, "#43a047", 0.92, "Tang Nano 9K"),
            SceneItem(exploded_cover, "#607d8b", 0.50, "Rear cover"),
        ],
        exploded_path,
        "Exploded render - front to rear",
        elev=24,
        azim=-55,
    )
    create_three_view(three_view_path)
    create_pdf(pdf_path, three_view_path, assembly_path, exploded_path)

    for path in (assembly_path, exploded_path, three_view_path, pdf_path):
        print(path)


if __name__ == "__main__":
    main()
