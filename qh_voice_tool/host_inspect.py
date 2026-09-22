from __future__ import annotations

import platform
from collections.abc import Callable, Iterable
from typing import Any, Protocol


class PortInfo(Protocol):
    device: str
    description: str
    vid: int | None
    pid: int | None


class HostInspectionError(RuntimeError):
    """Raised when the host cannot be inspected reliably."""


def _ports() -> Iterable[PortInfo]:
    try:
        from serial.tools import list_ports
    except ImportError as error:
        raise HostInspectionError(
            "pyserial is required for reliable serial-port inspection"
        ) from error
    return list_ports.comports()


def _host_id(system: str, machine: str) -> tuple[str, bool]:
    system_key = system.lower()
    machine_key = machine.lower()
    if system_key == "darwin" and machine_key in {"arm64", "aarch64"}:
        return "macos-arm64", True
    if system_key == "darwin" and machine_key in {"x86_64", "amd64"}:
        return "macos-x64", True
    if system_key == "windows" and machine_key in {"amd64", "x86_64"}:
        return "windows-x64", True
    label_system = "macos" if system_key == "darwin" else system_key
    return f"{label_system}-{machine_key}", False


def inspect_host(
    *,
    system: str | None = None,
    machine: str | None = None,
    ports_provider: Callable[[], Iterable[PortInfo]] = _ports,
) -> dict[str, Any]:
    host, supported = _host_id(system or platform.system(), machine or platform.machine())
    ports: list[dict[str, str | None]] = []
    for item in ports_provider():
        ports.append(
            {
                "port": item.device,
                "description": item.description,
                "vid": f"{item.vid:04x}" if item.vid is not None else None,
                "pid": f"{item.pid:04x}" if item.pid is not None else None,
            }
        )
    return {"host": host, "supported": supported, "ports": ports}
