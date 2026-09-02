import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import support
from elliott_methodology_kernel.brain import (
    BrainIntegrityError,
    REQUIRED_PROTECTED_FILES,
    load_brain_manifest,
)


class BrainAccessTests(unittest.TestCase):
    def test_required_files_are_available_and_match_package_metadata(self) -> None:
        manifest = load_brain_manifest(support.PROTECTED_ROOT)
        self.assertEqual(set(REQUIRED_PROTECTED_FILES), set(manifest.observed_hashes))
        self.assertEqual((), manifest.mismatches)
        self.assertEqual("0.1.0", manifest.version)

    def test_loading_does_not_change_required_file_hashes(self) -> None:
        before = load_brain_manifest(support.PROTECTED_ROOT).observed_hashes
        after = load_brain_manifest(support.PROTECTED_ROOT).observed_hashes
        self.assertEqual(before, after)

    def test_missing_required_file_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir=support.RUNTIME_ROOT / "tests") as directory:
            root = Path(directory)
            (root / "VERSION").write_text("0.1.0\n", encoding="utf-8")
            (root / "PACKAGE_MANIFEST.json").write_text(
                json.dumps({"package": "test", "version": "0.1.0", "files": []}),
                encoding="utf-8",
            )
            with self.assertRaises(BrainIntegrityError):
                load_brain_manifest(root)


if __name__ == "__main__":
    unittest.main()
