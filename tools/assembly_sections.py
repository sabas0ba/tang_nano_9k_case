#!/usr/bin/env python3
"""Exact 2-D assembly sections derived from the rectilinear STL solids."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Literal

from tools import generate_stl as model


Plane = Literal["x", "y"]


@dataclass(frozen=True)
class SectionPart:
    name: str
    solid: model.RectilinearSolid
    fill_key: str


@dataclass(frozen=True)
class SectionDefinition:
    code: str
    plane: Plane
    coordinate: float
    title: str
    purpose: str


SECTION_DEFINITIONS = (
    SectionDefinition(
        "A-A", "x", 53.20, "LONGITUDINAL Y-Z SECTION",
        "USB-C / HDMI, PCB end stop, LCD, FPC route and rear cover",
    ),
    SectionDefinition(
        "B-B", "y", 25.00, "PCB RETENTION X-Z SECTION",
        "fixed lip, support shelf, PCB and flexible clip",
    ),
    SectionDefinition(
        "C-C", "y", 17.20, "LCD HOOK X-Z SECTION",
        "retainer cantilevers, stepped heads and chassis windows",
    ),
    SectionDefinition(
        "D-D", "y", 40.50, "MICROSD SERVICE X-Z SECTION",
        "PCB underside, service aperture and rear clearance",
    ),
    SectionDefinition(
        "E-E", "y", 72.90, "HDMI-END M2 BOSS X-Z SECTION",
        "two HDMI-end mounting bosses, pilot bores, PCB and deep rear shell",
    ),
)


def _box_transform(
    box: model.Box,
    *,
    dx: float = 0.0,
    dy: float = 0.0,
    z_map: Callable[[float], float] | None = None,
) -> model.Box:
    z_fn = z_map or (lambda value: value)
    z0, z1 = sorted((z_fn(box.z0), z_fn(box.z1)))
    return model.Box(box.x0 + dx, box.y0 + dy, z0, box.x1 + dx, box.y1 + dy, z1)


def transformed(
    source: model.RectilinearSolid,
    name: str,
    *,
    dx: float = 0.0,
    dy: float = 0.0,
    z_map: Callable[[float], float] | None = None,
) -> model.RectilinearSolid:
    result = model.RectilinearSolid(name)
    result.additions = [
        _box_transform(box, dx=dx, dy=dy, z_map=z_map)
        for box in source.additions
    ]
    result.subtractions = [
        _box_transform(box, dx=dx, dy=dy, z_map=z_map)
        for box in source.subtractions
    ]
    return result


def box_solid(name: str, coords: tuple[float, float, float, float, float, float]) -> model.RectilinearSolid:
    solid = model.RectilinearSolid(name)
    solid.add(*coords)
    return solid


def assembly_parts(
    panel_t: float = 2.0,
    rear_clearance: float = model.STANDARD_REAR_CLEARANCE,
) -> tuple[SectionPart, ...]:
    """Return all verified mechanical solids in assembled global coordinates."""
    retainer = transformed(
        model.lcd_retainer(),
        "assembled-lcd-retainer",
        dx=model.BODY_X + model.WALL + 0.20,
        dy=model.BODY_Y + model.WALL + 0.20,
        z_map=lambda value: model.RETAINER_ASSEMBLY_Z + value,
    )
    cover_offset = (model.BEZEL_W - 111.60) / 2.0
    overall_depth = 22.0 + rear_clearance
    cover = transformed(
        model.rear_cover(rear_clearance),
        "assembled-rear-cover",
        dx=cover_offset,
        dy=(model.BEZEL_H - 74.60) / 2.0,
        z_map=lambda value: overall_depth - value,
    )
    lcd_x = model.BODY_X + (model.BODY_W - model.LCD_W) / 2.0
    lcd_y = model.BODY_Y + (model.BODY_H - model.LCD_H) / 2.0
    lcd = box_solid(
        "lcd-reference-envelope",
        (lcd_x, lcd_y, model.BEZEL_T, lcd_x + model.LCD_W,
         lcd_y + model.LCD_H, model.BEZEL_T + model.LCD_T),
    )
    pcb_x = (model.BEZEL_W - model.PCB_W) / 2.0
    pcb_y = model.BODY_Y + model.WALL + 0.50
    pcb = box_solid(
        "tang-nano-9k-pcb",
        (pcb_x, pcb_y, 18.40, pcb_x + model.PCB_W,
         pcb_y + model.PCB_H, 18.40 + model.PCB_T),
    )
    hdmi_hole_y = pcb_y + model.PCB_H - model.PCB_MOUNT_HOLE_EDGE_OFFSET
    hole_half = model.PCB_MOUNT_HOLE_D / 2.0
    for hdmi_hole_x in (
        pcb_x + model.PCB_MOUNT_HOLE_EDGE_OFFSET,
        pcb_x + model.PCB_W - model.PCB_MOUNT_HOLE_EDGE_OFFSET,
    ):
        pcb.cut(hdmi_hole_x - hole_half, hdmi_hole_y - hole_half, 18.30,
                hdmi_hole_x + hole_half, hdmi_hole_y + hole_half, 20.10)
    return (
        SectionPart("Front chassis", model.front_chassis(panel_t), "chassis"),
        SectionPart("LCD reference body", lcd, "lcd"),
        SectionPart("LCD retainer", retainer, "retainer"),
        SectionPart("Tang Nano 9K PCB", pcb, "pcb"),
        SectionPart("Rear cover + carrier", cover, "cover"),
    )


def section_cells(
    solid: model.RectilinearSolid,
    plane: Plane,
    coordinate: float,
) -> list[tuple[float, float, float, float]]:
    """Return occupied section cells as (horizontal0, vertical0, w, h)."""
    boxes = solid.additions + solid.subtractions
    if plane == "x":
        crossing = [box for box in boxes if box.x0 < coordinate < box.x1]
        horizontal = sorted({value for box in crossing for value in (box.y0, box.y1)})
    elif plane == "y":
        crossing = [box for box in boxes if box.y0 < coordinate < box.y1]
        horizontal = sorted({value for box in crossing for value in (box.x0, box.x1)})
    else:
        raise ValueError(plane)
    vertical = sorted({value for box in crossing for value in (box.z0, box.z1)})
    if len(horizontal) < 2 or len(vertical) < 2:
        return []

    result: list[tuple[float, float, float, float]] = []
    for h0, h1 in zip(horizontal, horizontal[1:]):
        for v0, v1 in zip(vertical, vertical[1:]):
            hm, vm = (h0 + h1) / 2.0, (v0 + v1) / 2.0
            occupied = (
                solid.contains(coordinate, hm, vm)
                if plane == "x"
                else solid.contains(hm, coordinate, vm)
            )
            if occupied:
                result.append((h0, v0, h1 - h0, v1 - v0))
    return result


def section_by_code(code: str) -> SectionDefinition:
    return next(section for section in SECTION_DEFINITIONS if section.code == code)


def mechanical_cells(
    section: SectionDefinition,
    parts: Iterable[SectionPart] | None = None,
) -> list[tuple[SectionPart, list[tuple[float, float, float, float]]]]:
    actual_parts = tuple(parts or assembly_parts())
    return [
        (part, section_cells(part.solid, section.plane, section.coordinate))
        for part in actual_parts
    ]
