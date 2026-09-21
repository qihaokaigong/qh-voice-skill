from __future__ import annotations

import argparse
import json
from pathlib import Path

from qh_voice_tool.config_wire import ConfigInputError
from qh_voice_tool.flash import (
    FlashError,
    apply_candidate_flash,
    apply_flash,
    build_candidate_flash_plan,
    build_flash_plan,
)
from qh_voice_tool.host_inspect import inspect_host
from qh_voice_tool.interactive_config import configure_interactively
from qh_voice_tool.provision import ProvisionError
from qh_voice_tool.release_manifest import (
    ManifestError,
    load_allowed_manifest,
    verify_release_artifacts,
)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="qh-voice")
    commands = root.add_subparsers(dest="command", required=True)
    release = commands.add_parser("release")
    release_commands = release.add_subparsers(dest="release_command", required=True)
    verify = release_commands.add_parser("verify")
    verify.add_argument("--manifest", required=True, type=Path)
    verify.add_argument("--root", required=True, type=Path)
    verify.add_argument("--json", action="store_true")
    flash = commands.add_parser("flash")
    flash_commands = flash.add_subparsers(dest="flash_command", required=True)
    for name in ("plan", "apply", "candidate-plan", "candidate-apply"):
        operation = flash_commands.add_parser(name)
        operation.add_argument("--manifest", required=True, type=Path)
        operation.add_argument("--root", required=True, type=Path)
        operation.add_argument("--port", required=True)
        operation.add_argument("--json", action="store_true")
        if name in ("apply", "candidate-apply"):
            operation.add_argument("--confirm-release-id", required=True)
        if name == "candidate-apply":
            operation.add_argument("--confirm-hardware-profile-id", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("--json", action="store_true")
    configure = commands.add_parser("configure")
    configure.add_argument("--port", required=True)
    return root


def emit(payload: dict[str, object], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return
    print(payload.get("message", payload.get("status", "")))


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    if arguments.command == "inspect":
        result = inspect_host()
        result["status"] = "supported" if result["supported"] else "unsupported"
        result["message"] = (
            f"Host {result['host']}; detected {len(result['ports'])} serial port(s)"
        )
        emit(result, arguments.json)
        return 0 if result["supported"] else 2
    if arguments.command == "configure":
        try:
            result = configure_interactively(arguments.port)
        except (ConfigInputError, ProvisionError, ValueError) as error:
            emit(
                {
                    "status": "blocked",
                    "code": "configuration_blocked",
                    "message": str(error),
                },
                False,
            )
            return 2
        emit(
            {
                **result,
                "message": (
                    "Configuration written directly; the device is restarting"
                    if result.get("deviceRestarting")
                    else "Configuration written directly to the device"
                ),
            },
            False,
        )
        return 0
    if arguments.command == "release" and arguments.release_command == "verify":
        try:
            manifest = load_allowed_manifest(arguments.manifest)
            artifacts = verify_release_artifacts(manifest, arguments.root)
        except ManifestError as error:
            emit(
                {
                    "status": "blocked",
                    "code": "invalid_release_manifest",
                    "message": str(error),
                },
                arguments.json,
            )
            return 2
        emit(
            {
                "status": "verified",
                "releaseId": manifest.release_id,
                "hardwareProfileId": manifest.hardware_profile_id,
                "chipFamily": manifest.chip_family,
                "artifacts": [artifact.role for artifact in artifacts],
                "message": f"Verified {manifest.release_id}",
            },
            arguments.json,
        )
        return 0
    if arguments.command == "flash":
        try:
            is_candidate = arguments.flash_command.startswith("candidate-")
            builder = build_candidate_flash_plan if is_candidate else build_flash_plan
            plan = builder(arguments.manifest, arguments.root, arguments.port)
            if arguments.flash_command == "apply":
                apply_flash(plan, arguments.confirm_release_id)
            elif arguments.flash_command == "candidate-apply":
                apply_candidate_flash(
                    plan,
                    arguments.confirm_release_id,
                    arguments.confirm_hardware_profile_id,
                )
        except FlashError as error:
            emit(
                {
                    "status": "blocked",
                    "code": "flash_blocked",
                    "message": str(error),
                },
                arguments.json,
            )
            return 2
        if arguments.flash_command in ("plan", "candidate-plan"):
            emit(
                {
                    "status": "candidate_planned" if is_candidate else "planned",
                    "releaseId": plan.release_id,
                    "hardwareProfileId": plan.hardware_profile_id,
                    "acceptanceStatus": plan.acceptance_status,
                    "port": plan.port,
                    "command": list(plan.command),
                    "message": f"Flash plan ready for {plan.release_id}",
                },
                arguments.json,
            )
        else:
            emit(
                {
                    "status": "candidate_flashed" if is_candidate else "flashed",
                    "releaseId": plan.release_id,
                    "hardwareProfileId": plan.hardware_profile_id,
                    "acceptanceStatus": plan.acceptance_status,
                    "port": plan.port,
                    "message": f"Flashed {plan.release_id}",
                },
                arguments.json,
            )
        return 0
    return 2
