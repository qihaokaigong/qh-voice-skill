from __future__ import annotations

import importlib
import importlib.util
import threading
import unittest
import urllib.parse
import urllib.request


class WebConfigTest(unittest.TestCase):
    def module(self):
        spec = importlib.util.find_spec("qh_voice_tool.web_config")
        self.assertIsNotNone(spec, "中文本地网页配置模块尚未实现")
        return importlib.import_module("qh_voice_tool.web_config")

    def form(self) -> dict[str, str]:
        return {
            "wifi_ssid": "studio-wifi",
            "wifi_password": "wifi-secret",
            "realtime_api_key": "realtime-secret",
            "voice": "zh_female_xiaohe_jupiter_bigtts",
            "system_prompt": "请用简洁的中文回答。",
            "show_reply_text": "on",
            "volume_percent": "50",
        }

    def test_renders_chinese_form_for_one_realtime_provider(self) -> None:
        module = self.module()
        page = module.render_config_page("COM7", "/configure/one-time-token")

        self.assertIn("配置 QH 语音助手", page)
        self.assertIn("已检测到设备", page)
        self.assertIn("Wi-Fi 名称", page)
        self.assertIn("豆包实时语音 API Key", page)
        self.assertIn("实时语音模型 3.0", page)
        self.assertIn("音色", page)
        self.assertIn("在屏幕显示识别和回复文字", page)
        self.assertIn("写入设备", page)
        self.assertNotIn("OpenAI-compatible", page)
        self.assertNotIn("语音合成 API Key", page)
        self.assertNotIn("语音识别 API Key", page)
        self.assertNotIn("wifi-secret", page)
        self.assertNotIn("localStorage", page)
        self.assertNotIn("sessionStorage", page)

    def test_builds_v3_config_with_one_realtime_key(self) -> None:
        module = self.module()
        config = module.build_device_config(self.form())

        self.assertEqual(config["schemaVersion"], 3)
        self.assertEqual(config["network"]["password"], "wifi-secret")
        self.assertEqual(
            config["realtimeVoice"],
            {
                "adapter": "doubao-seeduplex-v1",
                "apiKey": "realtime-secret",
                "voice": "zh_female_xiaohe_jupiter_bigtts",
            },
        )
        self.assertTrue(config["assistant"]["showReplyText"])
        self.assertNotIn("stt", config)
        self.assertNotIn("reply", config)
        self.assertNotIn("tts", config)
        self.assertEqual(config["qhSync"]["enabled"], False)

    def test_requires_realtime_key_and_supported_voice(self) -> None:
        module = self.module()
        form = self.form()
        form["realtime_api_key"] = ""
        form["voice"] = ""

        with self.assertRaisesRegex(module.WebConfigError, "实时语音 API Key"):
            module.build_device_config(form)

    def test_loopback_page_posts_directly_to_provisioner_and_stops(self) -> None:
        module = self.module()
        opened: list[str] = []
        received: list[tuple[str, dict[str, object]]] = []
        response: dict[str, object] = {}
        client_errors: list[BaseException] = []
        client_threads: list[threading.Thread] = []

        def opener(url: str) -> bool:
            opened.append(url)

            def submit() -> None:
                try:
                    body = urllib.parse.urlencode(self.form()).encode("utf-8")
                    request = urllib.request.Request(
                        url,
                        data=body,
                        method="POST",
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                    )
                    with urllib.request.urlopen(request, timeout=5) as opened_page:
                        response["body"] = opened_page.read().decode("utf-8")
                        response["cache"] = opened_page.headers["Cache-Control"]
                        response["csp"] = opened_page.headers[
                            "Content-Security-Policy"
                        ]
                except BaseException as error:  # pragma: no cover
                    client_errors.append(error)

            thread = threading.Thread(target=submit)
            thread.start()
            client_threads.append(thread)
            return True

        result = module.configure_in_browser(
            "COM7",
            opener=opener,
            output_fn=lambda _: None,
            provisioner=lambda port, config: (
                received.append((port, config))
                or {
                    "status": "configured",
                    "rebootRequired": False,
                    "deviceRestarting": True,
                }
            ),
            timeout_seconds=5,
        )
        for thread in client_threads:
            thread.join(timeout=5)

        self.assertEqual(client_errors, [])
        self.assertEqual(result["status"], "configured")
        self.assertEqual(received[0][0], "COM7")
        self.assertEqual(received[0][1]["network"]["password"], "wifi-secret")
        self.assertTrue(opened[0].startswith("http://127.0.0.1:"))
        self.assertIn("配置已写入设备", str(response["body"]))
        self.assertEqual(response["cache"], "no-store")
        self.assertIn("default-src 'none'", str(response["csp"]))
        self.assertNotIn("wifi-secret", str(response))
        self.assertNotIn("realtime-secret", str(response))


if __name__ == "__main__":
    unittest.main()
