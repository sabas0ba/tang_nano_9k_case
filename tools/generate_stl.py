#!/usr/bin/env python3
"""Generate print-ready STL files for the Tang Nano 9K panel enclosure.

The generator intentionally uses only the Python standard library.  Geometry is
constructed as rectilinear CSG, evaluated on an exact coordinate grid, and
written as binary STL.  This keeps the build reproducible without a CAD kernel.
"""

from __future__ import annotations

import argparse
import math
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


EPS = 1.0e-9


@dataclass(frozen=True)
class Box:
    x0: float
    y0: float
    z0: float
    x1: float
    y1: float
    z1: float

    def __post_init__(self) -> None:
        if not (self.x0 < self.x1 and self.y0 < self.y1 and self.z0 < self.z1):
            raise ValueError(f"invalid box: {self}")


class RectilinearSolid:
    def __init__(self, name: str) -> None:
        self.name = name
        self.additions: list[Box] = []
        self.subtractions: list[Box] = []

    def add(self, *coords: float) -> None:
        self.additions.append(Box(*(round(value, 6) for value in coords)))

    def cut(self, *coords: float) -> None:
        self.subtractions.append(Box(*(round(value, 6) for value in coords)))

    def contains(self, x: float, y: float, z: float) -> bool:
        """Return whether a point is inside the evaluated CSG solid.

        Section drawings use this same positive-minus-negative definition as
        the STL mesher, so a drawn section cannot silently omit a slot, hook,
        rail, or service aperture that exists in the printable model.
        """

        def inside(box: Box) -> bool:
            return (
                box.x0 - EPS <= x <= box.x1 + EPS
                and box.y0 - EPS <= y <= box.y1 + EPS
                and box.z0 - EPS <= z <= box.z1 + EPS
            )

        return any(inside(box) for box in self.additions) and not any(
            inside(box) for box in self.subtractions
        )

    def triangles(self) -> list[tuple[tuple[float, float, float], ...]]:
        boxes = self.additions + self.subtractions
        if not self.additions:
            raise ValueError(f"{self.name}: no positive geometry")

        xs = sorted({v for b in boxes for v in (b.x0, b.x1)})
        ys = sorted({v for b in boxes for v in (b.y0, b.y1)})
        zs = sorted({v for b in boxes for v in (b.z0, b.z1)})
        xi = {v: i for i, v in enumerate(xs)}
        yi = {v: i for i, v in enumerate(ys)}
        zi = {v: i for i, v in enumerate(zs)}

        occupied: set[tuple[int, int, int]] = set()

        def cells(box: Box) -> Iterable[tuple[int, int, int]]:
            for i in range(xi[box.x0], xi[box.x1]):
                for j in range(yi[box.y0], yi[box.y1]):
                    for k in range(zi[box.z0], zi[box.z1]):
                        yield i, j, k

        for box in self.additions:
            occupied.update(cells(box))
        for box in self.subtractions:
            occupied.difference_update(cells(box))

        tris: list[tuple[tuple[float, float, float], ...]] = []

        def quad(a, b, c, d) -> None:
            tris.append((a, b, c))
            tris.append((a, c, d))

        for i, j, k in sorted(occupied):
            x0, x1 = xs[i], xs[i + 1]
            y0, y1 = ys[j], ys[j + 1]
            z0, z1 = zs[k], zs[k + 1]

            if (i - 1, j, k) not in occupied:
                quad((x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0))
            if (i + 1, j, k) not in occupied:
                quad((x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1))
            if (i, j - 1, k) not in occupied:
                quad((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1))
            if (i, j + 1, k) not in occupied:
                quad((x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0))
            if (i, j, k - 1) not in occupied:
                quad((x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0))
            if (i, j, k + 1) not in occupied:
                quad((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))

        return tris


def normal(tri: tuple[tuple[float, float, float], ...]) -> tuple[float, float, float]:
    a, b, c = tri
    u = tuple(b[n] - a[n] for n in range(3))
    v = tuple(c[n] - a[n] for n in range(3))
    n = (
        u[1] * v[2] - u[2] * v[1],
        u[2] * v[0] - u[0] * v[2],
        u[0] * v[1] - u[1] * v[0],
    )
    length = math.sqrt(sum(value * value for value in n))
    if length < EPS:
        raise ValueError(f"degenerate triangle: {tri}")
    return tuple(value / length for value in n)


