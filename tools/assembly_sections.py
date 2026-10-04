#!/usr/bin/env python3
"""Exact 2-D assembly sections derived from the rectilinear STL solids."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Literal

from tools import generate_stl as model
from tools.profiles import CaseProfile


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


def section_definitions(profile: CaseProfile) -> tuple[SectionDefinition, ...]:
    """Return cutting planes positioned on the profile's actual features."""
    retainer_hook_y = profile.retainer_y + profile.retainer_hook_centres[0]
    return (
        SectionDefinition(
            "A-A", "x", profile.pcb_x + profile.section_a_offset,
            "LONGITUDINAL Y-Z SECTION",
            "USB-C / HDMI, PCB end stop, LCD, FPC route and rear cover",
        ),
        SectionDefinition(
            "B-B", "y", profile.pcb_y + 19.50, "PCB RETENTION X-Z SECTION",
            "fixed lip, support shelf, PCB and flexible clip",
        ),
        SectionDefinition(
            "C-C", "y", retainer_hook_y, "LCD HOOK X-Z SECTION",
            "retainer cantilevers, stepped heads and chassis windows",
        ),
        SectionDefinition(
            "D-D", "y", profile.pcb_y + model.PCB_H / 2.0,
            "MICROSD SERVICE X-Z SECTION",
            "PCB underside, service aperture and rear clearance",
        ),
        SectionDefinition(
            "E-E", "y",
            profile.pcb_y + model.PCB_H - model.PCB_MOUNT_HOLE_EDGE_OFFSET,
            "HDMI-END M2 BOSS X-Z SECTION",
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


def assembly_parts(
    profile: CaseProfile,
    panel_t: float = 2.0,
    rear_clearance: float = model.STANDARD_REAR_CLEARANCE,
) -> tuple[SectionPart, ...]:
    """Return all verified mechanical solids in assembled global coordinates."""
    retainer_z = model.retainer_assembly_z(profile)
    retainer = transformed(
        model.lcd_retainer(profile),
        "assembled-lcd-retainer",
        dx=profile.retainer_x,
        dy=profile.retainer_y,
        z_map=lambda value: retainer_z + value,
    )
    overall_depth = 22.0 + rear_clearance
    cover = transformed(
        model.rear_cover(profile, rear_clearance),
        "assembled-rear-cover",
        dx=profile.cover_x,
        dy=profile.cover_y,
        z_map=lambda value: overall_depth - value,
    )
    return (
        SectionPart("Front chassis", model.front_chassis(profile, panel_t),
                    "chassis"),
        SectionPart("LCD reference body", model.lcd_proxy(profile), "lcd"),
        SectionPart("LCD retainer", retainer, "retainer"),
        SectionPart("Tang Nano 9K PCB", model.pcb_proxy(profile), "pcb"),
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


def section_by_code(profile: CaseProfile, code: str) -> SectionDefinition:
    return next(
        section for section in section_definitions(profile)
        if section.code == code
    )


def mechanical_cells(
    section: SectionDefinition,
    parts: Iterable[SectionPart],
) -> list[tuple[SectionPart, list[tuple[float, float, float, float]]]]:
    return [
        (part, section_cells(part.solid, section.plane, section.coordinate))
        for part in parts
    ]
