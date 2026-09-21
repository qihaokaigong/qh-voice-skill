# Provider credential guide

Read this before starting `qh-voice configure`. Provider credentials must be
entered only in the temporary Chinese local page opened by that command. Never
paste them into an Agent chat, command-line argument, issue, screenshot, or QH
Platform form. The local page is served from `127.0.0.1`, sends the completed
configuration directly to the ESP32 over USB, and closes after the write.

## Values required by the current flow

| Local page field | What it means | Where it comes from |
| --- | --- | --- |
| Doubao ASR API Key | The new-console key sent as `X-Api-Key` | **API Key 管理** in the current Doubao Voice console |
| Doubao TTS API Key | A new-console key authorized for TTS V3 | **API Key 管理** in the current Doubao Voice console |
| Reply Provider API key | The credential for the selected OpenAI-compatible text model | That Provider's own console |

The current flow does **not** ask for APP ID, Access Token, or the general
Volcengine account AccessKey ID/Secret Key pair (AK/SK). Do not substitute any
of those values for an API Key.

## Doubao ASR

1. Sign in to the [current Doubao Voice console](https://console.volcengine.com/speech/).
2. Open **开通管理** and enable a supported **大模型流式语音识别** service
   for the selected project. In the local page, choose the same version:
   `volc.seedasr.sauc.duration` for 2.0 小时版, or
   `volc.bigasr.sauc.duration` for 1.0 小时版.
3. Open **API Key 管理** in the console's left navigation.
4. Create a key, or copy an existing key that is authorized for the selected
   project and ASR service.
5. Enter the value only in the local page field **豆包语音识别 API Key**.

If the page you are viewing only shows an APP ID, do not keep searching that
application detail page for an Access Token. Go to **API Key 管理** instead.
The official current API documentation separates the new-console
`X-Api-Key` flow from the legacy APP ID + Access Token flow.

## Doubao TTS

The current firmware uses the V3 SSE API with `X-Api-Key` and resource
`seed-tts-2.0`.

1. In **开通管理**, enable **豆包语音合成模型 2.0**.
2. In **API Key 管理**, create or copy a key authorized for that service.
3. Enter it only in the local page field **豆包语音合成 API Key**.
4. Use a speaker authorized for `seed-tts-2.0`. The page defaults to
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

The reply step is independent of Doubao ASR and TTS. The local page defaults to
火山方舟 and fills its chat-completions endpoint automatically. For that path,
copy the exact model or inference endpoint ID and create an API key in the
火山方舟 API Key 管理 page.

For another OpenAI-compatible Provider, obtain these three values:

- an HTTPS chat-completions-compatible endpoint;
- the exact model ID enabled for the account;
- that Provider's API key.

Do not reuse a Doubao Voice key unless the selected reply Provider's official
documentation explicitly says it is the same credential.
