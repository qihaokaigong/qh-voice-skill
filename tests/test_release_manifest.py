from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from qh_voice_tool.release_manifest import (
    ManifestError,
    load_allowed_manifest,
    load_candidate_manifest,
    verify_release_artifacts,
)


def manifest_for(payload: bytes) -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "releaseId": "qh-voice-kit-0.1.0",
        "hardwareProfileId": "qh.voice-kit.breadboard.n16r8.v1",
        "chipFamily": "ESP32-S3",
        "acceptance": {"status": "allowed", "reportId": "acceptance-1"},
        "flash": {
            "eraseAll": False,
            "files": [
                {
                    "role": "app",
                    "address": 0x10000,
                    "path": "firmware/app.bin",
                    "size": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            ],
        },
    }


class ReleaseManifestTest(unittest.TestCase):
    def test_loads_allowed_manifest_and_verifies_artifact(self) -> None:
        payload = b"firmware-image"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "firmware").mkdir()
            (root / "firmware" / "app.bin").write_bytes(payload)
            manifest_path = root / "release-manifest.json"
            manifest_path.write_text(json.dumps(manifest_for(payload)), encoding="utf-8")

            manifest = load_allowed_manifest(manifest_path)
            verified = verify_release_artifacts(manifest, root)

            self.assertEqual(manifest.release_id, "qh-voice-kit-0.1.0")
            self.assertEqual([item.role for item in verified], ["app"])

    def test_rejects_candidate_release(self) -> None:
        manifest = manifest_for(b"image")
        manifest["acceptance"] = {"status": "candidate", "reportId": None}

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "release-manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ManifestError, "allowed"):
                load_allowed_manifest(path)

    def test_loads_candidate_only_through_explicit_candidate_api(self) -> None:
        manifest = manifest_for(b"image")
        manifest["releaseId"] = "qh-voice-kit-0.1.0-candidate.1"
        manifest["acceptance"] = {"status": "candidate", "reportId": None}

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "release-manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")

            loaded = load_candidate_manifest(path)

            self.assertEqual(loaded.release_id, "qh-voice-kit-0.1.0-candidate.1")
            self.assertEqual(loaded.acceptance_status, "candidate")

    def test_rejects_path_traversal_and_overlapping_flash_ranges(self) -> None:
        manifest = manifest_for(b"image")
        manifest["flash"]["files"] = [
            {
                "role": "bootloader",
                "address": 0x0,
                "path": "../bootloader.bin",
                "size": 0x2000,
                "sha256": "0" * 64,
            },
            {
                "role": "partition-table",
                "address": 0x1000,
                "path": "firmware/partition-table.bin",
                "size": 0x1000,
                "sha256": "1" * 64,
            },
        ]

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "release-manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(ManifestError) as caught:
                load_allowed_manifest(path)
            self.assertIn("path", str(caught.exception))
            self.assertIn("overlap", str(caught.exception))

    def test_rejects_artifact_with_wrong_hash(self) -> None:
        expected = b"expected"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "firmware").mkdir()
            (root / "firmware" / "app.bin").write_bytes(b"tampered")
            manifest_path = root / "release-manifest.json"
            manifest_path.write_text(
                json.dumps(manifest_for(expected)), encoding="utf-8"
            )
            manifest = load_allowed_manifest(manifest_path)

            with self.assertRaisesRegex(ManifestError, "size|SHA-256"):
                verify_release_artifacts(manifest, root)


if __name__ == "__main__":
    unittest.main()
