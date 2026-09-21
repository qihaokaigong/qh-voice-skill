from __future__ import annotations

import json
import unittest

from qh_voice_tool.provision import ProvisionError, provision_device
from test_config_wire import valid_config


class FakeSerial:
    def __init__(self) -> None:
        self.writes: list[bytes] = []
        self.responses: list[bytes] = []
        self.closed = False

    def __enter__(self) -> "FakeSerial":
        return self

    def __exit__(self, *_: object) -> None:
        self.closed = True

    def write(self, payload: bytes) -> int:
        self.writes.append(payload)
        if payload.startswith(b"QH_VOICE_STATUS"):
            self.responses.append(
                b'{"protocol":"qh-voice-provision/1","status":"ready",'
                b'"configured":false}\n'
            )
        elif payload.startswith(b"QH_VOICE_CONFIG"):
            self.responses.append(
                b'{"protocol":"qh-voice-provision/1",'
                b'"status":"send_payload"}\n'
            )
        elif payload.startswith(b"QHVC"):
            self.responses.append(
                b'{"protocol":"qh-voice-provision/1",'
                b'"status":"configured","rebootRequired":false,'
                b'"restarting":true}\n'
            )
        return len(payload)

    def flush(self) -> None:
        pass

    def readline(self) -> bytes:
        return self.responses.pop(0) if self.responses else b""


class ProvisionTest(unittest.TestCase):
    def test_writes_hashed_payload_and_returns_only_redacted_status(self) -> None:
        fake = FakeSerial()
        result = provision_device(
            "/dev/cu.test",
            valid_config(),
            serial_factory=lambda **_: fake,
        )

        self.assertEqual(result["status"], "configured")
        self.assertFalse(result["rebootRequired"])
        self.assertTrue(result["deviceRestarting"])
        command = fake.writes[1].decode("ascii")
        self.assertRegex(command, r"^QH_VOICE_CONFIG \d+ [0-9a-f]{64}\n$")
        self.assertTrue(fake.writes[2].startswith(b"QHVC"))
        serialized_result = json.dumps(result)
        for secret in ("wifi-secret", "asr-secret", "reply-secret", "tts-secret"):
            self.assertNotIn(secret, serialized_result)
        self.assertTrue(fake.closed)

    def test_blocks_when_device_does_not_confirm_protocol(self) -> None:
        fake = FakeSerial()
        fake.write = lambda payload: len(payload)  # type: ignore[method-assign]

        with self.assertRaisesRegex(ProvisionError, "did not respond"):
            provision_device(
                "COM9", valid_config(), serial_factory=lambda **_: fake
            )


if __name__ == "__main__":
    unittest.main()
