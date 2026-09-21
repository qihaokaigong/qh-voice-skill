from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

from qh_voice_tool.flash import (
    FlashError,
    apply_candidate_flash,
    apply_flash,
    build_candidate_flash_plan,
    build_flash_plan,
)


class FlashTest(unittest.TestCase):
    def make_release(self, root: Path, *, status: str = "allowed") -> Path:
        firmware = root / "firmware"
        firmware.mkdir()
        bootloader = b"bootloader"
        app = b"application"
        (firmware / "bootloader.bin").write_bytes(bootloader)
        (firmware / "app.bin").write_bytes(app)
        manifest = {
            "schemaVersion": 1,
            "releaseId": "qh-voice-kit-0.1.0",
            "hardwareProfileId": "qh.voice-kit.breadboard.n16r8.v1",
            "chipFamily": "ESP32-S3",
            "acceptance": {
                "status": status,
                "reportId": "acceptance-1" if status == "allowed" else None,
            },
            "flash": {
                "eraseAll": False,
                "files": [
                    {
                        "role": "bootloader",
                        "address": 0,
                        "path": "firmware/bootloader.bin",
                        "size": len(bootloader),
                        "sha256": hashlib.sha256(bootloader).hexdigest(),
                    },
                    {
                        "role": "app",
                        "address": 0x10000,
                        "path": "firmware/app.bin",
                        "size": len(app),
                        "sha256": hashlib.sha256(app).hexdigest(),
                    },
                ],
            },
        }
        path = root / "release-manifest.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return path

    def test_builds_verified_non_erasing_esptool_plan(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.make_release(root)
            plan = build_flash_plan(manifest, root, "COM7")

            self.assertEqual(plan.release_id, "qh-voice-kit-0.1.0")
            self.assertEqual(plan.port, "COM7")
            self.assertEqual(plan.command[:3], (sys.executable, "-m", "esptool"))
            self.assertIn("esp32s3", plan.command)
            self.assertIn("write-flash", plan.command)
            self.assertNotIn("erase-flash", plan.command)
            self.assertNotIn("--erase-all", plan.command)
            self.assertIn("0x0", plan.command)
            self.assertIn("0x10000", plan.command)

    def test_apply_requires_exact_release_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = build_flash_plan(self.make_release(root), root, "COM7")
            calls: list[tuple[str, ...]] = []

            with self.assertRaisesRegex(FlashError, "confirmation"):
                apply_flash(
                    plan,
                    "wrong-release",
                    runner=lambda command: calls.append(tuple(command)),
                )

            self.assertEqual(calls, [])

    def test_apply_invokes_only_prebuilt_plan(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = build_flash_plan(self.make_release(root), root, "/dev/cu.test")
            calls: list[tuple[str, ...]] = []

            apply_flash(
                plan,
                plan.release_id,
                runner=lambda command: calls.append(tuple(command)),
            )

            self.assertEqual(calls, [plan.command])

    def test_candidate_plan_is_explicit_and_stable_plan_still_rejects_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.make_release(root, status="candidate")

            with self.assertRaisesRegex(FlashError, "allowed"):
                build_flash_plan(manifest, root, "/dev/cu.test")

            plan = build_candidate_flash_plan(manifest, root, "/dev/cu.test")

            self.assertEqual(plan.acceptance_status, "candidate")
            self.assertEqual(
                plan.hardware_profile_id, "qh.voice-kit.breadboard.n16r8.v1"
            )

    def test_candidate_apply_requires_release_and_hardware_profile_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = build_candidate_flash_plan(
                self.make_release(root, status="candidate"), root, "/dev/cu.test"
            )
            calls: list[tuple[str, ...]] = []

            with self.assertRaisesRegex(FlashError, "hardware profile"):
                apply_candidate_flash(
                    plan,
                    plan.release_id,
                    "wrong-profile",
                    runner=lambda command: calls.append(tuple(command)),
                )

            apply_candidate_flash(
                plan,
                plan.release_id,
                plan.hardware_profile_id,
                runner=lambda command: calls.append(tuple(command)),
            )

            self.assertEqual(calls, [plan.command])


if __name__ == "__main__":
    unittest.main()
