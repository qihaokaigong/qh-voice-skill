# Provider credential guide

Read this before starting `qh-voice configure`. Provider credentials must be
entered only in the local hidden prompts. Never paste them into an Agent chat,
command-line argument, issue, screenshot, or QH Platform form.

## Do not confuse these four values

| Local prompt | What it means | Where it comes from |
| --- | --- | --- |
| Doubao ASR App ID | The voice application identifier; some older examples call it APPKEY | The selected application in the Doubao Voice console |
| Doubao ASR Access Token | The token attached to that voice application | The same application details page |
| Doubao TTS API Key | The current V3 TTS `X-Api-Key` credential | API Key management in the current Doubao Voice console |
| Reply Provider API key | The credential for the selected OpenAI-compatible text model | That Provider's own console |

The ASR Access Token is **not** the general Volcengine account AccessKey
ID/Secret pair (AK/SK). Do not enter an account AK or Secret Access Key into the
ASR prompt.

## Doubao ASR

1. Sign in to the [Doubao Voice console](https://console.volcengine.com/speech/app).
2. Complete the account requirements shown by the console, including identity
   verification when required.
3. Create or select a voice application.
4. Enable the big-model streaming speech-recognition service for that
   application. The current firmware uses the streaming-input endpoint and the
   `volc.bigasr.sauc.duration` resource.
5. In the application details, copy:
   - **APP ID** into `Doubao ASR App ID`;
   - **Access Token** into `Doubao ASR Access Token`.

Official Doubao documentation describes these as the application identifier
and token used by the big-model streaming ASR SDK. Older examples may display
the identifier as `APPKEY`; the local prompt calls it App ID and explains both
labels.

## Doubao TTS

The current firmware uses the V3 SSE API with `X-Api-Key` and resource
`seed-tts-2.0`.

1. In the current Doubao Voice console, enable **豆包语音合成模型 2.0**.
2. Open **API Key 管理** and create or copy an API Key authorized for that
   service.
3. Enter it into `Doubao TTS API key`.
4. Use a speaker authorized for `seed-tts-2.0`. The default local prompt uses
   `zh_female_vv_uranus_bigtts`.

The [official V3 TTS API documentation](https://docs.volcengine.com/docs/DoubaoVoice/HTTPChunkedSSEUnidirectionalStreaming-V3?lang=zh)
states that the new-console path uses `X-Api-Key`. If the console only exposes
the old APP ID + Access Token combination, do not guess which value to enter;
switch to the current API Key flow or stop for adapter compatibility work.

## Reply Provider

The reply step is independent of Doubao ASR and TTS. Obtain these three values
from the chosen OpenAI-compatible Provider:

- an HTTPS chat-completions-compatible endpoint;
- the exact model ID enabled for the account;
- that Provider's API key.

Do not reuse a Doubao Voice token unless the selected reply Provider's official
documentation explicitly says it is the same credential.
