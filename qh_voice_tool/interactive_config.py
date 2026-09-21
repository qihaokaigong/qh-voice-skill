from __future__ import annotations

import getpass
from collections.abc import Callable
from typing import Any

from qh_voice_tool.provision import provision_device


InputFunction = Callable[[str], str]
OutputFunction = Callable[[str], None]
Provisioner = Callable[[str, dict[str, Any]], dict[str, object]]


def _answer(input_fn: InputFunction, prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input_fn(f"{prompt}{suffix}: ").strip()
    return value or default


def collect_config(
    *,
    input_fn: InputFunction = input,
    secret_fn: InputFunction = getpass.getpass,
    output_fn: OutputFunction = print,
) -> dict[str, Any]:
    output_fn("Configuration stays in this process and is sent directly to the ESP32.")
    output_fn("Secrets are hidden and are never written to a configuration file.")
    output_fn(
        "Doubao realtime voice: open https://console.volcengine.com/speech/, "
        "enable Realtime Voice Model 3.0 (Seeduplex), then create or copy its "
        "API Key from API Key management."
    )
    ssid = _answer(input_fn, "Wi-Fi SSID")
    wifi_password = secret_fn("Wi-Fi password (hidden): ")
    realtime_api_key = secret_fn("Doubao realtime voice API Key (hidden): ")
    voice = _answer(
        input_fn,
        "Doubao realtime voice speaker",
        "zh_female_xiaohe_jupiter_bigtts",
    )
    system_prompt = _answer(
        input_fn, "Assistant system prompt", "请用简洁的中文回答。"
    )
    show_reply_choice = _answer(
        input_fn, "Show transcript and reply text on screen (yes/no)", "yes"
    ).lower()
    if show_reply_choice not in {"yes", "no"}:
        raise ValueError("screen text must be answered with yes or no")
    volume_percent = int(_answer(input_fn, "Speaker volume percent", "50"))
    qh_choice = _answer(
        input_fn, "Sync structured conversation events to QH (yes/no)", "no"
    ).lower()
    if qh_choice not in {"yes", "no"}:
        raise ValueError("QH sync must be answered with yes or no")
    qh_enabled = qh_choice == "yes"
    qh_endpoint = ""
    qh_device_id = ""
    qh_credential = ""
    if qh_enabled:
        qh_endpoint = _answer(input_fn, "QH conversation event endpoint")
        qh_device_id = _answer(input_fn, "QH device ID")
        qh_credential = secret_fn("QH device write token (hidden): ")

    return {
        "schemaVersion": 3,
        "network": {"ssid": ssid, "password": wifi_password},
        "realtimeVoice": {
            "adapter": "doubao-seeduplex-v1",
            "apiKey": realtime_api_key,
            "voice": voice,
        },
        "assistant": {
            "language": "zh-CN",
            "systemPrompt": system_prompt,
            "showReplyText": show_reply_choice == "yes",
        },
        "qhSync": {
            "enabled": qh_enabled,
            "endpoint": qh_endpoint,
            "deviceId": qh_device_id,
            "credential": qh_credential,
        },
        "preferences": {"volumePercent": volume_percent},
    }


def configure_interactively(
    port: str,
    *,
    input_fn: InputFunction = input,
    secret_fn: InputFunction = getpass.getpass,
    output_fn: OutputFunction = print,
    provisioner: Provisioner = provision_device,
) -> dict[str, object]:
    config = collect_config(
        input_fn=input_fn, secret_fn=secret_fn, output_fn=output_fn
    )
    return provisioner(port, config)
