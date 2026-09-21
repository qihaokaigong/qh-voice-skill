from __future__ import annotations

import unittest

from qh_voice_tool.interactive_config import collect_config, configure_interactively


class InteractiveConfigTest(unittest.TestCase):
    def answers(self) -> list[str]:
        return [
            "studio-wifi",
            "",
            "",
            "yes",
            "50",
            "no",
        ]

    def test_collects_one_provider_key_through_hidden_prompt(self) -> None:
        answers = iter(self.answers())
        hidden = iter(["wifi-secret", "realtime-secret"])
        visible_prompts: list[str] = []
        hidden_prompts: list[str] = []

        config = collect_config(
            input_fn=lambda prompt: visible_prompts.append(prompt) or next(answers),
            secret_fn=lambda prompt: hidden_prompts.append(prompt) or next(hidden),
            output_fn=lambda _: None,
        )

        self.assertEqual(config["network"]["password"], "wifi-secret")
        self.assertEqual(config["realtimeVoice"]["apiKey"], "realtime-secret")
        self.assertEqual(len(hidden_prompts), 2)
        self.assertNotIn("stt", config)
        self.assertNotIn("reply", config)
        self.assertNotIn("tts", config)
        all_prompts = " ".join(visible_prompts + hidden_prompts)
        self.assertNotIn("wifi-secret", all_prompts)
        self.assertNotIn("realtime-secret", all_prompts)

    def test_explains_where_realtime_credential_comes_from(self) -> None:
        answers = iter(self.answers())
        hidden = iter(["wifi-secret", "realtime-secret"])
        guidance: list[str] = []
        hidden_prompts: list[str] = []

        collect_config(
            input_fn=lambda _: next(answers),
            secret_fn=lambda prompt: hidden_prompts.append(prompt) or next(hidden),
            output_fn=guidance.append,
        )

        self.assertIn("Doubao realtime voice API Key", " ".join(hidden_prompts))
        help_text = " ".join(guidance)
        self.assertIn("console.volcengine.com/speech/", help_text)
        self.assertIn("API Key", help_text)
        self.assertNotIn("Access Token", help_text)
        self.assertNotIn("reply Provider", help_text)

    def test_can_enable_qh_sync_without_mixing_provider_credentials(self) -> None:
        answers = iter(
            self.answers()[:-1]
            + [
                "yes",
                "https://qh.example/api/v1/conversation-events",
                "device-1",
            ]
        )
        hidden = iter(["wifi-secret", "realtime-secret", "qh-device-token"])

        config = collect_config(
            input_fn=lambda _: next(answers),
            secret_fn=lambda _: next(hidden),
            output_fn=lambda _: None,
        )

        self.assertEqual(
            config["qhSync"],
            {
                "enabled": True,
                "endpoint": "https://qh.example/api/v1/conversation-events",
                "deviceId": "device-1",
                "credential": "qh-device-token",
            },
        )
        self.assertNotEqual(
            config["qhSync"]["credential"],
            config["realtimeVoice"]["apiKey"],
        )

    def test_provisions_in_memory_and_returns_only_redacted_result(self) -> None:
        answers = iter(self.answers())
        hidden = iter(["wifi-secret", "realtime-secret"])
        received: list[tuple[str, dict[str, object]]] = []

        result = configure_interactively(
            "COM7",
            input_fn=lambda _: next(answers),
            secret_fn=lambda _: next(hidden),
            output_fn=lambda _: None,
            provisioner=lambda port, config: (
                received.append((port, config))
                or {
                    "status": "configured",
                    "rebootRequired": False,
                    "deviceRestarting": True,
                }
            ),
        )

        self.assertEqual(result["status"], "configured")
        self.assertEqual(received[0][0], "COM7")
        self.assertNotIn("wifi-secret", str(result))
        self.assertNotIn("realtime-secret", str(result))


if __name__ == "__main__":
    unittest.main()
