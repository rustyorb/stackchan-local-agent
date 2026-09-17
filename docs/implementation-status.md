# Implementation status

This continues the existing `rustyorb/stackchan-local-agent` project from `7f63cfd377d81f1840db2a0f0d26335037401a90`. The research and original upgrade plan are preserved in [upgrade-plan.md](upgrade-plan.md). Mars's later requirement for independence from vendor services supersedes the earlier bootstrap proposal.

## Implemented in this branch

| Request | Delivered behavior |
|---|---|
| More time to finish speaking | Dashboard pause control from 1 to 30 seconds; default 6 seconds. |
| Control inactivity | Never by default; configurable 1 to 1440 minutes; independent farewell switch, off by default. Both server silence-close guards are patched. |
| Choose the model | LM Studio by default; OpenRouter only when explicitly selected. Credentials stay in the host configuration. |
| Local speech | Local faster-whisper, Silero VAD, and Piper assets; startup fails clearly when required assets are missing. |
| Retain earlier work | Existing bridge, persona, dashboard, and provider structure retained; structured conversation history survives the optional bridge relay. |
| Expressive eyes | Larger emerald irises, pupils, highlights, gaze, independent lids, six emotion mappings, and a smaller mouth. |
| Independent robot connection | Authenticated private LAN TLS WebSocket compiled into firmware; vendor activation/bootstrap and saved vendor endpoints bypassed. |
| Independent runtime | Vendor account/apps, public NTP, camera uploads, network updates, and asset downloads disabled in the active firmware paths. |
| Use existing ESP-IDF | Native build helper for the pinned commercial StackChan source and ESP-IDF 5.5.4; no automatic flashing. |

Settings are saved immediately and take effect when the voice server is recreated. Runtime palette selection, audio-driven lips, local vision, local time synchronization, and card-backed assets are later integrations, not claims about this build.

## Verification and limits

- Host and TLS regressions passed with the pinned upstream fixture available. Firmware helper unittest and compiled C++ eye geometry check also passed. No paid model calls were made.
- The idle integration fixture applies the actual patch to pinned upstream source and executes its close logic with a simulated clock. Never survives one simulated hour; finite timeout and farewell remain independently effective.
- Firmware patches apply cleanly to the pinned sources. Repeated preparation is idempotent. Eye geometry and endpoint-validation checks pass.
- Source review caught and fixed a Wi-Fi setup initialization ordering error. Wi-Fi setup now starts after the application and Wi-Fi manager are initialized.
- Final host review identified inherited cloud prompt enrichment, an implicit Whisper tokenizer download, and a provider mount mismatch; their fixes are included before delivery.

The full Docker service and ESP-IDF firmware have **not** been built or run in this workspace. No physical display, microphone, speaker, servo, model inference, network capture, or USB flash has been tested. This branch is ready for those bench checks, not a prebuilt firmware release.

Firmware revisions are pinned. Some upstream dependency references are tags rather than immutable commit IDs. Hardware timing and appearance still need measurement on the robot.

## Windows handoff

Use [the host setup](../README.md) and [the firmware build guide](../firmware/STAKIA-BUILD.md).

Still needed from the PC: private LAN IPv4 address and robot port identification. The latest screenshot shows ESP-IDF 6.1 and COM15 as USB Serial Device. Use ESP-IDF 5.5.4 for the pinned firmware and identify Stakia by a port unplug/replug check. The native build targets the commercial M5Stack StackChan K151/K151-R; verify the robot's controller matches before flashing.

Mars already has a maintained stock restore option and explicitly requested no stock rebuild or backup work. None is required by these scripts. The reported 32 GB removable card has not been inspected; the new renderer does not require it.

Changing the compiled host address currently requires rebuilding the firmware, so reserve the PC's LAN address in the router. The service now requires a private certificate and robot credential. The HTTP listener is disabled and the dashboard binds to localhost. It remains a LAN deployment.
