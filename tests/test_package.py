from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from tools import package_artifacts


class ArtifactPackage(unittest.TestCase):
    def test_archive_is_complete_and_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            project_root = temporary_root / "project"
            for index, relative_path in enumerate(package_artifacts.ARTIFACT_PATHS):
                path = project_root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(f"fixture-{index}\n".encode())

            first = temporary_root / "first.zip"
            second = temporary_root / "second.zip"
            package_artifacts.build_archive(project_root, first)
            package_artifacts.build_archive(project_root, second)

            self.assertEqual(
                hashlib.sha256(first.read_bytes()).digest(),
                hashlib.sha256(second.read_bytes()).digest(),
            )
            with ZipFile(first) as archive:
                self.assertEqual(
                    archive.namelist(), list(package_artifacts.ARTIFACT_PATHS)
                )


if __name__ == "__main__":
    unittest.main()
