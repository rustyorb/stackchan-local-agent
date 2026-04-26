# Dotty StackChan Integration Notes

Source project:

https://github.com/BrettKinny/dotty-stackchan

License:

MIT, Copyright (c) 2026 Brett Kinny.

## Why It Matters

Dotty already solved several hard pieces of the local StackChan pipeline:

- OpenAI-compatible LLM provider for OpenAI, OpenRouter, Ollama, LM Studio,
  vLLM, and similar `/v1/chat/completions` APIs.
- Local ASR providers using FunASR and faster-whisper.
- Local and cloud TTS providers that produce Opus frames for the XiaoZhi voice
  pipeline.
- ZeroClaw bridge provider with streaming response support.
- Architecture docs for StackChan firmware -> xiaozhi-server -> bridge -> LLM.

## Files Worth Importing

- `custom-providers/openai_compat/openai_compat.py`
- `custom-providers/asr/whisper_local.py`
- `custom-providers/asr/fun_local.py`
- `custom-providers/piper_local/piper_local.py`
- `custom-providers/edge_stream/edge_stream.py`
- `custom-providers/zeroclaw/zeroclaw.py`
- `custom-providers/textUtils.py`
- `.config.yaml`
- `SETUP.md`
- `docs/architecture.md`
- `docs/voice-pipeline.md`
- `docs/protocols.md`

## Integration Direction

Do not keep growing `bridge/server-xz` into a full production voice stack.
It is useful as a bootstrapping and debugging bridge. The production direction
should be:

1. Run `xiaozhi-esp32-server` locally.
2. Add Dotty-style custom providers for ASR, LLM, and TTS.
3. Point StackChan firmware OTA/WebSocket config at that local server.
4. Reuse the local dashboard from `bridge/server-xz` as the human-friendly
   config surface.

## Attribution Rules

If Dotty source is copied into this repo, keep it under
`third_party/dotty-stackchan/` until it is intentionally adapted. When adapted,
preserve attribution in file headers or nearby docs and keep this notice.
