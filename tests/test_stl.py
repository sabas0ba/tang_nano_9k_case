#!/usr/bin/env python3
"""Structural checks for generated binary STL meshes."""

from __future__ import annotations

import math
import struct
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import generate_stl as model  # noqa: E402
from tools.assembly_sections import assembly_parts, section_by_code, section_cells  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]


def read_stl(path: Path):
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + count * 50:
        raise AssertionError(f"invalid STL byte count: {path}")
    triangles = []
    offset = 84
    for _ in range(count):
        values = struct.unpack_from("<12fH", data, offset)
        triangles.append((values[3:6], values[6:9], values[9:12]))
        offset += 50
    return triangles


def key(point):
    return tuple(round(value, 5) for value in point)


class GeneratedMeshes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.TemporaryDirectory()
        cls.output = Path(cls.tempdir.name)
        subprocess.run(
            [sys.executable, str(ROOT / "tools/generate_stl.py"), "--output", str(cls.output)],
            check=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls.tempdir.cleanup()

    def check_mesh(self, name, expected_bounds):
        triangles = read_stl(self.output / name)
        self.assertGreater(len(triangles), 100)
        points = [point for tri in triangles for point in tri]
        self.assertTrue(all(math.isfinite(value) for point in points for value in point))

        bounds = tuple(
            value
            for axis in range(3)
            for value in (
                min(point[axis] for point in points),
                max(point[axis] for point in points),
            )
        )
        for actual, expected in zip(bounds, expected_bounds):
            self.assertAlmostEqual(actual, expected, places=4)

        edges = Counter()
        for tri in triangles:
            for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
                edges[tuple(sorted((key(a), key(b))))] += 1
        self.assertEqual({count for count in edges.values()}, {2}, "mesh is not 2-manifold")

        signed_volume = 0.0
        for a, b, c in triangles:
            signed_volume += (
                a[0] * (b[1] * c[2] - b[2] * c[1])
                - a[1] * (b[0] * c[2] - b[2] * c[0])
                + a[2] * (b[0] * c[1] - b[1] * c[0])
            ) / 6.0
        self.assertGreater(signed_volume, 1.0)

    def test_front_variants(self):
        for name in (
            "front_chassis_panel_1p5mm.stl",
            "front_chassis_panel_2p0mm.stl",
            "front_chassis_panel_3p0mm.stl",
        ):
            with self.subTest(name=name):
                self.check_mesh(name, (0.0, 118.0, 0.0, 81.0, 0.0, 27.0))

    def test_lcd_retainer(self):
        self.check_mesh("lcd_retainer.stl", (-0.6, 108.2, 0.0, 70.6, 0.0, 6.5))

    def test_rear_cover(self):
        self.check_mesh("rear_cover.stl", (0.0, 111.6, 0.0, 74.6, 0.0, 9.2))

    def test_deep_rear_cover_variants(self):
        self.check_mesh(
            "rear_cover_clearance_20mm.stl",
            (0.0, 111.6, 0.0, 74.6, 0.0, 24.2),
        )
        self.check_mesh(
            "rear_cover_clearance_30mm.stl",
            (0.0, 111.6, 0.0, 74.6, 0.0, 34.2),
        )

    def test_retainer_hook_capture_clearance(self):
        max_step = len(model.RETAINER_HOOK_PROJECTIONS) - 1
        head_z0 = (
            model.RETAINER_ASSEMBLY_Z
            + model.RETAINER_HOOK_STEP_Z0
            + max_step * model.RETAINER_HOOK_STEP_H
        )
        head_z1 = head_z0 + model.RETAINER_HOOK_STEP_H
        self.assertAlmostEqual(head_z0 - model.RETAINER_WINDOW_Z0, 0.10, places=4)
        self.assertAlmostEqual(model.RETAINER_WINDOW_Z1 - head_z1, 0.10, places=4)

    def test_pcb_nominal_clearances(self):
        self.assertAlmostEqual(model.PCB_SIDE_CLEARANCE, 0.25, places=4)
        self.assertAlmostEqual(model.PCB_AXIAL_CLEARANCE, 0.30, places=4)

    def test_hdmi_end_m2_bosses(self):
        cover = model.rear_cover(20.0)
        board_x = (111.60 - model.PCB_W) / 2.0
        board_y = (74.60 - model.PCB_H) / 2.0
        support_z = 22.0
        hole_y = board_y + model.PCB_H - model.PCB_MOUNT_HOLE_EDGE_OFFSET
        for hole_x in (
            board_x + model.PCB_MOUNT_HOLE_EDGE_OFFSET,
            board_x + model.PCB_W - model.PCB_MOUNT_HOLE_EDGE_OFFSET,
        ):
            with self.subTest(hole_x=hole_x):
                self.assertFalse(cover.contains(hole_x, hole_y, support_z - 1.0))
                self.assertTrue(cover.contains(hole_x - 2.0, hole_y, support_z - 1.0))

    def test_deep_cover_preserves_pcb_plane(self):
        for clearance in model.EXPANDED_REAR_CLEARANCES:
            parts = {part.name: part.solid for part in assembly_parts(
                rear_clearance=clearance
            )}
            pcb = parts["Tang Nano 9K PCB"]
            cover = parts["Rear cover + carrier"]
            with self.subTest(clearance=clearance):
                self.assertTrue(pcb.contains(59.0, 40.0, 19.0))
                inner_plate_z = 20.0 + clearance
                self.assertTrue(cover.contains(10.0, 10.0, inner_plate_z + 1.0))
                self.assertFalse(cover.contains(10.0, 10.0, inner_plate_z - 0.1))

    def test_assembly_reference_meshes(self):
        for clearance, overall_depth in ((20.0, 42.0), (30.0, 52.0)):
            path = self.output / f"assembly_reference_clearance_{clearance:.0f}mm.stl"
            triangles = read_stl(path)
            points = [point for triangle in triangles for point in triangle]
            with self.subTest(clearance=clearance):
                self.assertGreater(len(triangles), 10000)
                self.assertTrue(all(
                    math.isfinite(value) for point in points for value in point
                ))
                bounds = tuple(
                    value
                    for axis in range(3)
                    for value in (
                        min(point[axis] for point in points),
                        max(point[axis] for point in points),
                    )
                )
                expected = (0.0, 118.0, 0.0, 81.0, 0.0, overall_depth)
                for actual, target in zip(bounds, expected):
                    self.assertAlmostEqual(actual, target, places=4)

                signed_volume = 0.0
                for a, b, c in triangles:
                    signed_volume += (
                        a[0] * (b[1] * c[2] - b[2] * c[1])
                        - a[1] * (b[0] * c[2] - b[2] * c[0])
                        + a[2] * (b[0] * c[1] - b[1] * c[0])
                    ) / 6.0
                self.assertGreater(signed_volume, 1.0)

    def test_exact_section_planes_cross_required_features(self):
        parts = {part.name: part.solid for part in assembly_parts()}
        cover = parts["Rear cover + carrier"]
        retainer = parts["LCD retainer"]
        chassis = parts["Front chassis"]

        # C-C crosses a retainer hook head while the matching chassis wall is
        # absent at its engagement window.
        self.assertTrue(retainer.contains(4.80, 17.20, 12.00))
        self.assertFalse(chassis.contains(4.00, 17.20, 12.00))

        # B-B crosses the left fixed lip and the right flexible clip head.
        self.assertTrue(cover.contains(46.10, 25.00, 18.10))
        self.assertTrue(cover.contains(72.30, 25.00, 18.10))

        # D-D crosses the intentional service aperture under the PCB.
        self.assertFalse(cover.contains(59.00, 40.50, 26.00))
        self.assertTrue(parts["Tang Nano 9K PCB"].contains(59.00, 40.50, 19.00))

        for code in ("A-A", "B-B", "C-C", "D-D", "E-E"):
            section = section_by_code(code)
            with self.subTest(section=code):
                self.assertTrue(any(
                    section_cells(part, section.plane, section.coordinate)
                    for part in parts.values()
                ))


if __name__ == "__main__":
    unittest.main()
