---
name: qh-voice-skill
description: Install, configure, diagnose, or adapt the QH Voice Kit on supported ESP32-S3 hardware without requiring Arduino IDE, a local Voice Gateway, or secrets in the Agent conversation.
---

# QH Voice Skill

Use this Skill for the single supported product path: verify a QH Voice Kit release, flash it to the exact supported ESP32-S3 profile, write user-owned runtime configuration directly to the device, and verify a real voice conversation.

## User experience contract

This is an installed Skill, not a repository tutorial. Treat the directory
containing this `SKILL.md` as the Skill root and resolve all bundled scripts and
references from that directory, regardless of the Agent's current working
directory.

The Agent owns source discovery, isolated runtime setup, dependency preparation,
and execution of the bundled deterministic tools. Do not ask the user to clone
`qh-voice-skill` or `qh-voice-kit`, locate source files, copy commands, or manage
an internal working directory. Do not ask the user to install or configure Python.
If the Agent cannot prepare a supported internal runtime, report the concrete
blocker and stop at that stage.

The user-facing flow begins after the Skill is installed. The user should only
need to connect the device, answer hardware questions, approve an exact Flash
plan, enter secrets in the local Chinese page, and perform physical acceptance
checks. Internal commands and paths may appear in diagnostic evidence when
needed, but never as setup homework for the user.

Read [the product contract](references/product-contract.md) before changing the path or adding a component. Read [supported environments](references/supported-environments.md) before selecting host tools. For release or flash work, read [the release contract](references/release-contract.md). For any secret-bearing configuration, read [safety and secrets](references/safety-and-secrets.md).

Before asking a user to configure Provider fields, read
[the Provider credential guide](references/provider-credentials.md). Explain
where the required Doubao Realtime Voice Model 3.0 (Seeduplex) API Key and
voice ID come from. Do not request APP ID, Access Token, account-level AK/SK,
a separate ASR key, a reply-model key, or a TTS key in the supported flow. Do
not start configuration until the user knows which console service must be
enabled.

## Workflow

1. Inspect the host, Agent capabilities, USB devices, and exact hardware profile without changing state.
2. Resolve one `allowed` QH Voice Kit release for that profile.
3. Verify its Manifest, file sizes, hashes, paths, and non-overlapping Flash ranges with the bundled deterministic tool.
4. Show the exact device, release, files, addresses, preserved regions, and recovery effect before asking for the flash confirmation.
5. Flash only through the versioned tool. Never invent an address, accept an arbitrary URL, or convert an unsupported environment into a trial run.
6. Start the temporary Chinese local configuration page. Provider credentials and Wi-Fi passwords go directly from the loopback page to the device and never into the Agent conversation or QH Platform. If the browser does not open automatically, give the user the printed one-time `127.0.0.1` URL.
7. After the device confirms the transactional write, let it restart automatically. Do not ask the user to launch a computer-side service or manually start the firmware.
8. Run layered health checks for configuration, Wi-Fi, clock sync, realtime Provider session, microphone streaming, response audio, playback, screen state, and optional QH structured-data sync.
9. Report observed tool results separately from unverified advice. Leave recoverable failures at the failed stage.

During pre-release hardware acceptance, keep the Release marked `candidate`.
Use only `flash candidate-plan` to produce the preview. After the user confirms
the exact candidate Release ID and hardware Profile ID, use
`flash candidate-apply` with both confirmations. Never route a candidate through
the stable `verify`, `plan`, or `apply` commands, and never describe a successful
candidate flash as an accepted Release.

Intel macOS (`x86_64`) is a supported host and is the environment in which the
reference candidate was flashed, configured through the local page, and given
a real voice-turn acceptance test. Do not stop merely because the Mac is Intel.
Continue through the same deterministic flash workflow and the existing
`configure --port` browser flow; do not replace it with a command-line form or
a new installer.

## Agent-internal deterministic commands

In the examples below, `<skill-root>` is the absolute directory containing this
`SKILL.md`. Run these commands yourself from an Agent-managed runtime; do not
instruct the user to execute them.

Inspect the host and serial ports:

```text
python3 <skill-root>/scripts/qh_voice.py inspect --json
```

Verify an accepted Release and preview its exact non-erasing Flash plan:

```text
python3 <skill-root>/scripts/qh_voice.py release verify \
  --manifest <release>/release-manifest.json \
  --root <release> \
  --json

python3 <skill-root>/scripts/qh_voice.py flash plan \
  --manifest <release>/release-manifest.json \
  --root <release> \
  --port <serial-port> \
  --json
```

After showing that plan and receiving confirmation for the exact Release:

```text
python3 <skill-root>/scripts/qh_voice.py flash apply \
  --manifest <release>/release-manifest.json \
  --root <release> \
  --port <serial-port> \
  --confirm-release-id <release-id> \
  --json
```

Candidate acceptance uses the isolated commands below and requires both exact
identifiers at apply time:

```text
python3 <skill-root>/scripts/qh_voice.py flash candidate-plan \
  --manifest <release>/release-manifest.json \
  --root <release> \
  --port <serial-port> \
  --json

python3 <skill-root>/scripts/qh_voice.py flash candidate-apply \
  --manifest <release>/release-manifest.json \
  --root <release> \
  --port <serial-port> \
  --confirm-release-id <candidate-release-id> \
  --confirm-hardware-profile-id <hardware-profile-id> \
  --json
```

Open the temporary Chinese local page and write its configuration directly to
the flashed device:

```text
python3 <skill-root>/scripts/qh_voice.py configure --port <serial-port>
```

The page is bound to `127.0.0.1`, uses a random one-time path, loads no
third-party assets, disables caching, and keeps secrets out of terminal output.
It exits after the device confirms the write or after ten minutes. This is a
short-lived configuration UI, not a Voice Gateway; the computer-side process
does not remain running after configuration.

The current `qh-voice-kit` firmware contains a direct Seeduplex WebSocket voice
loop, mandatory screen state UI, and best-effort structured-event upload to QH.
One reference device has completed a real voice, display, and buffered-playback
acceptance turn, but the build remains a candidate, not an accepted
voice-assistant Release. Do not generalize that single-device result or bypass
the `acceptance.status=allowed` gate. Clean-host macOS/Windows acceptance,
layered recovery checks, durable QH retry/outbox behavior, packaged distribution,
and Provider adaptation automation remain under development.
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
