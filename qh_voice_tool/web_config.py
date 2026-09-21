from __future__ import annotations

import html
import secrets
import time
import webbrowser
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import parse_qs

from qh_voice_tool.config_wire import ConfigInputError, encode_device_config
from qh_voice_tool.provision import ProvisionError, provision_device


DEFAULT_VOICE = "zh_female_xiaohe_jupiter_bigtts"
MAXIMUM_FORM_BYTES = 65536

Provisioner = Callable[[str, Mapping[str, Any]], dict[str, object]]
BrowserOpener = Callable[[str], bool]
OutputFunction = Callable[[str], None]


class WebConfigError(ValueError):
    """Raised when the local browser configuration flow cannot continue."""


def _value(form: Mapping[str, Any], name: str, *, strip: bool = True) -> str:
    raw = form.get(name, "")
    if isinstance(raw, (list, tuple)):
        raw = raw[0] if raw else ""
    if not isinstance(raw, str):
        return ""
    return raw.strip() if strip else raw


def _required(
    form: Mapping[str, Any], name: str, label: str, *, strip: bool = True
) -> str:
    value = _value(form, name, strip=strip)
    if not value or (not strip and not value.strip()):
        raise WebConfigError(f"请填写{label}。")
    return value


def _integer(
    form: Mapping[str, Any], name: str, label: str, minimum: int, maximum: int
) -> int:
    value = _required(form, name, label)
    try:
        parsed = int(value)
    except ValueError as error:
        raise WebConfigError(f"{label}必须是数字。") from error
    if not minimum <= parsed <= maximum:
        raise WebConfigError(f"{label}必须在 {minimum} 到 {maximum} 之间。")
    return parsed


def _checked(form: Mapping[str, Any], name: str) -> bool:
    return _value(form, name).lower() in {"1", "true", "yes", "on"}


def build_device_config(form: Mapping[str, Any]) -> dict[str, Any]:
    qh_enabled = _checked(form, "qh_enabled")
    config: dict[str, Any] = {
        "schemaVersion": 3,
        "network": {
            "ssid": _required(form, "wifi_ssid", "Wi-Fi 名称", strip=False),
            "password": _required(
                form, "wifi_password", "Wi-Fi 密码", strip=False
            ),
        },
        "realtimeVoice": {
            "adapter": "doubao-seeduplex-v1",
            "apiKey": _required(
                form, "realtime_api_key", "豆包实时语音 API Key"
            ),
            "voice": _required(form, "voice", "豆包实时语音音色 ID"),
        },
        "assistant": {
            "language": "zh-CN",
            "systemPrompt": _value(form, "system_prompt", strip=False),
            "showReplyText": _checked(form, "show_reply_text"),
        },
        "qhSync": {
            "enabled": qh_enabled,
            "endpoint": (
                _required(form, "qh_endpoint", "QH 数据接口")
                if qh_enabled
                else ""
            ),
            "deviceId": (
                _required(form, "qh_device_id", "QH 设备 ID")
                if qh_enabled
                else ""
            ),
            "credential": (
                _required(form, "qh_token", "QH 设备写入令牌")
                if qh_enabled
                else ""
            ),
        },
        "preferences": {
            "volumePercent": _integer(
                form, "volume_percent", "扬声器音量", 0, 100
            )
        },
    }
    try:
        encode_device_config(config)
    except ConfigInputError as error:
        raise WebConfigError("请检查必填项、QH 接口地址和数值范围。") from error
    return config


