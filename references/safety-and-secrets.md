# Safety and secrets

Provider credentials and Wi-Fi passwords are user-owned runtime configuration. They may exist in the temporary local page/process memory and the target ESP32 configuration partition. They must not enter:

- Agent messages or retained context;
- command-line arguments or shell history;
- QH pages, APIs, databases, logs, analytics, or support attachments;
- public source, precompiled firmware, Release archives, or diagnostics;
- ordinary status responses from the device.

The local tool should return only a redacted configuration state. If a user pastes a credential into chat, stop copying or logging it and tell the user to revoke and replace it.

The configuration page must remain loopback-only, use an unguessable one-time
path, load no third-party resources, disable caching, and stop after a
successful write or timeout. It must never prefill old device secrets or echo
submitted secrets into the response. The page is a temporary input surface,
not a persistent Gateway.

This is a development-board release, not a production secure element. Document that a person with physical access and specialist tools may extract device-side credentials. Recommend separate, revocable, quota-limited credentials. Do not add a second security mode or enable irreversible eFuse operations.