def write_binary_stl(path: Path, name: str, triangles) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = f"Tang Nano 9K panel case: {name}".encode("ascii")[:80].ljust(80, b"\0")
    with path.open("wb") as stream:
        stream.write(header)
        stream.write(struct.pack("<I", len(triangles)))
        for tri in triangles:
            values = (*normal(tri), *tri[0], *tri[1], *tri[2])
            stream.write(struct.pack("<12fH", *values, 0))


# Reference dimensions, millimetres.
LCD_W = 105.50
LCD_H = 67.15
LCD_T = 2.90
LCD_ACTIVE_W = 95.04
LCD_ACTIVE_H = 53.856
LCD_ACTIVE_X = 5.18
LCD_ACTIVE_Y = 4.04

PCB_W = 26.00
PCB_H = 70.00
PCB_T = 1.60

BEZEL_W = 118.00
BEZEL_H = 81.00
BEZEL_T = 3.00
BODY_W = 112.00
BODY_H = 75.00
BODY_D = 27.00
BODY_X = (BEZEL_W - BODY_W) / 2.0
BODY_Y = (BEZEL_H - BODY_H) / 2.0
WALL = 2.00

RETAINER_ASSEMBLY_Z = BEZEL_T + LCD_T
RETAINER_HOOK_ARM_Z = 6.50
RETAINER_HOOK_STEP_Z0 = 4.70
RETAINER_HOOK_STEP_H = 0.60
RETAINER_HOOK_PROJECTIONS = (0.00, 0.20, 0.60)
RETAINER_WINDOW_Z0 = 11.70
RETAINER_WINDOW_Z1 = 12.50

PCB_SIDE_CLEARANCE = 0.25
PCB_AXIAL_CLEARANCE = 0.30
PCB_MOUNT_HOLE_D = 2.20
PCB_MOUNT_HOLE_EDGE_OFFSET = 2.60
M2_PILOT_SQUARE = 1.70
M2_BOSS_SIZE = 6.00
M2_THREAD_DEPTH = 6.00
STANDARD_REAR_CLEARANCE = 5.00
EXPANDED_REAR_CLEARANCES = (20.00, 30.00)

# Through-slots remove material from the broad, non-load-bearing regions of
# the rear plate.  The pattern stays outside the PCB carrier, screw bosses,
# perimeter rim, and connector-stop buttresses.
REAR_HATCH_SLOT_W = 8.00
REAR_HATCH_SLOT_H = 6.00
REAR_HATCH_XS = (7.00, 18.50, 30.00, 73.60, 85.10, 96.60)
REAR_HATCH_YS = (7.00, 18.00, 29.00, 40.00, 51.00, 62.00)


def add_side_with_snap_arms(
    solid: RectilinearSolid,
    side: str,
    panel_t: float,
) -> None:
    """Add one long side wall with two inward-deflecting panel clips."""
    arm_centres = (24.0, 51.0)
    slot_half = 5.0
    arm_half = 4.0
    arm_z0 = 4.2
    arm_anchor_z = 17.0

    if side == "left":
        wall_x0, wall_x1 = BODY_X, BODY_X + WALL
        arm_x0, arm_x1 = BODY_X + 0.55, BODY_X + 1.55
        head_ranges = (
            (BODY_X - 0.80, BODY_X + 1.55),
            (BODY_X - 0.50, BODY_X + 1.55),
            (BODY_X - 0.20, BODY_X + 1.55),
        )
    elif side == "right":
        wall_x0, wall_x1 = BODY_X + BODY_W - WALL, BODY_X + BODY_W
        arm_x0, arm_x1 = BODY_X + BODY_W - 1.55, BODY_X + BODY_W - 0.55
        head_ranges = (
            (BODY_X + BODY_W - 1.55, BODY_X + BODY_W + 0.80),
            (BODY_X + BODY_W - 1.55, BODY_X + BODY_W + 0.50),
            (BODY_X + BODY_W - 1.55, BODY_X + BODY_W + 0.20),
        )
    else:
        raise ValueError(side)

    # Continuous wall at the front and rear of the flexible-arm zone.
    solid.add(wall_x0, BODY_Y, BEZEL_T, wall_x1, BODY_Y + BODY_H, arm_z0)
    solid.add(wall_x0, BODY_Y, arm_anchor_z, wall_x1, BODY_Y + BODY_H, BODY_D)

    # Wall segments between the arm clearance slots.
    bounds = [BODY_Y]
    for centre in arm_centres:
        bounds.extend((BODY_Y + centre - slot_half, BODY_Y + centre + slot_half))
    bounds.append(BODY_Y + BODY_H)
    for start, end in zip(bounds[0::2], bounds[1::2]):
        solid.add(wall_x0, start, arm_z0, wall_x1, end, arm_anchor_z)

    catch_z = BEZEL_T + panel_t + 0.40
    for centre in arm_centres:
        y0 = BODY_Y + centre - arm_half
        y1 = BODY_Y + centre + arm_half
        solid.add(arm_x0, y0, arm_z0, arm_x1, y1, arm_anchor_z + 1.0)
        for step, (x0, x1) in enumerate(head_ranges):
            z0 = catch_z + step * 0.8
            solid.add(x0, y0, z0, x1, y1, z0 + 0.8)


