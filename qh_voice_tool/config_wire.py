from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from urllib.parse import urlsplit


MAXIMUM_WIRE_BYTES = 8192
WIRE_VERSION = 3
WIRE_FIELD_COUNT = 13


class ConfigInputError(ValueError):
    """Raised when local configuration cannot be safely sent to the device."""


def _object(value: Any, path: str, errors: list[str]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        errors.append(f"{path} must be an object")
        return {}
    return value


def _string(
    value: Any, path: str, errors: list[str], *, required: bool = True
) -> str:
    if not isinstance(value, str):
        errors.append(f"{path} must be a string")
        return ""
    if required and not value.strip():
        errors.append(f"{path} is required")
    return value


def _integer(value: Any, path: str, errors: list[str]) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        errors.append(f"{path} must be an integer")
        return 0
    return value


def _boolean(value: Any, path: str, errors: list[str]) -> bool:
    if not isinstance(value, bool):
        errors.append(f"{path} must be a boolean")
        return False
    return value


def _secure_endpoint(value: str, path: str, errors: list[str]) -> None:
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or bool(parsed.fragment)
        or any(character.isspace() for character in value)
    ):
        errors.append(f"{path} must use https without embedded credentials")


def _field(output: bytearray, field_id: int, value: str) -> None:
    encoded = value.encode("utf-8")
    if len(encoded) > 65535:
        raise ConfigInputError(f"field {field_id} exceeds 65535 UTF-8 bytes")
    output.append(field_id)
    output.extend(len(encoded).to_bytes(2, "big"))
    output.extend(encoded)


def encode_device_config(config: Mapping[str, Any]) -> bytes:
    errors: list[str] = []
    if config.get("schemaVersion") != 3:
        errors.append("schemaVersion must be 3")

    network = _object(config.get("network"), "network", errors)
    realtime = _object(config.get("realtimeVoice"), "realtimeVoice", errors)
    assistant = _object(config.get("assistant"), "assistant", errors)
    qh_sync = _object(config.get("qhSync"), "qhSync", errors)
    preferences = _object(config.get("preferences"), "preferences", errors)

    show_reply_text = _boolean(
        assistant.get("showReplyText"), "assistant.showReplyText", errors
    )
    qh_enabled = _boolean(qh_sync.get("enabled"), "qhSync.enabled", errors)
    volume = _integer(
        preferences.get("volumePercent"), "preferences.volumePercent", errors
    )
    if not 0 <= volume <= 100:
        errors.append("preferences.volumePercent must be between 0 and 100")

    values = {
        1: _string(network.get("ssid"), "network.ssid", errors),
        2: _string(network.get("password"), "network.password", errors),
        3: _string(realtime.get("adapter"), "realtimeVoice.adapter", errors),
        4: _string(realtime.get("apiKey"), "realtimeVoice.apiKey", errors),
        5: _string(realtime.get("voice"), "realtimeVoice.voice", errors),
        6: _string(assistant.get("language"), "assistant.language", errors),
        7: _string(
            assistant.get("systemPrompt"),
            "assistant.systemPrompt",
            errors,
            required=False,
        ),
        8: "1" if show_reply_text else "0",
        9: "1" if qh_enabled else "0",
        10: _string(
            qh_sync.get("endpoint"),
            "qhSync.endpoint",
            errors,
            required=qh_enabled,
        ),
        11: _string(
            qh_sync.get("deviceId"),
            "qhSync.deviceId",
            errors,
            required=qh_enabled,
        ),
        12: _string(
            qh_sync.get("credential"),
            "qhSync.credential",
            errors,
            required=qh_enabled,
        ),
        13: str(volume),
    }

    if values[3] != "doubao-seeduplex-v1":
        errors.append("realtimeVoice.adapter is unsupported")
    if qh_enabled:
        _secure_endpoint(values[10], "qhSync.endpoint", errors)

    if errors:
        raise ConfigInputError("; ".join(dict.fromkeys(errors)))

    output = bytearray(b"QHVC\x03\x0d")
    for field_id in range(1, WIRE_FIELD_COUNT + 1):
        _field(output, field_id, values[field_id])
    if len(output) > MAXIMUM_WIRE_BYTES:
        raise ConfigInputError(
            f"encoded configuration exceeds {MAXIMUM_WIRE_BYTES} bytes"
        )
    return bytes(output)
