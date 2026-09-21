# Provider credential guide

Read this before starting `qh-voice configure`. The credential must be entered
only in the temporary Chinese local page opened by that command. Never paste it
into an Agent chat, command-line argument, issue, screenshot, or QH Platform
form. The page is served from `127.0.0.1`, sends the completed configuration
directly to the ESP32 over USB, and closes after the write.

## Values required by the current flow

| Local page field | What it means | Where it comes from |
| --- | --- | --- |
| Doubao realtime voice API Key | The key sent to Seeduplex as `X-Api-Key` | **API Key 管理** in the current Doubao Voice console |
| Voice ID | The response voice authorized for the realtime model | The realtime voice service or voice list in the same console |

The supported flow does **not** ask for APP ID, Access Token, account-level
AccessKey ID/Secret Key (AK/SK), a separate ASR key, an OpenAI-compatible reply
key, or a separate TTS key.

## How to obtain the key

1. Sign in to the [current Doubao Voice console](https://console.volcengine.com/speech/).
2. Open **开通管理** and enable **豆包实时语音模型 3.0（Seeduplex）** for the selected project.
3. Open **API Key 管理** in the console navigation.
4. Create a key, or copy an existing key that the console shows as authorized for that project and realtime voice service.
5. Confirm an authorized voice ID. The local page provides the product default, but the console is authoritative when the account uses another voice.
6. Enter both values only in the local configuration page.

If an application detail page only shows an APP ID, leave that page and open
**API Key 管理**. Do not substitute APP ID, Access Token, AK/SK, or a key from an
unrelated model service.

Use a separate, revocable, quota-limited key for the development board. The
current board does not contain a secure element; a person with physical access
and specialist tools may be able to extract device-side configuration.
