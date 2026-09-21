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
        "Doubao ASR: open https://console.volcengine.com/speech/, enable the "
        "streaming ASR service, then create or copy its API Key from API Key "
        "management."
    )
    output_fn(
        "Doubao TTS: create a TTS API Key in the current Doubao Voice console. "
        "Keep it separate from the ASR key unless the console explicitly "
        "authorizes one key for both."
    )
    output_fn(
        "For the reply Provider, prepare its HTTPS OpenAI-compatible endpoint, "
        "model ID, and API key."
    )
    ssid = _answer(input_fn, "Wi-Fi SSID")
    wifi_password = secret_fn("Wi-Fi password (hidden): ")
    stt_api_key = secret_fn("Doubao ASR API Key (hidden): ")
    stt_endpoint = _answer(
        input_fn,
        "Doubao ASR WebSocket endpoint",
        "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel",
    )
    reply_endpoint = _answer(input_fn, "OpenAI-compatible reply endpoint")
    reply_model = _answer(input_fn, "Reply model")
    reply_credential = secret_fn("Reply Provider API key (hidden): ")
    tts_endpoint = _answer(
        input_fn,
        "Doubao TTS endpoint",
        "https://openspeech.bytedance.com/api/v3/tts/unidirectional/sse",
    )
    tts_speaker = _answer(
        input_fn, "Doubao TTS speaker", "zh_female_vv_uranus_bigtts"
    )
    tts_credential = secret_fn("Doubao TTS API key (hidden): ")
    system_prompt = _answer(
        input_fn, "Assistant system prompt", "请用简洁的中文回答。"
    )
    max_reply_chars = int(_answer(input_fn, "Maximum reply characters", "120"))
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
        "schemaVersion": 2,
        "network": {"ssid": ssid, "password": wifi_password},
        "stt": {
            "adapter": "doubao-asr-v1",
            "endpoint": stt_endpoint,
            "apiKey": stt_api_key,
            "resourceId": "volc.bigasr.sauc.duration",
        },
        "reply": {
            "adapter": "openai-compatible-v1",
            "endpoint": reply_endpoint,
            "model": reply_model,
            "credential": reply_credential,
        },
        "tts": {
            "adapter": "doubao-tts-v1",
            "endpoint": tts_endpoint,
            "credential": tts_credential,
            "resourceId": "seed-tts-2.0",
            "speaker": tts_speaker,
        },
        "assistant": {
            "language": "zh-CN",
            "systemPrompt": system_prompt,
            "maxReplyChars": max_reply_chars,
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
