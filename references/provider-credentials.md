# Provider credential guide

Read this before starting `qh-voice configure`. Provider credentials must be
entered only in the local hidden prompts. Never paste them into an Agent chat,
command-line argument, issue, screenshot, or QH Platform form.

## Values required by the current flow

| Local prompt | What it means | Where it comes from |
| --- | --- | --- |
| Doubao ASR API Key | The new-console key sent as `X-Api-Key` | **API Key 管理** in the current Doubao Voice console |
| Doubao TTS API Key | A new-console key authorized for TTS V3 | **API Key 管理** in the current Doubao Voice console |
| Reply Provider API key | The credential for the selected OpenAI-compatible text model | That Provider's own console |

The current flow does **not** ask for APP ID, Access Token, or the general
Volcengine account AccessKey ID/Secret Key pair (AK/SK). Do not substitute any
of those values for an API Key.

## Doubao ASR

1. Sign in to the [current Doubao Voice console](https://console.volcengine.com/speech/).
2. Open **开通管理** and enable **大模型流式语音识别** for the selected
   project. The firmware currently uses resource
   `volc.bigasr.sauc.duration`.
3. Open **API Key 管理** in the console's left navigation.
4. Create a key, or copy an existing key that is authorized for the selected
   project and ASR service.
5. Enter the value only when the local tool displays
   `Doubao ASR API Key (hidden)`.

If the page you are viewing only shows an APP ID, do not keep searching that
application detail page for an Access Token. Go to **API Key 管理** instead.
The official current API documentation separates the new-console
`X-Api-Key` flow from the legacy APP ID + Access Token flow.

## Doubao TTS

The current firmware uses the V3 SSE API with `X-Api-Key` and resource
`seed-tts-2.0`.

1. In **开通管理**, enable **豆包语音合成模型 2.0**.
2. In **API Key 管理**, create or copy a key authorized for that service.
3. Enter it only when the local tool displays `Doubao TTS API Key (hidden)`.
4. Use a speaker authorized for `seed-tts-2.0`. The default prompt uses
   `zh_female_vv_uranus_bigtts`.

The ASR and TTS prompts remain separate so the tool does not silently broaden
the permissions of either key. A user may enter the same value in both hidden
prompts only when the console explicitly shows that key is authorized for both
services.

Official references:

- [Doubao Voice current console guide](https://www.volcengine.com/docs/6561/2485392?lang=zh)
- [Doubao ASR API new-console `X-Api-Key` example](https://www.volcengine.com/docs/6561/1631584?lang=zh)
- [Doubao TTS V3 API](https://docs.volcengine.com/docs/DoubaoVoice/HTTPChunkedSSEUnidirectionalStreaming-V3?lang=zh)

## Reply Provider

The reply step is independent of Doubao ASR and TTS. Obtain these three values
from the chosen OpenAI-compatible Provider:

- an HTTPS chat-completions-compatible endpoint;
- the exact model ID enabled for the account;
- that Provider's API key.

Do not reuse a Doubao Voice key unless the selected reply Provider's official
documentation explicitly says it is the same credential.
