# Architecture

## Current Bootstrapping Path

```text
StackChan firmware
  -> OTA URL: http://192.168.0.250:8003/xiaozhi/ota/
  -> bridge/server-xz
  -> WebSocket: ws://192.168.0.250:8003/xiaozhi/v1/
```

`bridge/server-xz` currently proves:

- device can skip vendor activation
- device can connect to a LAN server
- server receives microphone Opus frames
- server can send XiaoZhi-compatible `stt`, `llm`, and `tts` JSON
- local dashboard can safely hold provider config

## Target Production Path

```text
StackChan firmware
  -> xiaozhi-esp32-server
  -> ASR: faster-whisper or FunASR
  -> LLM: OpenAI-compatible or ZeroClaw
  -> TTS: Piper, EdgeTTS, OpenAI, or ElevenLabs
  -> Opus frames back to StackChan
```

## Repo Boundary

Keep firmware source in the firmware fork. Keep local runtime, provider
configuration, and server integration here.
