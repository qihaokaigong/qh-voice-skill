from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from typing import Any, Protocol

from qh_voice_tool.config_wire import ConfigInputError, encode_device_config


class ProvisionError(RuntimeError):
    """Raised when the device refuses or cannot complete local provisioning."""


class SerialConnection(Protocol):
    def __enter__(self) -> "SerialConnection": ...

    def __exit__(self, *args: object) -> None: ...

    def write(self, payload: bytes) -> int: ...

    def flush(self) -> None: ...

    def readline(self) -> bytes: ...


SerialFactory = Callable[..., SerialConnection]


def _default_serial_factory(**kwargs: Any) -> SerialConnection:
    try:
        import serial
    except ImportError as error:
        raise ProvisionError(
            "pyserial is required; install the qh-voice-skill package dependencies"
        ) from error
    return serial.Serial(**kwargs)


def _read_response(connection: SerialConnection, expected: str) -> dict[str, Any]:
    for _ in range(20):
        raw = connection.readline()
        if not raw:
            continue
        try:
            response = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not isinstance(response, dict):
            continue
        if response.get("protocol") != "qh-voice-provision/1":
            continue
        if response.get("status") == "blocked":
            code = response.get("code", "device_rejected_request")
            raise ProvisionError(f"device blocked provisioning: {code}")
        if response.get("status") == expected:
            return response
    raise ProvisionError(f"device did not respond with {expected}")


def _write_all(connection: SerialConnection, payload: bytes) -> None:
    written = connection.write(payload)
    if written != len(payload):
        raise ProvisionError("serial write was incomplete")
    connection.flush()


def provision_device(
    port: str,
    config: Mapping[str, Any],
    *,
    serial_factory: SerialFactory | None = None,
    timeout_seconds: float = 2.0,
) -> dict[str, object]:
    if not port.strip():
        raise ProvisionError("serial port is required")
    try:
        payload = encode_device_config(config)
    except ConfigInputError:
        raise
    digest = hashlib.sha256(payload).hexdigest()
    factory = serial_factory or _default_serial_factory

    try:
        connection_context = factory(
            port=port, baudrate=115200, timeout=timeout_seconds
        )
        with connection_context as connection:
            _write_all(connection, b"QH_VOICE_STATUS\n")
            _read_response(connection, "ready")
            command = f"QH_VOICE_CONFIG {len(payload)} {digest}\n".encode("ascii")
            _write_all(connection, command)
            _read_response(connection, "send_payload")
            _write_all(connection, payload)
            response = _read_response(connection, "configured")
    except ProvisionError:
        raise
    except OSError as error:
        raise ProvisionError(f"cannot use serial port: {error}") from error

    return {
        "status": "configured",
        "rebootRequired": bool(response.get("rebootRequired", False)),
    }
