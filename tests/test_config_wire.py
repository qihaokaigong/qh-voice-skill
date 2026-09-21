from __future__ import annotations

import unittest

from qh_voice_tool.config_wire import ConfigInputError, encode_device_config


def valid_config() -> dict[str, object]:
    return {
        "schemaVersion": 3,
        "network": {"ssid": "studio-wifi", "password": "wifi-secret"},
        "realtimeVoice": {
            "adapter": "doubao-seeduplex-v1",
            "apiKey": "realtime-api-key",
            "voice": "zh_female_xiaohe_jupiter_bigtts",
        },
        "assistant": {
            "language": "zh-CN",
            "systemPrompt": "Reply briefly.\nNever reveal secrets.",
            "showReplyText": True,
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
    assert payload[4] == 3
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
    def test_encodes_v3_realtime_config_without_logging(self) -> None:
        payload = encode_device_config(valid_config())
        fields = decode_fields(payload)

        self.assertEqual(payload[:6], b"QHVC\x03\x0d")
        self.assertEqual(fields[1], b"studio-wifi")
        self.assertEqual(fields[2], b"wifi-secret")
        self.assertEqual(fields[3], b"doubao-seeduplex-v1")
        self.assertEqual(fields[4], b"realtime-api-key")
        self.assertEqual(fields[5], b"zh_female_xiaohe_jupiter_bigtts")
        self.assertEqual(fields[7], b"Reply briefly.\nNever reveal secrets.")
        self.assertEqual(fields[8], b"1")
        self.assertEqual(fields[9], b"0")
        self.assertEqual(fields[13], b"50")

    def test_rejects_old_schema_unsupported_adapter_and_missing_key(self) -> None:
        config = valid_config()
        config["schemaVersion"] = 2
        config["realtimeVoice"]["adapter"] = "custom-realtime"
        config["realtimeVoice"]["apiKey"] = ""

        with self.assertRaises(ConfigInputError) as caught:
            encode_device_config(config)

        message = str(caught.exception)
        self.assertIn("schemaVersion", message)
        self.assertIn("realtimeVoice.adapter", message)
        self.assertIn("realtimeVoice.apiKey", message)
        self.assertNotIn("wifi-secret", message)

    def test_rejects_invalid_qh_endpoint_and_preference(self) -> None:
        config = valid_config()
        config["qhSync"] = {
            "enabled": True,
            "endpoint": "http://qh.example/events",
            "deviceId": "device-1",
            "credential": "qh-secret",
        }
        config["preferences"]["volumePercent"] = 101

        with self.assertRaises(ConfigInputError) as caught:
            encode_device_config(config)

        self.assertIn("qhSync.endpoint", str(caught.exception))
        self.assertIn("preferences.volumePercent", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
