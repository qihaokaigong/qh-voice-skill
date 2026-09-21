from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any


SHA256_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")


class ManifestError(ValueError):
    """Raised when a release cannot be trusted for flashing."""


@dataclass(frozen=True)
class FirmwareArtifact:
    role: str
    address: int
    path: PurePosixPath
    size: int
    sha256: str


@dataclass(frozen=True)
class ReleaseManifest:
    release_id: str
    hardware_profile_id: str
    chip_family: str
    acceptance_status: str
    acceptance_report_id: str | None
    artifacts: tuple[FirmwareArtifact, ...]


def _object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ManifestError(f"{field} must be an object")
    return value


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{field} must be a non-empty string")
    return value


def _integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ManifestError(f"{field} must be an integer")
    return value


def _artifact(value: Any, index: int) -> tuple[FirmwareArtifact | None, list[str]]:
    errors: list[str] = []
    try:
        item = _object(value, f"flash.files[{index}]")
        role = _string(item.get("role"), f"flash.files[{index}].role")
        address = _integer(item.get("address"), f"flash.files[{index}].address")
        size = _integer(item.get("size"), f"flash.files[{index}].size")
        raw_path = _string(item.get("path"), f"flash.files[{index}].path")
        digest = _string(item.get("sha256"), f"flash.files[{index}].sha256")
    except ManifestError as error:
        return None, [str(error)]

    path = PurePosixPath(raw_path)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        errors.append(f"flash.files[{index}].path must stay inside the release")
    if address < 0:
        errors.append(f"flash.files[{index}].address must be non-negative")
    if size <= 0:
        errors.append(f"flash.files[{index}].size must be positive")
    if not SHA256_PATTERN.fullmatch(digest):
        errors.append(f"flash.files[{index}].sha256 must be 64 hexadecimal characters")
    return FirmwareArtifact(role, address, path, size, digest.lower()), errors


def _load_manifest(path: Path, expected_status: str) -> ReleaseManifest:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ManifestError(f"cannot read release manifest: {error}") from error

    root = _object(raw, "manifest")
    if root.get("schemaVersion") != 1:
        raise ManifestError("schemaVersion must be 1")

    acceptance = _object(root.get("acceptance"), "acceptance")
    if acceptance.get("status") != expected_status:
        if expected_status == "allowed":
            raise ManifestError("stable installation requires an allowed release")
        raise ManifestError("candidate testing requires a candidate release")
    report_id: str | None
    if expected_status == "allowed":
        report_id = _string(acceptance.get("reportId"), "acceptance.reportId")
    else:
        report_id = None

    flash = _object(root.get("flash"), "flash")
    if flash.get("eraseAll") is not False:
        raise ManifestError("stable installation requires eraseAll=false")
    files = flash.get("files")
    if not isinstance(files, list) or not files:
        raise ManifestError("flash.files must contain at least one artifact")

    artifacts: list[FirmwareArtifact] = []
    errors: list[str] = []
    for index, value in enumerate(files):
        artifact, artifact_errors = _artifact(value, index)
        errors.extend(artifact_errors)
        if artifact is not None:
            artifacts.append(artifact)

    roles = [artifact.role for artifact in artifacts]
    if len(set(roles)) != len(roles):
        errors.append("flash.files roles must be unique")

    ordered = sorted(artifacts, key=lambda artifact: artifact.address)
    for previous, current in zip(ordered, ordered[1:]):
        if current.address < previous.address + previous.size:
            errors.append(
                f"flash ranges overlap: {previous.role} and {current.role}"
            )

    if errors:
        raise ManifestError("; ".join(errors))

    return ReleaseManifest(
        release_id=_string(root.get("releaseId"), "releaseId"),
        hardware_profile_id=_string(
            root.get("hardwareProfileId"), "hardwareProfileId"
        ),
        chip_family=_string(root.get("chipFamily"), "chipFamily"),
        acceptance_status=expected_status,
        acceptance_report_id=report_id,
        artifacts=tuple(artifacts),
    )


def load_allowed_manifest(path: Path) -> ReleaseManifest:
    return _load_manifest(path, "allowed")


def load_candidate_manifest(path: Path) -> ReleaseManifest:
    return _load_manifest(path, "candidate")


def verify_release_artifacts(
    manifest: ReleaseManifest, release_root: Path
) -> tuple[FirmwareArtifact, ...]:
    resolved_root = release_root.resolve()
    for artifact in manifest.artifacts:
        path = (resolved_root / Path(artifact.path)).resolve()
        if not path.is_relative_to(resolved_root):
            raise ManifestError(f"artifact path escapes release root: {artifact.path}")
        try:
            payload = path.read_bytes()
        except OSError as error:
            raise ManifestError(f"cannot read artifact {artifact.path}: {error}") from error
        if len(payload) != artifact.size:
            raise ManifestError(
                f"artifact size mismatch for {artifact.role}: "
                f"expected {artifact.size}, got {len(payload)}"
            )
        actual = hashlib.sha256(payload).hexdigest()
        if actual != artifact.sha256:
            raise ManifestError(f"artifact SHA-256 mismatch for {artifact.role}")
    return manifest.artifacts
