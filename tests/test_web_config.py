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
            "stt_api_key": "asr-secret",
            "stt_resource_id": "volc.seedasr.sauc.duration",
            "stt_endpoint": "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel",
            "reply_provider": "ark",
            "reply_endpoint": "",
            "reply_model": "doubao-model-endpoint-id",
            "reply_api_key": "reply-secret",
            "tts_endpoint": "https://openspeech.bytedance.com/api/v3/tts/unidirectional/sse",
            "tts_speaker": "zh_female_vv_uranus_bigtts",
            "tts_api_key": "tts-secret",
            "system_prompt": "请用简洁的中文回答。",
            "max_reply_chars": "120",
            "volume_percent": "50",
        }

    def test_renders_chinese_form_with_safe_provider_defaults(self) -> None:
        module = self.module()
        page = module.render_config_page("COM7", "/configure/one-time-token")

        self.assertIn("配置 QH 语音助手", page)
        self.assertIn("已检测到设备", page)
        self.assertIn("Wi-Fi 名称", page)
        self.assertIn("豆包语音识别 API Key", page)
        self.assertIn("火山方舟", page)
        self.assertIn(
            "https://ark.cn-beijing.volces.com/api/v3/chat/completions", page
        )
        self.assertIn("豆包语音合成 API Key", page)
        self.assertIn("写入设备", page)
        self.assertIn('autocomplete="off"', page)
        self.assertNotIn("wifi-secret", page)
        self.assertNotIn("localStorage", page)
        self.assertNotIn("sessionStorage", page)

    def test_builds_v2_config_and_uses_ark_endpoint_preset(self) -> None:
        module = self.module()
        config = module.build_device_config(self.form())

        self.assertEqual(config["schemaVersion"], 2)
        self.assertEqual(config["network"]["password"], "wifi-secret")
        self.assertEqual(config["stt"]["apiKey"], "asr-secret")
        self.assertEqual(
            config["stt"]["resourceId"], "volc.seedasr.sauc.duration"
        )
        self.assertEqual(
            config["reply"]["endpoint"],
            "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
        )
        self.assertEqual(config["reply"]["credential"], "reply-secret")
        self.assertEqual(config["tts"]["credential"], "tts-secret")
        self.assertEqual(config["qhSync"]["enabled"], False)

    def test_custom_reply_provider_requires_a_full_https_endpoint(self) -> None:
        module = self.module()
        form = self.form()
        form["reply_provider"] = "custom"
        form["reply_endpoint"] = ""

        with self.assertRaisesRegex(module.WebConfigError, "回复接口"):
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
                        headers={
                            "Content-Type": "application/x-www-form-urlencoded"
                        },
                    )
                    with urllib.request.urlopen(request, timeout=5) as opened_page:
                        response["body"] = opened_page.read().decode("utf-8")
                        response["cache"] = opened_page.headers["Cache-Control"]
                        response["csp"] = opened_page.headers[
                            "Content-Security-Policy"
                        ]
                except BaseException as error:  # pragma: no cover - surfaced below
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
        self.assertNotIn("asr-secret", str(response))


if __name__ == "__main__":
    unittest.main()
