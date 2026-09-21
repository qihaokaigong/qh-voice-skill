from __future__ import annotations

import unittest

from qh_voice_tool.interactive_config import collect_config, configure_interactively


class InteractiveConfigTest(unittest.TestCase):
    def answers(self) -> list[str]:
        return [
            "studio-wifi",
            "app-key",
            "",
            "https://api.example.com/v1",
            "reply-model",
            "",
            "speaker-id",
            "",
            "",
            "",
        ]

    def test_collects_non_secret_fields_and_uses_hidden_prompts_for_secrets(self) -> None:
        answers = iter(self.answers())
        hidden = iter(
            ["wifi-secret", "asr-secret", "reply-secret", "tts-secret"]
        )
        visible_prompts: list[str] = []
        hidden_prompts: list[str] = []

        config = collect_config(
            input_fn=lambda prompt: (
                visible_prompts.append(prompt) or next(answers)
            ),
            secret_fn=lambda prompt: (
                hidden_prompts.append(prompt) or next(hidden)
            ),
            output_fn=lambda _: None,
        )

        self.assertEqual(config["network"]["password"], "wifi-secret")
        self.assertEqual(config["stt"]["credential"], "asr-secret")
        self.assertEqual(config["reply"]["credential"], "reply-secret")
        self.assertEqual(config["tts"]["credential"], "tts-secret")
        self.assertEqual(len(hidden_prompts), 4)
        all_prompts = " ".join(visible_prompts + hidden_prompts)
        for secret in ("wifi-secret", "asr-secret", "reply-secret", "tts-secret"):
            self.assertNotIn(secret, all_prompts)

    def test_provisions_in_memory_and_returns_only_redacted_result(self) -> None:
        answers = iter(self.answers())
        hidden = iter(
            ["wifi-secret", "asr-secret", "reply-secret", "tts-secret"]
        )
        received: list[tuple[str, dict[str, object]]] = []

        result = configure_interactively(
            "COM7",
            input_fn=lambda _: next(answers),
            secret_fn=lambda _: next(hidden),
            output_fn=lambda _: None,
            provisioner=lambda port, config: (
                received.append((port, config))
                or {"status": "configured", "rebootRequired": True}
            ),
        )

        self.assertEqual(result, {"status": "configured", "rebootRequired": True})
        self.assertEqual(received[0][0], "COM7")
        self.assertEqual(received[0][1]["network"]["password"], "wifi-secret")
        self.assertNotIn("wifi-secret", str(result))


if __name__ == "__main__":
    unittest.main()
