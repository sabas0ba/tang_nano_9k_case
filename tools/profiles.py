#!/usr/bin/env python3
"""LCD-dependent enclosure profiles.

All coordinates use the model frame of ``generate_stl``: x and y are measured
from the lower-left corner of the front bezel as seen from the rear, z grows
from the bezel face toward the rear cover.  The USB-C end of the Tang Nano 9K
is at low y and the HDMI end is at high y.  Viewed from the front, model x is
mirrored; datasheet offsets measured from the front-left edge are converted
before they are stored here.

Shared mechanical values such as the wall thickness, bezel thickness, PCB
size, snap geometry and depth datums remain in ``generate_stl``.  A profile
only holds values that depend on the LCD module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


BEZEL_MARGIN = 3.00
WALL = 2.00
PANEL_CUTOUT_CLEARANCE = 0.30
COVER_CLEARANCE = 0.20
RETAINER_CLEARANCE = 0.20
WINDOW_MARGIN = 0.30
PCB_W = 26.00
PCB_H = 70.00


@dataclass(frozen=True)
class LcdModule:
    name: str
    description: str
    width: float
    height: float
    thickness: float
    active_w: float
    active_h: float
    # Active-area offsets from the module edge at model x=0 and y=0.
    active_x: float
    active_y: float
    # Edge from which the FPC leaves the module and the x range, measured
    # from the module edge at model x=0, that the retainer must keep open.
    fpc_side: Literal["top", "bottom"]
    fpc_x0: float
    fpc_x1: float
    source: str


@dataclass(frozen=True)
class PortOpening:
    """Rectangular opening centred on the PCB centreline.

    ``z0`` and ``z1`` are assembled global z coordinates.
    """

    half_w: float
    z0: float
    z1: float

    @property
    def width(self) -> float:
        return self.half_w * 2.0

    @property
    def height(self) -> float:
        return self.z1 - self.z0


@dataclass(frozen=True)
class CaseProfile:
    key: str
    title: str
    lcd: LcdModule
    body_w: float
    body_h: float
    retainer_opening_w: float
    retainer_opening_h: float
    # Centres measured from the bottom edge of the part that carries them.
    panel_arm_centres: tuple[float, float]
    retainer_hook_centres: tuple[float, float]
    rear_latch_ys: tuple[float, float]
    usb_opening: PortOpening
    hdmi_opening: PortOpening
    rear_hatch_xs: tuple[float, ...]
    rear_hatch_ys: tuple[float, ...]
    # A-A section x position relative to the PCB left edge.
    section_a_offset: float

    # Global enclosure outline.
    @property
    def bezel_w(self) -> float:
        return self.body_w + BEZEL_MARGIN * 2.0

    @property
    def bezel_h(self) -> float:
        return self.body_h + BEZEL_MARGIN * 2.0

    @property
    def body_x(self) -> float:
        return (self.bezel_w - self.body_w) / 2.0

    @property
    def body_y(self) -> float:
        return (self.bezel_h - self.body_h) / 2.0

    @property
    def panel_cutout_w(self) -> float:
        return self.body_w + PANEL_CUTOUT_CLEARANCE * 2.0

    @property
    def panel_cutout_h(self) -> float:
        return self.body_h + PANEL_CUTOUT_CLEARANCE * 2.0

    # LCD placement and display window.
    @property
    def lcd_x(self) -> float:
        return self.body_x + (self.body_w - self.lcd.width) / 2.0

    @property
    def lcd_y(self) -> float:
        return self.body_y + (self.body_h - self.lcd.height) / 2.0

    @property
    def window_x(self) -> float:
        return self.lcd_x + self.lcd.active_x - WINDOW_MARGIN

    @property
    def window_y(self) -> float:
        return self.lcd_y + self.lcd.active_y - WINDOW_MARGIN

    @property
    def window_w(self) -> float:
        return self.lcd.active_w + WINDOW_MARGIN * 2.0

    @property
    def window_h(self) -> float:
        return self.lcd.active_h + WINDOW_MARGIN * 2.0

    # LCD retainer, in its own coordinates and in assembly coordinates.
    @property
    def retainer_w(self) -> float:
        return self.body_w - (WALL + RETAINER_CLEARANCE) * 2.0

    @property
    def retainer_h(self) -> float:
        return self.body_h - (WALL + RETAINER_CLEARANCE) * 2.0

    @property
    def retainer_x(self) -> float:
        return self.body_x + WALL + RETAINER_CLEARANCE

    @property
    def retainer_y(self) -> float:
        return self.body_y + WALL + RETAINER_CLEARANCE

    @property
    def retainer_lcd_dx(self) -> float:
        """LCD x origin relative to the retainer x origin."""
        return (self.retainer_w - self.lcd.width) / 2.0

    # Rear cover.
    @property
    def cover_w(self) -> float:
        return self.body_w - COVER_CLEARANCE * 2.0

    @property
    def cover_h(self) -> float:
        return self.body_h - COVER_CLEARANCE * 2.0

    @property
    def cover_x(self) -> float:
        return (self.bezel_w - self.cover_w) / 2.0

    @property
    def cover_y(self) -> float:
        return (self.bezel_h - self.cover_h) / 2.0

    # Tang Nano 9K, centred in the bezel.
    @property
    def pcb_x(self) -> float:
        return (self.bezel_w - PCB_W) / 2.0

    @property
    def pcb_y(self) -> float:
        return (self.bezel_h - PCB_H) / 2.0

    @property
    def pcb_end_gap(self) -> float:
        """Distance from each PCB end to the inner face of the chassis wall."""
        return (self.body_h - WALL * 2.0 - PCB_H) / 2.0

    def validate(self) -> None:
        lcd_gap_x = (self.body_w - WALL * 2.0 - self.lcd.width) / 2.0
        lcd_gap_y = (self.body_h - WALL * 2.0 - self.lcd.height) / 2.0
        if min(lcd_gap_x, lcd_gap_y) < 0.40:
            raise ValueError(f"{self.key}: LCD clearance below 0.40 mm")
        if self.pcb_end_gap < 0.40:
            raise ValueError(f"{self.key}: PCB end clearance below 0.40 mm")
        if self.pcb_end_gap > 1.0:
            raise ValueError(f"{self.key}: connector faces are recessed")
        if not 0.0 <= self.lcd.fpc_x0 < self.lcd.fpc_x1 <= self.lcd.width:
            raise ValueError(f"{self.key}: FPC relief outside the LCD outline")


HT043DA = LcdModule(
    name="HT043DA-V.0",
    description="4.3-inch 480 x 272 RGB",
    width=105.50,
    height=67.15,
    thickness=2.90,
    active_w=95.04,
    active_h=53.856,
    active_x=5.18,
    active_y=4.04,
    fpc_side="top",
    fpc_x0=(105.50 - 25.00) / 2.0,
    fpc_x1=(105.50 + 25.00) / 2.0,
    source="Sipeed HT043DA-V.0 datasheet",
)

PROFILE_4P3IN = CaseProfile(
    key="4p3in",
    title="4.3-inch",
    lcd=HT043DA,
    # The 70 mm PCB, not the LCD, sets the body height.
    body_w=112.00,
    body_h=75.00,
    retainer_opening_w=97.00,
    retainer_opening_h=56.00,
    panel_arm_centres=(24.0, 51.0),
    retainer_hook_centres=(12.0, 58.0),
    rear_latch_ys=(9.0, 60.0),
    usb_opening=PortOpening(half_w=6.2, z0=15.4, z1=22.8),
    hdmi_opening=PortOpening(half_w=8.2, z0=14.6, z1=23.4),
    rear_hatch_xs=(7.00, 18.50, 30.00, 73.60, 85.10, 96.60),
    rear_hatch_ys=(7.00, 18.00, 29.00, 40.00, 51.00, 62.00),
    section_a_offset=7.20,
)

PROFILES: dict[str, CaseProfile] = {
    profile.key: profile for profile in (PROFILE_4P3IN,)
}
DEFAULT_PROFILE = PROFILE_4P3IN

for _profile in PROFILES.values():
    _profile.validate()


def get_profile(key: str) -> CaseProfile:
    try:
        return PROFILES[key]
    except KeyError as error:
        known = ", ".join(PROFILES)
        raise ValueError(f"unknown profile {key!r}; choose one of: {known}") from error
