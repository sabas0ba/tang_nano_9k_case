#!/usr/bin/env python3
"""Create a deterministic archive of printable and reference deliverables."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import generate_stl  # noqa: E402
from tools.profiles import PROFILES  # noqa: E402


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_NAME = "tang-nano-9k-panel-case-r5.zip"
ARCHIVE_TIMESTAMP = (2026, 1, 1, 0, 0, 0)
DOCUMENT_PATHS = (
    "README.md",
    "docs/development.md",
    "docs/retention-design.md",
)
PROFILE_ARTIFACT_NAMES = (
    *(f"build/{{profile}}/{name}" for name in generate_stl.PRINTABLE_STL_NAMES),
    *(f"build/{{profile}}/{name}" for name in generate_stl.REFERENCE_STL_NAMES),
    "output/{profile}/images/assembly_render.png",
    "output/{profile}/images/exploded_render.png",
    "output/{profile}/images/orthographic_three_view.png",
    "output/{profile}/pdf/tang-nano-9k-panel-case-drawing.pdf",
    "output/{profile}/pdf/tang-nano-9k-panel-case-1to1.pdf",
    "output/{profile}/pdf/tang-nano-9k-panel-case-retention-design.pdf",
)
ARTIFACT_PATHS = DOCUMENT_PATHS + tuple(
    template.format(profile=profile)
    for profile in PROFILES
    for template in PROFILE_ARTIFACT_NAMES
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