def front_chassis(panel_t: float) -> RectilinearSolid:
    solid = RectilinearSolid(f"front-chassis-{panel_t:.1f}mm-panel")

    # Front bezel and active-area window.
    solid.add(0.0, 0.0, 0.0, BEZEL_W, BEZEL_H, BEZEL_T)
    lcd_x = BODY_X + (BODY_W - LCD_W) / 2.0
    lcd_y = BODY_Y + (BODY_H - LCD_H) / 2.0
    aperture_margin = 0.30
    window_x = lcd_x + LCD_ACTIVE_X - aperture_margin
    window_y = lcd_y + LCD_ACTIVE_Y - aperture_margin
    solid.cut(
        window_x,
        window_y,
        -0.1,
        window_x + LCD_ACTIVE_W + aperture_margin * 2.0,
        window_y + LCD_ACTIVE_H + aperture_margin * 2.0,
        BEZEL_T + 0.1,
    )

    add_side_with_snap_arms(solid, "left", panel_t)
    add_side_with_snap_arms(solid, "right", panel_t)

    # Top and bottom walls. The generous openings accept moulding variation in
    # USB-C and HDMI shells while keeping the connector faces recessed.
    solid.add(BODY_X, BODY_Y, BEZEL_T, BODY_X + BODY_W, BODY_Y + WALL, BODY_D)
    solid.add(
        BODY_X,
        BODY_Y + BODY_H - WALL,
        BEZEL_T,
        BODY_X + BODY_W,
        BODY_Y + BODY_H,
        BODY_D,
    )
    port_centre_x = BEZEL_W / 2.0
    solid.cut(
        port_centre_x - 6.2,
        BODY_Y - 0.1,
        15.4,
        port_centre_x + 6.2,
        BODY_Y + WALL + 0.1,
        22.8,
    )
    solid.cut(
        port_centre_x - 8.2,
        BODY_Y + BODY_H - WALL - 0.1,
        14.6,
        port_centre_x + 8.2,
        BODY_Y + BODY_H + 0.1,
        23.4,
    )

    # Four windows accept the independent LCD-retainer snap hooks.  The hook
    # centres deliberately avoid the panel-mount flex arms so the two snap
    # systems do not weaken the same wall sections.
    retainer_y = BODY_Y + WALL + 0.20
    for centre in (retainer_y + 12.0, retainer_y + 58.0):
        y0 = centre - 3.20
        y1 = centre + 3.20
        solid.cut(BODY_X - 0.1, y0, RETAINER_WINDOW_Z0,
                  BODY_X + WALL + 0.1, y1, RETAINER_WINDOW_Z1)
        solid.cut(BODY_X + BODY_W - WALL - 0.1, y0, RETAINER_WINDOW_Z0,
                  BODY_X + BODY_W + 0.1, y1, RETAINER_WINDOW_Z1)

    # Rear-cover latch windows, two on each long wall.
    for y0 in (BODY_Y + 9.0, BODY_Y + 60.0):
        solid.cut(BODY_X - 0.1, y0, 23.2, BODY_X + WALL + 0.1, y0 + 6.0, 25.7)
        solid.cut(
            BODY_X + BODY_W - WALL - 0.1,
            y0,
            23.2,
            BODY_X + BODY_W + 0.1,
            y0 + 6.0,
            25.7,
        )

    return solid


