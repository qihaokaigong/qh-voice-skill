from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "qh_voice.py"


class CliTest(unittest.TestCase):
    def test_release_verify_returns_structured_success(self) -> None:
        payload = b"app-image"
        with tempfile.TemporaryDirectory() as directory:
            release_root = Path(directory)
            (release_root / "firmware").mkdir()
            (release_root / "firmware" / "app.bin").write_bytes(payload)
            manifest = {
                "schemaVersion": 1,
                "releaseId": "qh-voice-kit-0.1.0",
                "hardwareProfileId": "qh.voice-kit.breadboard.n16r8.v1",
                "chipFamily": "ESP32-S3",
                "acceptance": {
                    "status": "allowed",
                    "reportId": "acceptance-1",
                },
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
            manifest_path = release_root / "release-manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            completed = subprocess.run(
                [
                    "python3",
                    str(CLI),
                    "release",
                    "verify",
                    "--manifest",
                    str(manifest_path),
                    "--root",
                    str(release_root),
                    "--json",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(completed.stdout)
            self.assertEqual(result["status"], "verified")
            self.assertEqual(result["releaseId"], "qh-voice-kit-0.1.0")
            self.assertEqual(result["artifacts"], ["app"])

    def test_release_verify_returns_stable_error_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            release_root = Path(directory)
            manifest_path = release_root / "release-manifest.json"
            manifest_path.write_text("{}", encoding="utf-8")

            completed = subprocess.run(
                [
                    "python3",
                    str(CLI),
                    "release",
                    "verify",
                    "--manifest",
                    str(manifest_path),
                    "--root",
                    str(release_root),
                    "--json",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )

            self.assertEqual(completed.returncode, 2)
            result = json.loads(completed.stdout)
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["code"], "invalid_release_manifest")
            self.assertNotIn("Traceback", completed.stderr)

    def test_flash_plan_is_structured_and_never_erases_all(self) -> None:
        payload = b"app-image"
        with tempfile.TemporaryDirectory() as directory:
            release_root = Path(directory)
            (release_root / "firmware").mkdir()
            (release_root / "firmware" / "app.bin").write_bytes(payload)
            manifest_path = release_root / "release-manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "releaseId": "qh-voice-kit-0.1.0",
                        "hardwareProfileId": "qh.voice-kit.breadboard.n16r8.v1",
                        "chipFamily": "ESP32-S3",
                        "acceptance": {
                            "status": "allowed",
                            "reportId": "acceptance-1",
                        },
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
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    "python3",
                    str(CLI),
                    "flash",
                    "plan",
                    "--manifest",
                    str(manifest_path),
                    "--root",
                    str(release_root),
                    "--port",
                    "COM7",
                    "--json",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(completed.stdout)
            self.assertEqual(result["status"], "planned")
            self.assertEqual(result["port"], "COM7")
            self.assertNotIn("erase-flash", result["command"])
            self.assertNotIn("--erase-all", result["command"])


if __name__ == "__main__":
    unittest.main()
