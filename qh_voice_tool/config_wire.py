from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from urllib.parse import urlsplit


MAXIMUM_WIRE_BYTES = 8192


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


def _secure_endpoint(
    value: str, path: str, scheme: str, errors: list[str]
) -> None:
    parsed = urlsplit(value)
    if (
        parsed.scheme != scheme
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or bool(parsed.fragment)
        or any(character.isspace() for character in value)
    ):
        errors.append(f"{path} must use {scheme} without embedded credentials")


def _field(output: bytearray, field_id: int, value: str) -> None:
    encoded = value.encode("utf-8")
    if len(encoded) > 65535:
        raise ConfigInputError(f"field {field_id} exceeds 65535 UTF-8 bytes")
    output.append(field_id)
    output.extend(len(encoded).to_bytes(2, "big"))
    output.extend(encoded)


def encode_device_config(config: Mapping[str, Any]) -> bytes:
    errors: list[str] = []
    if config.get("schemaVersion") != 1:
        errors.append("schemaVersion must be 1")

    network = _object(config.get("network"), "network", errors)
    stt = _object(config.get("stt"), "stt", errors)
    reply = _object(config.get("reply"), "reply", errors)
    tts = _object(config.get("tts"), "tts", errors)
    assistant = _object(config.get("assistant"), "assistant", errors)
    qh_sync = _object(config.get("qhSync"), "qhSync", errors)
    preferences = _object(config.get("preferences"), "preferences", errors)

    values = {
        1: _string(network.get("ssid"), "network.ssid", errors),
        2: _string(network.get("password"), "network.password", errors),
        3: _string(stt.get("adapter"), "stt.adapter", errors),
        4: _string(stt.get("endpoint"), "stt.endpoint", errors),
        5: _string(stt.get("appKey"), "stt.appKey", errors),
        6: _string(stt.get("credential"), "stt.credential", errors),
        7: _string(stt.get("resourceId"), "stt.resourceId", errors),
        8: _string(reply.get("adapter"), "reply.adapter", errors),
        9: _string(reply.get("endpoint"), "reply.endpoint", errors),
        10: _string(reply.get("model"), "reply.model", errors),
        11: _string(reply.get("credential"), "reply.credential", errors),
        12: _string(tts.get("adapter"), "tts.adapter", errors),
        13: _string(tts.get("endpoint"), "tts.endpoint", errors),
        14: _string(tts.get("credential"), "tts.credential", errors),
        15: _string(tts.get("resourceId"), "tts.resourceId", errors),
        16: _string(tts.get("speaker"), "tts.speaker", errors),
        17: _string(assistant.get("language"), "assistant.language", errors),
        18: _string(
            assistant.get("systemPrompt"),
            "assistant.systemPrompt",
            errors,
            required=False,
        ),
    }
    max_reply_chars = _integer(
        assistant.get("maxReplyChars"), "assistant.maxReplyChars", errors
    )
    if not 1 <= max_reply_chars <= 1000:
        errors.append("assistant.maxReplyChars must be between 1 and 1000")
    values[19] = str(max_reply_chars)

    enabled = qh_sync.get("enabled")
    if not isinstance(enabled, bool):
        errors.append("qhSync.enabled must be a boolean")
        enabled = False
    values[20] = "1" if enabled else "0"
    values[21] = _string(
        qh_sync.get("endpoint"), "qhSync.endpoint", errors, required=enabled
    )
    values[22] = _string(
        qh_sync.get("deviceId"), "qhSync.deviceId", errors, required=enabled
    )
    values[23] = _string(
        qh_sync.get("credential"), "qhSync.credential", errors, required=enabled
    )

    volume = _integer(
        preferences.get("volumePercent"), "preferences.volumePercent", errors
    )
    if not 0 <= volume <= 100:
        errors.append("preferences.volumePercent must be between 0 and 100")
    values[24] = str(volume)

    _secure_endpoint(values[4], "stt.endpoint", "wss", errors)
    _secure_endpoint(values[9], "reply.endpoint", "https", errors)
    _secure_endpoint(values[13], "tts.endpoint", "https", errors)
    if values[3] != "doubao-asr-v1":
        errors.append("stt.adapter is unsupported")
    if values[8] != "openai-compatible-v1":
        errors.append("reply.adapter is unsupported")
    if values[12] != "doubao-tts-v1":
        errors.append("tts.adapter is unsupported")
    if enabled:
        _secure_endpoint(values[21], "qhSync.endpoint", "https", errors)

    if errors:
        raise ConfigInputError("; ".join(dict.fromkeys(errors)))

    output = bytearray(b"QHVC\x01\x18")
    for field_id in range(1, 25):
        _field(output, field_id, values[field_id])
    if len(output) > MAXIMUM_WIRE_BYTES:
        raise ConfigInputError(
            f"encoded configuration exceeds {MAXIMUM_WIRE_BYTES} bytes"
        )
    return bytes(output)
