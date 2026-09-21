# Supported environments

## Target release matrix

| Host | Architecture | Status |
| --- | --- | --- |
| macOS | arm64 | Target; end-to-end acceptance not yet complete |
| Windows | x64 | Target; end-to-end acceptance not yet complete |
| Linux | any | Detect and report only; do not flash |

The only target device profile is `qh.voice-kit.breadboard.n16r8.v1`, based on the recorded ESP32-S3 N16R8 reference build. A ROM identity that says ESP32-S3 does not prove the exact board, Flash size, PSRAM configuration, wiring, or safe profile match.

The source tool now implements host inspection, Release verification, a guarded
non-erasing esptool plan/apply path, hidden interactive configuration input, and
SHA-256 checked serial provisioning. These paths have automated host tests, but
have not completed clean-machine acceptance on macOS arm64 or Windows x64.

The current firmware build implements the direct-Provider voice path and
compiles for the target profile, but has not completed real-device Provider,
audio, health, or recovery acceptance. No stable installation may be claimed
yet.
