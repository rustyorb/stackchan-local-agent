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
  Dotty project by Brett Kinny.

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

## Attribution

This project includes work inspired by and/or derived from:

- `BrettKinny/dotty-stackchan`
- `xinnan-tech/xiaozhi-esp32-server`
- `m5stack/StackChan`

See `NOTICE.md` and `third_party/dotty-stackchan/README.md`.

## Local Secrets

Do not commit local API keys or Wi-Fi credentials. The local dashboard writes
provider secrets to:

```text
bridge/server-xz/config.local.json
```

That file is ignored by git.
