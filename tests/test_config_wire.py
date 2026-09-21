from __future__ import annotations

import unittest

from qh_voice_tool.config_wire import ConfigInputError, encode_device_config


def valid_config() -> dict[str, object]:
    return {
        "schemaVersion": 2,
        "network": {"ssid": "studio-wifi", "password": "wifi-secret"},
        "stt": {
            "adapter": "doubao-asr-v1",
            "endpoint": "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel",
            "apiKey": "asr-api-key",
            "resourceId": "volc.bigasr.sauc.duration",
        },
        "reply": {
            "adapter": "openai-compatible-v1",
            "endpoint": "https://api.example.com/v1",
            "model": "reply-model",
            "credential": "reply-secret",
        },
        "tts": {
            "adapter": "doubao-tts-v1",
            "endpoint": "https://openspeech.bytedance.com/api/v3/tts/unidirectional/sse",
            "credential": "tts-secret",
            "resourceId": "seed-tts-2.0",
            "speaker": "speaker-id",
        },
        "assistant": {
            "language": "zh-CN",
            "systemPrompt": "Reply briefly.\nNever reveal secrets.",
            "maxReplyChars": 120,
        },
        "qhSync": {
            "enabled": False,
            "endpoint": "",
            "deviceId": "",
            "credential": "",
        },
        "preferences": {"volumePercent": 50},
    }


def decode_fields(payload: bytes) -> dict[int, bytes]:
    assert payload[:4] == b"QHVC"
    assert payload[4] == 2
    cursor = 6
    fields: dict[int, bytes] = {}
    for _ in range(payload[5]):
        field_id = payload[cursor]
        size = int.from_bytes(payload[cursor + 1 : cursor + 3], "big")
        cursor += 3
        fields[field_id] = payload[cursor : cursor + size]
        cursor += size
    assert cursor == len(payload)
    return fields


class ConfigWireTest(unittest.TestCase):
    def test_encodes_device_compatible_tlv_without_logging(self) -> None:
        payload = encode_device_config(valid_config())
        fields = decode_fields(payload)

        self.assertEqual(payload[:6], b"QHVC\x02\x17")
        self.assertEqual(fields[1], b"studio-wifi")
        self.assertEqual(fields[2], b"wifi-secret")
        self.assertEqual(fields[5], b"asr-api-key")
        self.assertEqual(fields[17], b"Reply briefly.\nNever reveal secrets.")
        self.assertEqual(fields[18], b"120")
        self.assertEqual(fields[19], b"0")
        self.assertEqual(fields[23], b"50")

    def test_rejects_wrong_transport_and_missing_secrets(self) -> None:
        config = valid_config()
        config["stt"]["endpoint"] = "https://openspeech.bytedance.com"
        config["stt"]["adapter"] = "unknown-asr"
        config["tts"]["endpoint"] += "#fragment"
        config["reply"]["credential"] = ""

        with self.assertRaises(ConfigInputError) as caught:
            encode_device_config(config)

        self.assertIn("stt.endpoint", str(caught.exception))
        self.assertIn("stt.adapter", str(caught.exception))
        self.assertIn("tts.endpoint", str(caught.exception))
        self.assertIn("reply.credential", str(caught.exception))
        self.assertNotIn("wifi-secret", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
