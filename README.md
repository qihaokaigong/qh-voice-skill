# QH Voice Skill

Agent Skill and deterministic macOS/Windows installer tooling for
`qh-voice-kit`.

The Skill handles environment inspection, trusted Release verification,
guarded flashing, and local device provisioning. Provider credentials and the
Wi-Fi password are entered through a temporary Chinese page served only on
`127.0.0.1`, then sent directly to the ESP32 over USB. They are not accepted as
command-line arguments, written to a config file, or sent to QH Platform. The
same flow works on the target macOS and Windows hosts and requires no frontend
runtime or cloud configuration service.

Supported host detection includes macOS Intel (`x86_64`), macOS Apple Silicon
(`arm64`), and Windows x64. Intel macOS is the reference development host on
which candidate flashing, the local browser configuration page, and a complete
device voice turn were exercised. Firmware acceptance remains a separate
Release gate.

## User installation

In an AI Agent that supports installing Skills from GitHub, send:

```text
请安装这个 Skill：https://github.com/qihaokaigong/qh-voice-skill
```

After installation, start a new conversation and send:

```text
请使用 qh-voice-skill 帮我安装并配置 QH Voice Kit。
```

用户不需要克隆本仓库、查找源码目录、配置 Python 或复制下面的开发命令。Skill 和 Agent
负责准备内部运行环境、检查设备、验证 Release、展示烧录计划、执行已确认的烧录，并打开中文本地
配置页。用户只负责连接设备、确认硬件和烧录目标、在本地页面填写配置；出现问题时再反馈实际现象。

接线必须与当前固件的唯一 Hardware Profile 一致，完整供电、信号和喇叭端子表见
[`references/hardware-wiring.md`](references/hardware-wiring.md)。配置写入成功并自动重启后，安装流程结束；
只有用户主动要求验证或实际遇到问题时，Skill 才继续做针对性诊断。

## Development setup

This section is for Skill maintainers, not the end-user installation flow.

```bash
uv sync
uv run qh-voice inspect --json
python3 -m unittest discover -s tests -v
```

There is no accepted end-user `qh-voice-kit` Release yet. Configuration causes the device to restart into
its saved runtime automatically; no computer-side process remains running.
The configured firmware connects directly to Doubao Realtime Voice Model 3.0
(Seeduplex) with one device-owned API Key; users do not configure separate ASR,
reply, or TTS services. One reference device has completed a real voice,
display, and buffered-playback turn; this single candidate result must not be
described as an accepted stable Release or clean-host validation.

Pre-release maintainers can use the separately named `flash candidate-plan`
and `flash candidate-apply` workflow. It requires exact confirmation of both
the candidate Release ID and hardware Profile ID and does not weaken the stable
Release gate.

See [`SKILL.md`](SKILL.md) for the Agent workflow and hard safety boundaries.
See [`references/provider-credentials.md`](references/provider-credentials.md)
before collecting Provider configuration.

Start the local configuration page for an already flashed device with:

```bash
uv run qh-voice configure --port <serial-port>
```

The command opens the page automatically and prints a one-time local URL as a
fallback. After a successful write the temporary server exits; it is not a
Voice Gateway and does not need to remain running.
