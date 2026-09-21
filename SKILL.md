---
name: qh-voice-skill
description: Install, configure, diagnose, or adapt the QH Voice Kit on supported ESP32-S3 hardware without requiring Arduino IDE, a local Voice Gateway, or secrets in the Agent conversation.
---

# QH Voice Skill

Use this Skill for the single supported product path: verify a QH Voice Kit release, flash it to the exact supported ESP32-S3 profile, write user-owned runtime configuration directly to the device, and verify a real voice conversation.

Read [the product contract](references/product-contract.md) before changing the path or adding a component. Read [supported environments](references/supported-environments.md) before selecting host tools. For release or flash work, read [the release contract](references/release-contract.md). For any secret-bearing configuration, read [safety and secrets](references/safety-and-secrets.md).

## Workflow

1. Inspect the host, Agent capabilities, USB devices, and exact hardware profile without changing state.
2. Resolve one `allowed` QH Voice Kit release for that profile.
3. Verify its Manifest, file sizes, hashes, paths, and non-overlapping Flash ranges with the bundled deterministic tool.
4. Show the exact device, release, files, addresses, preserved regions, and recovery effect before asking for the flash confirmation.
5. Flash only through the versioned tool. Never invent an address, accept an arbitrary URL, or convert an unsupported environment into a trial run.
6. Start the temporary local configuration input. Provider credentials and Wi-Fi passwords go directly to the device and never into the Agent conversation or QH Platform.
7. Run layered health checks for configuration, Wi-Fi, STT, reply, TTS, playback, and optional QH structured-data sync.
8. Report observed tool results separately from unverified advice. Leave recoverable failures at the failed stage.

## Deterministic commands

Inspect the host and serial ports:

```text
python3 scripts/qh_voice.py inspect --json
```

Verify an accepted Release and preview its exact non-erasing Flash plan:

```text
python3 scripts/qh_voice.py release verify \
  --manifest <release>/release-manifest.json \
  --root <release> \
  --json

python3 scripts/qh_voice.py flash plan \
  --manifest <release>/release-manifest.json \
  --root <release> \
  --port <serial-port> \
  --json
```

After showing that plan and receiving confirmation for the exact Release:

```text
python3 scripts/qh_voice.py flash apply \
  --manifest <release>/release-manifest.json \
  --root <release> \
  --port <serial-port> \
  --confirm-release-id <release-id> \
  --json
```

Collect secrets through hidden local terminal input and write them directly to
the flashed device:

```text
python3 scripts/qh_voice.py configure --port <serial-port>
```

The current `qh-voice-kit` firmware is a candidate provisioning build, not an
accepted voice-assistant Release. Do not bypass the `acceptance.status=allowed`
gate to flash it as a stable user Release. Layered health checks, recovery, the
complete direct-Provider voice loop, QH synchronization, packaged macOS/Windows
distribution, and Provider adaptation automation remain under development.
Until their deterministic commands and acceptance evidence exist, explain the
missing capability and stop before that stage. Do not substitute ad hoc
`esptool`, Arduino IDE, or generated shell commands.

## Non-negotiable boundaries

- Do not install, start, or suggest a Voice Gateway, local Python voice service, local Whisper model, or user cloud Gateway.
- Do not request Provider Key, Wi-Fi password, QH password, or long-lived token in chat, shell arguments, logs, or issue reports.
- Do not send Provider credentials or raw audio to QH Platform.
- Do not enable Secure Boot, Flash Encryption, or irreversible eFuse settings in the current development-board release.
- Do not claim a compile, simulated response, or USB identification is a successful real voice conversation.
- Stop before writing when the board identity, release acceptance, Flash layout, serial target, power state, or user confirmation is unresolved.

For an incompatible Provider, gather its official versioned API documentation without credentials, constrain changes to the target adapter and its fixtures, run contract and firmware builds, show the diff, and require confirmation before flashing the modified firmware.
