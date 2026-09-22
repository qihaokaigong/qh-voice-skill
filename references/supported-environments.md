# Supported environments

## Target release matrix

| Host | Architecture | Status |
| --- | --- | --- |
| macOS | arm64 | Target; end-to-end acceptance not yet complete |
| Windows | x64 | Target; end-to-end acceptance not yet complete |
| Linux | any | Detect and report only; do not flash |

The only target device profile is `qh.voice-kit.breadboard.n16r8.v1`, based on the recorded ESP32-S3 N16R8 reference build. A ROM identity that says ESP32-S3 does not prove the exact board, Flash size, PSRAM configuration, wiring, or safe profile match.

The source tool now implements host inspection, Release verification, a guarded
non-erasing esptool plan/apply path, a framework-free Chinese loopback
configuration page, and SHA-256 checked serial provisioning. The page uses the
system browser and Python standard library on both target hosts. These paths
have automated host tests, but have not completed clean-machine acceptance on
macOS arm64 or Windows x64.

The current firmware build implements the direct-Provider voice path and
compiles for the target profile. One reference device has completed a real
Provider turn with screen output and continuous buffered playback, including
the backpressure fix. This is single-device candidate evidence, not clean-host,
recovery, reconnect, or stable-Release acceptance. No stable installation may
be claimed yet.

The separately named candidate Flash commands support maintainer acceptance
work after exact board identification. They do not convert an unlisted host,
including the current Intel macOS development machine, into a supported
end-user environment.
