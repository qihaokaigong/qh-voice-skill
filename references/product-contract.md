# Product contract

The product has one runtime path:

```text
ESP32 microphone
  -> user-selected STT Provider
  -> user-selected reply Provider
  -> user-selected TTS Provider
  -> ESP32 speaker
```

QH Platform stores only user-authorized structured device and conversation data. It does not possess, proxy, or forward Provider credentials or default inference requests. QH availability must not decide whether the current conversation can complete.

The installation computer and Agent are needed only for installation, configuration changes, diagnostics, recovery, and adapter development. After configuration, the ESP32 starts the firmware automatically on power-up.

There is no local or cloud Voice Gateway path. Adding one requires an explicit product-baseline change, not a local implementation choice.
