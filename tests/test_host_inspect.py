from __future__ import annotations

import unittest

from qh_voice_tool.host_inspect import inspect_host


class Port:
    def __init__(self, device: str, description: str, vid: int | None, pid: int | None):
        self.device = device
        self.description = description
        self.vid = vid
        self.pid = pid


class HostInspectTest(unittest.TestCase):
    def test_reports_supported_macos_and_serial_ports(self) -> None:
        result = inspect_host(
            system="Darwin",
            machine="arm64",
            ports_provider=lambda: [Port("/dev/cu.test", "USB UART", 0x10C4, 0xEA60)],
        )

        self.assertTrue(result["supported"])
        self.assertEqual(result["host"], "macos-arm64")
        self.assertEqual(result["ports"][0]["port"], "/dev/cu.test")
        self.assertEqual(result["ports"][0]["vid"], "10c4")
        self.assertEqual(result["ports"][0]["pid"], "ea60")

    def test_reports_unsupported_linux_without_guessing(self) -> None:
        result = inspect_host(
            system="Linux", machine="x86_64", ports_provider=lambda: []
        )

        self.assertFalse(result["supported"])
        self.assertEqual(result["host"], "linux-x86_64")
        self.assertEqual(result["ports"], [])


if __name__ == "__main__":
    unittest.main()
