# QH Voice Skill

Agent Skill and deterministic macOS/Windows installer tooling for
`qh-voice-kit`.

The Skill handles environment inspection, trusted Release verification,
guarded flashing, and local device provisioning. Provider credentials and the
Wi-Fi password are entered through hidden local prompts and sent directly to
the ESP32; they are not accepted as command-line arguments, written to a config
file, or sent to QH Platform.

## Development setup

```bash
uv sync
uv run qh-voice inspect --json
python3 -m unittest discover -s tests -v
```

The source commands are implemented, but there is no accepted end-user
`qh-voice-kit` Release yet. Configuration now causes the device to restart into
its saved runtime automatically; no computer-side process remains running.
Do not bypass the Release acceptance gate or claim that the direct-provider
voice loop has passed real-device verification.

Pre-release maintainers can use the separately named `flash candidate-plan`
and `flash candidate-apply` workflow. It requires exact confirmation of both
the candidate Release ID and hardware Profile ID and does not weaken the stable
Release gate.

See [`SKILL.md`](SKILL.md) for the Agent workflow and hard safety boundaries.