def lcd_retainer() -> RectilinearSolid:
    solid = RectilinearSolid("lcd-retainer")
    outer_w = 107.60
    outer_h = 70.60
    thickness = 2.00
    inner_w = 97.00
    inner_h = 56.00
    bx = (outer_w - inner_w) / 2.0
    by = (outer_h - inner_h) / 2.0

    solid.add(0.0, 0.0, 0.0, outer_w, outer_h, thickness)
    solid.cut(bx, by, -0.1, bx + inner_w, by + inner_h, thickness + 0.1)
    # 40-pin FPC tail relief on the side with the larger LCD border.
    solid.cut((outer_w - 25.0) / 2.0, outer_h - by - 0.1, -0.1,
              (outer_w + 25.0) / 2.0, outer_h + 0.1, thickness + 0.1)

    # Four rear-facing cantilever hooks make the retainer independent of the
    # removable rear cover.  The 1.2 mm arms flex inward during insertion and
    # the stepped 0.6 mm heads engage the chassis windows.
    arm_w = 1.20
    arm_z = RETAINER_HOOK_ARM_Z
    for centre in (12.0, 58.0):
        y0 = centre - 3.0
        y1 = centre + 3.0

        # Left and right cantilever arms.
        solid.add(0.0, y0, 0.0, arm_w, y1, arm_z)
        solid.add(outer_w - arm_w, y0, 0.0, outer_w, y1, arm_z)

        # Three rectilinear ramp steps on each outward-facing hook head.
        for step, projection in enumerate(RETAINER_HOOK_PROJECTIONS):
            z0 = RETAINER_HOOK_STEP_Z0 + step * RETAINER_HOOK_STEP_H
            z1 = z0 + RETAINER_HOOK_STEP_H
            solid.add(-projection, y0, z0, arm_w, y1, z1)
            solid.add(outer_w - arm_w, y0, z0,
                      outer_w + projection, y1, z1)
    return solid