def render_config_page(device_port: str, action_path: str) -> str:
    safe_port = html.escape(device_port, quote=True)
    safe_action = html.escape(action_path, quote=True)
    safe_voice = html.escape(DEFAULT_VOICE, quote=True)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>配置 QH 语音助手</title>
  <style>
    :root {{ color-scheme: light; font-family: -apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: #f4f6f8; color: #172033; }}
    main {{ width: min(720px, calc(100% - 32px)); margin: 32px auto 64px; }}
    .hero,.card {{ background: white; border: 1px solid #dfe4ea; border-radius: 16px; box-shadow: 0 8px 30px rgba(23,32,51,.06); }}
    .hero {{ padding: 28px; margin-bottom: 18px; }} .card {{ padding: 24px; margin: 14px 0; }}
    h1 {{ margin: 0 0 10px; font-size: 28px; }} h2 {{ margin: 0 0 18px; font-size: 19px; }}
    p {{ line-height: 1.65; margin: 8px 0; }}
    .device {{ margin-top: 18px; padding: 12px 14px; border-radius: 10px; background: #eef8f2; color: #17633a; font-weight: 650; }}
    .notice {{ color: #536176; font-size: 14px; }}
    label {{ display: block; font-weight: 650; margin: 14px 0 7px; }}
    input,textarea {{ width: 100%; border: 1px solid #bbc5d1; border-radius: 9px; padding: 11px 12px; font: inherit; background: white; }}
    input:focus,textarea:focus {{ outline: 3px solid rgba(36,100,235,.16); border-color: #2464eb; }}
    .help {{ display: block; margin-top: 6px; color: #66758b; font-size: 13px; line-height: 1.5; }}
    a {{ color: #1558d6; }} details {{ margin-top: 18px; border-top: 1px solid #e5e9ee; padding-top: 14px; }}
    summary {{ cursor: pointer; font-weight: 650; }}
    .check {{ display: flex; gap: 9px; align-items: center; font-weight: 600; }} .check input {{ width: auto; }}
    button {{ width: 100%; border: 0; border-radius: 11px; padding: 14px 18px; background: #1d5fe9; color: white; font: inherit; font-weight: 750; cursor: pointer; }}
    @media (max-width: 640px) {{ main {{ margin-top: 16px; }} .hero,.card {{ border-radius: 12px; }} }}
  </style>
</head>
<body><main>
  <section class="hero">
    <h1>配置 QH 语音助手</h1>
    <p>预计 2 分钟。信息会从这个本地页面直接通过 USB 写入 ESP32。</p>
    <p class="notice">QH 平台和 Agent 对话不会收到你的 Wi-Fi 密码或 Provider API Key。设备中的旧密钥不可读取，请重新填写。</p>
    <div class="device">已检测到设备：<span>{safe_port}</span></div>
  </section>

  <form method="post" action="{safe_action}" autocomplete="off">
    <section class="card">
      <h2>1. 连接网络</h2>
      <label for="wifi_ssid">Wi-Fi 名称</label>
      <input id="wifi_ssid" name="wifi_ssid" required maxlength="32" autocomplete="off">
      <label for="wifi_password">Wi-Fi 密码</label>
      <input id="wifi_password" name="wifi_password" type="password" required maxlength="64" autocomplete="new-password" spellcheck="false" autocapitalize="none">
    </section>

    <section class="card">
      <h2>2. 豆包实时语音模型 3.0</h2>
      <label for="realtime_api_key">豆包实时语音 API Key</label>
      <input id="realtime_api_key" name="realtime_api_key" type="password" required autocomplete="new-password" spellcheck="false" autocapitalize="none">
      <span class="help">先在豆包语音控制台的“开通管理”开通实时语音模型 3.0（Seeduplex），再到“API Key 管理”创建或复制授权 Key。不要填写 APP ID、Access Token 或账户 AK/SK。<a href="https://console.volcengine.com/speech/" target="_blank" rel="noreferrer noopener">打开控制台</a></span>
      <label for="voice">音色 ID</label>
      <input id="voice" name="voice" value="{safe_voice}" required maxlength="128" spellcheck="false">
      <span class="help">默认音色可直接使用；如账号开通的是其他音色，请填写控制台显示的准确 ID。</span>
    </section>

    <section class="card">
      <h2>3. 助手偏好</h2>
      <label for="system_prompt">助手提示词</label>
      <textarea id="system_prompt" name="system_prompt" rows="3" maxlength="2000">请用简洁的中文回答。</textarea>
      <label class="check"><input id="show_reply_text" name="show_reply_text" type="checkbox" checked>在屏幕显示识别和回复文字</label>
      <label for="volume_percent">扬声器音量（0–100）</label>
      <input id="volume_percent" name="volume_percent" type="number" min="0" max="100" value="50" required>

      <details>
        <summary>QH 数据同步（可选）</summary>
        <label class="check"><input id="qh_enabled" name="qh_enabled" type="checkbox">同步结构化对话事件</label>
        <span class="help">只同步文字和设备事件，不上传原始音频或豆包 API Key。</span>
        <label for="qh_endpoint">QH 数据接口</label>
        <input id="qh_endpoint" name="qh_endpoint" spellcheck="false">
        <label for="qh_device_id">QH 设备 ID</label>
        <input id="qh_device_id" name="qh_device_id" spellcheck="false">
        <label for="qh_token">QH 设备写入令牌</label>
        <input id="qh_token" name="qh_token" type="password" autocomplete="new-password" spellcheck="false">
      </details>
    </section>

    <section class="card">
      <button type="submit">写入设备</button>
      <p class="notice">提交后请保持 USB 连接。写入成功后设备会自动重启；电脑上不需要常驻运行任何程序。</p>
    </section>
  </form>
</main></body></html>"""


def _result_page(title: str, message: str, *, success: bool) -> str:
    safe_title = html.escape(title)
    safe_message = html.escape(message)
    accent = "#17633a" if success else "#9a3412"
    action = (
        "现在可以关闭此页面，等待设备重新启动。"
        if success
        else "请返回配置页检查后重新提交。"
    )
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{safe_title}</title>
<style>body{{margin:0;background:#f4f6f8;color:#172033;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif}}main{{width:min(560px,calc(100% - 32px));margin:64px auto;background:white;border:1px solid #dfe4ea;border-radius:16px;padding:32px}}h1{{color:{accent};margin-top:0}}p{{line-height:1.7}}</style></head>
<body><main><h1>{safe_title}</h1><p>{safe_message}</p><p>{action}</p></main></body></html>"""


@dataclass
class _SessionState:
    device_port: str
    action_path: str
    provisioner: Provisioner
    completed: bool = False
    result: dict[str, object] | None = None


def _handler_for(state: _SessionState) -> type[BaseHTTPRequestHandler]:
    class ConfigRequestHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            return

        def _send_html(self, status: int, page: str) -> None:
            payload = page.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Pragma", "no-cache")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'none'; style-src 'unsafe-inline'; "
                "form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
            )
            self.end_headers()
            self.wfile.write(payload)

        def _not_found(self) -> None:
            self._send_html(
                404, _result_page("页面已失效", "请重新启动配置。", success=False)
            )

        def do_GET(self) -> None:
            if self.path != state.action_path or state.completed:
                self._not_found()
                return
            self._send_html(
                200, render_config_page(state.device_port, state.action_path)
            )

        def do_POST(self) -> None:
            if self.path != state.action_path or state.completed:
                self._not_found()
                return
            content_type = self.headers.get("Content-Type", "")
            if not content_type.startswith("application/x-www-form-urlencoded"):
                self._send_html(
                    415,
                    _result_page(
                        "无法提交", "配置页面提交格式不正确。", success=False
                    ),
                )
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = 0
            if length <= 0 or length > MAXIMUM_FORM_BYTES:
                self._send_html(
                    413,
                    _result_page(
                        "无法提交", "配置内容为空或超过安全限制。", success=False
                    ),
                )
                return
            try:
                form = parse_qs(
                    self.rfile.read(length).decode("utf-8"),
                    keep_blank_values=True,
                    max_num_fields=24,
                    strict_parsing=False,
                )
                config = build_device_config(form)
                result = state.provisioner(state.device_port, config)
            except (UnicodeDecodeError, ValueError, ConfigInputError, ProvisionError) as error:
                message = (
                    str(error)
                    if isinstance(error, WebConfigError)
                    else "设备写入失败，请检查连接和配置后重试。"
                )
                self._send_html(
                    400, _result_page("配置未写入", message, success=False)
                )
                return

            state.result = result
            state.completed = True
            self._send_html(
                200,
                _result_page(
                    "配置已写入设备",
                    "ESP32 已接收并保存配置，设备正在重新启动。",
                    success=True,
                ),
            )

    return ConfigRequestHandler


def configure_in_browser(
    device_port: str,
    *,
    opener: BrowserOpener = webbrowser.open,
    output_fn: OutputFunction = print,
    provisioner: Provisioner = provision_device,
    timeout_seconds: float = 600,
) -> dict[str, object]:
    if not device_port.strip():
        raise WebConfigError("没有可用的设备串口。")
    if timeout_seconds <= 0:
        raise WebConfigError("配置页面等待时间必须大于零。")

    token = secrets.token_urlsafe(24)
    action_path = f"/configure/{token}"
    state = _SessionState(device_port, action_path, provisioner)
    server = HTTPServer(("127.0.0.1", 0), _handler_for(state))
    server.timeout = min(0.25, timeout_seconds)
    url = f"http://127.0.0.1:{server.server_port}{action_path}"
    output_fn("正在打开中文本地配置页面。")
    output_fn(f"如果浏览器没有自动打开，请访问：{url}")
    opener(url)

    deadline = time.monotonic() + timeout_seconds
    try:
        while not state.completed and time.monotonic() < deadline:
            server.handle_request()
    finally:
        server.server_close()
    if not state.completed or state.result is None:
        raise WebConfigError("配置页面等待超时，设备没有被修改。")
    return state.result
