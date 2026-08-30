#!/usr/bin/env python3
"""Create a deterministic archive of printable and reference deliverables."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_NAME = "tang-nano-9k-panel-case-r4.zip"
ARCHIVE_TIMESTAMP = (2026, 1, 1, 0, 0, 0)
ARTIFACT_PATHS = (
    "README.md",
    "docs/development.md",
    "docs/retention-design.md",
    "build/front_chassis_panel_1p5mm.stl",
    "build/front_chassis_panel_2p0mm.stl",
    "build/front_chassis_panel_3p0mm.stl",
    "build/lcd_retainer.stl",
    "build/rear_cover.stl",
    "build/rear_cover_clearance_20mm.stl",
    "build/rear_cover_clearance_30mm.stl",
    "build/assembly_reference_clearance_20mm.stl",
    "build/assembly_reference_clearance_30mm.stl",
    "output/images/assembly_render.png",
    "output/images/exploded_render.png",
    "output/images/orthographic_three_view.png",
    "output/pdf/tang-nano-9k-panel-case-drawing.pdf",
    "output/pdf/tang-nano-9k-panel-case-1to1.pdf",
    "output/pdf/tang-nano-9k-panel-case-retention-design.pdf",
)


def build_archive(project_root: Path, archive_path: Path) -> None:
    missing = [path for path in ARTIFACT_PATHS if not (project_root / path).is_file()]
    if missing:
        raise FileNotFoundError("missing generated artifacts: " + ", ".join(missing))

    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for relative_path in ARTIFACT_PATHS:
            source = project_root / relative_path
            info = ZipInfo(relative_path, ARCHIVE_TIMESTAMP)
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, source.read_bytes(), compresslevel=9)


def write_checksum(archive_path: Path, checksum_path: Path) -> None:
    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    checksum_path.write_text(f"{digest}  {archive_path.name}\n", encoding="ascii")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "dist")
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    archive_path = output_dir / ARCHIVE_NAME
    build_archive(PROJECT_ROOT, archive_path)
    write_checksum(archive_path, output_dir / "SHA256SUMS")
    print(f"created {archive_path}")


if __name__ == "__main__":
    main()