def rear_cover(rear_clearance: float = STANDARD_REAR_CLEARANCE) -> RectilinearSolid:
    """Build a cover while keeping the PCB and connector planes unchanged.

    ``rear_clearance`` is measured from the PCB rear surface at global z=20
    to the inner face of the rear plate.  Increasing it extends only the rear
    shell and the carrier columns; USB-C, HDMI, LCD, and PCB global positions
    remain identical across variants.
    """
    if rear_clearance < STANDARD_REAR_CLEARANCE:
        raise ValueError("rear clearance cannot be less than 5 mm")
    overall_depth = 22.00 + rear_clearance
    depth_extension = overall_depth - BODY_D
    solid = RectilinearSolid(
        f"rear-cover-pcb-carrier-{rear_clearance:.0f}mm-clearance"
    )
    cover_w = 111.60
    cover_h = 74.60
    plate_t = 2.00
    rim_w = 107.60
    rim_h = 70.60
    rim_x = (cover_w - rim_w) / 2.0
    rim_y = (cover_h - rim_h) / 2.0
    rim_t = 1.50
    rim_hz = 4.50 + depth_extension

    solid.add(0.0, 0.0, 0.0, cover_w, cover_h, plate_t)
    solid.add(rim_x, rim_y, plate_t, rim_x + rim_t, rim_y + rim_h, rim_hz)
    solid.add(rim_x + rim_w - rim_t, rim_y, plate_t,
              rim_x + rim_w, rim_y + rim_h, rim_hz)
    solid.add(rim_x, rim_y, plate_t, rim_x + rim_w, rim_y + rim_t, rim_hz)
    solid.add(rim_x, rim_y + rim_h - rim_t, plate_t,
              rim_x + rim_w, rim_y + rim_h, rim_hz)

    # Four shallow bumps engage the chassis latch windows.
    latch_z0 = 2.25 + depth_extension
    latch_z1 = 3.85 + depth_extension
    for y0 in (rim_y + 9.0, rim_y + 60.0):
        solid.add(rim_x - 0.35, y0, latch_z0,
                  rim_x + 0.35, y0 + 6.0, latch_z1)
        solid.add(rim_x + rim_w - 0.35, y0, latch_z0,
                  rim_x + rim_w + 0.35, y0 + 6.0, latch_z1)

    board_x = (cover_w - PCB_W) / 2.0
    board_y = (cover_h - PCB_H) / 2.0
    support_z = 7.00 + depth_extension
    board_top = support_z + PCB_T
    rail_top = board_top + 0.60
    side_clearance = PCB_SIDE_CLEARANCE

    for y0, y1 in ((board_y + 9.0, board_y + 28.0),
                   (board_y + 42.0, board_y + 61.0)):
        # Four shelves support the PCB without loading components.
        solid.add(board_x - side_clearance - 0.80, y0, plate_t,
                  board_x + 1.20, y1, support_z)
        solid.add(board_x + PCB_W - 1.20, y0, plate_t,
                  board_x + PCB_W + side_clearance, y1, support_z)

        # Left side: fixed guide and lip.  Insert this PCB edge first.
        solid.add(board_x - side_clearance - 0.80, y0, support_z,
                  board_x - side_clearance, y1, rail_top)
        solid.add(board_x - side_clearance, y0, board_top,
                  board_x + 0.55, y1, rail_top)

        # Right side: 1.2 mm cantilever clip rooted at the cover plate.  Its
        # stepped head cams outward as the second PCB edge is pressed down.
        clip_x0 = board_x + PCB_W + side_clearance
        clip_x1 = clip_x0 + 1.20
        solid.add(clip_x0, y0, plate_t, clip_x1, y1, board_top)
        for step, overlap in enumerate((0.55, 0.35, 0.15)):
            z0 = board_top + step * 0.20
            solid.add(board_x + PCB_W - overlap, y0, z0,
                      clip_x1, y1, z0 + 0.20)

    # Paired end stops take USB-C/HDMI insertion loads instead of transferring
    # them through the PCB connector solder joints.  Each stop is carried by a
    # buttress that overlaps the perimeter rim, so the STL contains one
    # connected printable part instead of four floating stop bodies.
    stop_y_ranges = (
        (board_y - PCB_AXIAL_CLEARANCE - 0.30,
         board_y - PCB_AXIAL_CLEARANCE),
        (board_y + PCB_H + PCB_AXIAL_CLEARANCE,
         board_y + PCB_H + PCB_AXIAL_CLEARANCE + 0.30),
    )
    for x0, x1 in ((board_x + 4.50, board_x + 7.50),
                   (board_x + 18.50, board_x + 21.50)):
        lower_y0, lower_y1 = stop_y_ranges[0]
        upper_y0, upper_y1 = stop_y_ranges[1]
        solid.add(x0, lower_y0, support_z, x1, lower_y1, board_top)
        solid.add(x0, upper_y0, support_z, x1, upper_y1, board_top)

        # These supports remain outside the PCB outline.  Their overlap with
        # the bottom/top rim gives a volumetric union that survives importers
        # which do not merge bodies that merely share a coplanar face.
        solid.add(x0, lower_y0, plate_t,
                  x1, rim_y + rim_t, support_z)
        solid.add(x0, rim_y + rim_h - rim_t, plate_t,
                  x1, upper_y1, support_z)

    # Tang Nano 9K has two mounting holes at the HDMI end.  Square 1.70 mm
    # pilot bores are intentional: they are printable without circular CSG and
    # give an M2 self-tapping screw four gripping flats.  The optional screws
    # supplement the fixed lip and flex clips; screwless use remains possible.
    hdmi_hole_y = board_y + PCB_H - PCB_MOUNT_HOLE_EDGE_OFFSET
    boss_half = M2_BOSS_SIZE / 2.0
    pilot_half = M2_PILOT_SQUARE / 2.0
    for hole_x in (
        board_x + PCB_MOUNT_HOLE_EDGE_OFFSET,
        board_x + PCB_W - PCB_MOUNT_HOLE_EDGE_OFFSET,
    ):
        solid.add(hole_x - boss_half, hdmi_hole_y - boss_half, plate_t,
                  hole_x + boss_half, hdmi_hole_y + boss_half, support_z)
        solid.cut(hole_x - pilot_half, hdmi_hole_y - pilot_half,
                  support_z - M2_THREAD_DEPTH,
                  hole_x + pilot_half, hdmi_hole_y + pilot_half,
                  support_z + 0.10)

    # Large service aperture exposes the underside TF/microSD socket and also
    # provides ventilation. It deliberately avoids the PCB edge rails.
    solid.cut(board_x + 3.50, board_y + 12.0, -0.1,
              board_x + PCB_W - 3.50, board_y + 58.0, plate_t + 0.1)

    # Explicit rear-plate perforations reduce submitted model volume even
    # when the print service does not expose slicer infill settings.  The
    # remaining orthogonal webs keep the plate and all integrated features in
    # one connected component.
    for hatch_x in REAR_HATCH_XS:
        for hatch_y in REAR_HATCH_YS:
            solid.cut(hatch_x, hatch_y, -0.1,
                      hatch_x + REAR_HATCH_SLOT_W,
                      hatch_y + REAR_HATCH_SLOT_H,
                      plate_t + 0.1)

    return solid


