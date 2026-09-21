# Product contract

The product has one runtime path:

```text
ESP32 microphone
  -> Doubao Realtime Voice Model 3.0 (Seeduplex), one WebSocket session
  -> ESP32 speaker and ST7789 screen
```

The first release uses push-to-talk half-duplex interaction. The device sends
16 kHz mono PCM while the button is held and plays the Provider's 24 kHz PCM
response after release. The Provider performs speech recognition, dialogue,
and speech generation in the same session; users do not configure separate
ASR, LLM, or TTS endpoints.

The ST7789 screen is mandatory. It must show boot, setup, connection, idle,
recording, waiting, playback, success, and recoverable error information. A
black screen is a release-blocking defect even if serial logs work.

QH Platform stores only user-authorized structured device and conversation
data. It does not possess, proxy, or forward the Doubao API Key or raw audio.
QH availability must not decide whether the current conversation can complete.

The installation computer and Agent are needed only for installation,
configuration changes, diagnostics, recovery, and adapter development. After
configuration, the ESP32 starts automatically on power-up.

There is no local or cloud Voice Gateway path. Adding one requires an explicit
product-baseline change, not a local implementation choice.
