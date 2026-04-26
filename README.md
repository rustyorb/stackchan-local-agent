# StackChan Local Agent

Local voice-agent infrastructure for M5Stack StackChan.

This repo is intended to sit beside the firmware fork, not replace it. The
firmware fork handles ESP32-S3 code and flashing. This repo handles the local
AI bridge, provider configuration, and reusable integration pieces for a
self-hosted StackChan assistant.

## Current Shape

- `bridge/server-xz/`: known-good minimal XiaoZhi-compatible local bridge.
  It handles OTA bootstrap, WebSocket hello/listen events, and a local provider
  config dashboard at `http://192.168.0.250:8003/`.
- `scripts/`: firmware helper scripts copied from the working StackChan fork.
- `firmware-patches/`: local XiaoZhi firmware patch set used by the fork.
- `third_party/dotty-stackchan/`: attribution and integration notes for the
  Dotty project by Brett Kinny, plus a vendored provider snapshot under
  `third_party/dotty-stackchan/source/`.

## Goal

Replace the fragile vendor cloud path with a local, configurable pipeline:

```text
StackChan firmware
  -> local XiaoZhi-compatible server
  -> STT provider
  -> LLM provider
  -> TTS/Opus provider
  -> StackChan speaker + face
```

The short-term path is to keep `bridge/server-xz` as the provisioning and
debugging bridge, then adopt the already-working provider architecture from
`BrettKinny/dotty-stackchan`.

## Dotty Provider Snapshot

Dotty provider source has been pulled into:

```text
third_party/dotty-stackchan/source/custom-providers/
```

To copy those providers into a local `xiaozhi-esp32-server` checkout:

```powershell
.\scripts\sync-dotty-providers.bat -TargetRoot U:\_Projects\xiaozhi-esp32-server
```

See `docs/dotty-provider-integration.md` for the current integration notes.

## Real Server Checkpoint

The current real-server bring-up is documented in:

```text
docs/real-server-bringup.md
```

Start the real XiaoZhi server with:

```powershell
.\scripts\start-real-server.bat
```

It serves OTA on `http://192.168.0.250:8003/xiaozhi/ota/` and WebSocket on
`ws://192.168.0.250:8000/xiaozhi/v1/`.

The same real server also serves a local settings GUI at:

```text
http://192.168.0.250:8003/
```

The GUI edits the ignored XiaoZhi live config so provider URLs, keys, models,
voices, robot name, and personality prompt stay local.

## Attribution

This project includes work inspired by and/or derived from:

- `BrettKinny/dotty-stackchan`
- `xinnan-tech/xiaozhi-esp32-server`
- `m5stack/StackChan`

See `NOTICE.md` and `third_party/dotty-stackchan/README.md`.

## Local Secrets

Do not commit local API keys or Wi-Fi credentials. The local dashboard writes
bridge provider secrets to:

```text
bridge/server-xz/config.local.json
```

The real XiaoZhi server GUI writes provider secrets to:

```text
U:\_Projects\xiaozhi-esp32-server\main\xiaozhi-server\data\.config.yaml
```

Both files are ignored by git.