def _translated_triangles(triangles, dx: float, dy: float, dz: float):
    return [
        tuple((x + dx, y + dy, z + dz) for x, y, z in triangle)
        for triangle in triangles
    ]


def _assembled_cover_triangles(
    triangles,
    overall_depth: float,
    dx: float,
    dy: float,
):
    """Reflect a rear-cover mesh into assembly coordinates.

    Reflection reverses handedness, so the second and third vertices are
    swapped to retain outward winding and positive signed volume.
    """
    assembled = []
    for triangle in triangles:
        mapped = tuple(
            (x + dx, y + dy, overall_depth - z)
            for x, y, z in triangle
        )
        assembled.append((mapped[0], mapped[2], mapped[1]))
    return assembled


def assembly_reference_triangles(rear_clearance: float):
    """Return a non-print assembly reference containing five closed shells."""
    overall_depth = 22.0 + rear_clearance
    triangles = list(front_chassis(2.0).triangles())

    retainer = lcd_retainer().triangles()
    triangles.extend(_translated_triangles(
        retainer,
        BODY_X + WALL + 0.20,
        BODY_Y + WALL + 0.20,
        RETAINER_ASSEMBLY_Z,
    ))

    cover_offset_x = (BEZEL_W - 111.60) / 2.0
    cover_offset_y = (BEZEL_H - 74.60) / 2.0
    triangles.extend(_assembled_cover_triangles(
        rear_cover(rear_clearance).triangles(),
        overall_depth,
        cover_offset_x,
        cover_offset_y,
    ))

    lcd_x = BODY_X + (BODY_W - LCD_W) / 2.0
    lcd_y = BODY_Y + (BODY_H - LCD_H) / 2.0
    lcd = RectilinearSolid("assembly-reference-lcd-proxy")
    lcd.add(lcd_x, lcd_y, BEZEL_T,
            lcd_x + LCD_W, lcd_y + LCD_H, BEZEL_T + LCD_T)
    triangles.extend(lcd.triangles())

    pcb_x = (BEZEL_W - PCB_W) / 2.0
    pcb_y = BODY_Y + WALL + 0.50
    pcb = RectilinearSolid("assembly-reference-pcb-proxy")
    pcb.add(pcb_x, pcb_y, 18.40,
            pcb_x + PCB_W, pcb_y + PCB_H, 18.40 + PCB_T)
    hdmi_hole_y = pcb_y + PCB_H - PCB_MOUNT_HOLE_EDGE_OFFSET
    hole_half = PCB_MOUNT_HOLE_D / 2.0
    for hdmi_hole_x in (
        pcb_x + PCB_MOUNT_HOLE_EDGE_OFFSET,
        pcb_x + PCB_W - PCB_MOUNT_HOLE_EDGE_OFFSET,
    ):
        pcb.cut(hdmi_hole_x - hole_half, hdmi_hole_y - hole_half, 18.30,
                hdmi_hole_x + hole_half, hdmi_hole_y + hole_half, 20.10)
    triangles.extend(pcb.triangles())
    return triangles


def generate(output_dir: Path) -> None:
    models = {
        "front_chassis_panel_1p5mm.stl": front_chassis(1.5),
        "front_chassis_panel_2p0mm.stl": front_chassis(2.0),
        "front_chassis_panel_3p0mm.stl": front_chassis(3.0),
        "lcd_retainer.stl": lcd_retainer(),
        "rear_cover.stl": rear_cover(),
        "rear_cover_clearance_20mm.stl": rear_cover(20.0),
        "rear_cover_clearance_30mm.stl": rear_cover(30.0),
    }
    for filename, solid in models.items():
        triangles = solid.triangles()
        write_binary_stl(output_dir / filename, solid.name, triangles)
        print(f"{filename}: {len(triangles)} triangles")

    for rear_clearance in EXPANDED_REAR_CLEARANCES:
        filename = f"assembly_reference_clearance_{rear_clearance:.0f}mm.stl"
        triangles = assembly_reference_triangles(rear_clearance)
        write_binary_stl(
            output_dir / filename,
            f"REFERENCE-ONLY assembled case {rear_clearance:.0f}mm clearance",
            triangles,
        )
        print(f"{filename}: {len(triangles)} triangles (REFERENCE ONLY)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("build"))
    args = parser.parse_args()
    generate(args.output)


if __name__ == "__main__":
    main()
