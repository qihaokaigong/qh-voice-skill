from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from qh_voice_tool.release_manifest import (
    ManifestError,
    load_allowed_manifest,
    verify_release_artifacts,
)


class FlashError(RuntimeError):
    """Raised before or during a controlled firmware write."""


@dataclass(frozen=True)
class FlashPlan:
    release_id: str
    hardware_profile_id: str
    port: str
    command: tuple[str, ...]


Runner = Callable[[Sequence[str]], object]


def build_flash_plan(
    manifest_path: Path, release_root: Path, port: str
) -> FlashPlan:
    if not port.strip() or any(character in port for character in "\r\n\x00"):
        raise FlashError("a valid serial port is required")
    try:
        manifest = load_allowed_manifest(manifest_path)
        artifacts = verify_release_artifacts(manifest, release_root)
    except ManifestError as error:
        raise FlashError(str(error)) from error
    if manifest.chip_family != "ESP32-S3":
        raise FlashError("the first supported release must target ESP32-S3")

    resolved_root = release_root.resolve()
    command = [
        sys.executable,
        "-m",
        "esptool",
        "--chip",
        "esp32s3",
        "--port",
        port,
        "--baud",
        "921600",
        "--before",
        "default-reset",
        "--after",
        "hard-reset",
        "write-flash",
        "--flash-mode",
        "keep",
        "--flash-freq",
        "keep",
        "--flash-size",
        "keep",
    ]
    for artifact in sorted(artifacts, key=lambda item: item.address):
        command.extend(
            [hex(artifact.address), str(resolved_root / Path(artifact.path))]
        )
    return FlashPlan(
        release_id=manifest.release_id,
        hardware_profile_id=manifest.hardware_profile_id,
        port=port,
        command=tuple(command),
    )


def _run(command: Sequence[str]) -> None:
    subprocess.run(command, check=True)


def apply_flash(
    plan: FlashPlan,
    confirmed_release_id: str,
    *,
    runner: Runner | None = None,
) -> None:
    if confirmed_release_id != plan.release_id:
        raise FlashError("release confirmation does not match the verified plan")
    try:
        (runner or _run)(plan.command)
    except subprocess.CalledProcessError as error:
        raise FlashError(f"esptool failed with exit code {error.returncode}") from error
    except OSError as error:
        raise FlashError(f"cannot start esptool: {error}") from error
