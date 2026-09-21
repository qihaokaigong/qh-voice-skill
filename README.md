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

## Development setup

```bash
uv sync
uv run qh-voice inspect --json
python3 -m unittest discover -s tests -v
```

The source commands are implemented, but there is no accepted end-user
`qh-voice-kit` Release yet. Configuration now causes the device to restart into
its saved runtime automatically; no computer-side process remains running.
The configured firmware connects directly to Doubao Realtime Voice Model 3.0
(Seeduplex) with one device-owned API Key; users do not configure separate ASR,
reply, or TTS services. Do not bypass the Release acceptance gate or claim that
the realtime voice and screen flow has passed real-device verification.

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
