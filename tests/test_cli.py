from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from qh_voice_tool.cli import main
from qh_voice_tool.host_inspect import HostInspectionError


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "qh_voice.py"


class CliTest(unittest.TestCase):
    def test_inspect_reports_missing_dependency_without_traceback(self) -> None:
        output = StringIO()
        with patch(
            "qh_voice_tool.cli.inspect_host",
            side_effect=HostInspectionError("pyserial is required"),
        ), redirect_stdout(output):
            return_code = main(["inspect", "--json"])

        self.assertEqual(return_code, 2)
        result = json.loads(output.getvalue())
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["code"], "host_inspection_unavailable")
        self.assertIn("pyserial", result["message"])

    def test_configure_uses_local_browser_flow_by_default(self) -> None:
        output = StringIO()
        with patch(
            "qh_voice_tool.cli.configure_in_browser",
            return_value={
                "status": "configured",
                "rebootRequired": False,
                "deviceRestarting": True,
            },
        ) as configure, redirect_stdout(output):
            return_code = main(["configure", "--port", "COM7"])

        self.assertEqual(return_code, 0)
        configure.assert_called_once_with("COM7")
        self.assertIn("配置已写入设备", output.getvalue())

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

    def test_candidate_flash_plan_requires_explicit_command(self) -> None:
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
                        "releaseId": "qh-voice-kit-0.1.0-candidate.1",
                        "hardwareProfileId": "qh.voice-kit.breadboard.n16r8.v1",
                        "chipFamily": "ESP32-S3",
                        "acceptance": {"status": "candidate", "reportId": None},
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

            stable = subprocess.run(
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
                    "/dev/cu.test",
                    "--json",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            candidate = subprocess.run(
                [
                    "python3",
                    str(CLI),
                    "flash",
                    "candidate-plan",
                    "--manifest",
                    str(manifest_path),
                    "--root",
                    str(release_root),
                    "--port",
                    "/dev/cu.test",
                    "--json",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )

            self.assertEqual(stable.returncode, 2)
            self.assertEqual(candidate.returncode, 0, candidate.stderr)
            result = json.loads(candidate.stdout)
            self.assertEqual(result["status"], "candidate_planned")
            self.assertEqual(result["acceptanceStatus"], "candidate")


if __name__ == "__main__":
    unittest.main()
