# Dotty Provider Integration

This repo vendors the useful Dotty provider layer under:

```text
third_party/dotty-stackchan/source/
```

The copied source is kept separate from the local bridge so we can track what
came from Dotty before adapting it.

## Imported Pieces

- `custom-providers/openai_compat/`: OpenAI-compatible LLM provider for OpenAI,
  OpenRouter, Ollama, LM Studio, vLLM, and similar `/v1/chat/completions` APIs.
- `custom-providers/asr/`: local ASR providers for faster-whisper and FunASR.
- `custom-providers/edge_stream/`: streaming Edge TTS provider.
- `custom-providers/piper_local/`: local Piper TTS provider.
- `custom-providers/zeroclaw/`: bridge provider for a ZeroClaw-style local brain.
- `custom-providers/textUtils.py`: shared emoji and TTS text helpers.
- selected Dotty docs for architecture, protocol, voice pipeline, backend, and
  troubleshooting reference.

## Sync Into xiaozhi-esp32-server

After cloning `xinnan-tech/xiaozhi-esp32-server`, copy the provider bundle into
that checkout:

```powershell
cd U:\_Projects\stackchan-local-agent
.\scripts\sync-dotty-providers.bat -TargetRoot U:\_Projects\xiaozhi-esp32-server
```

Preview first:

```powershell
.\scripts\sync-dotty-providers.bat -TargetRoot U:\_Projects\xiaozhi-esp32-server -DryRun
```

The script writes:

```text
<xiaozhi-server>\custom-providers\
```

Use `config\xiaozhi-dotty.example.yaml` as the starting point for the server
configuration. Keep real API keys in environment variables or local ignored
config files, not in git.

## Current Direction

`bridge/server-xz` remains the small boot/debug bridge. The production voice
stack should move to `xiaozhi-esp32-server` plus these Dotty providers, with the
local dashboard eventually becoming the friendly editor for provider URL, API
key, model, voice, robot name, and persona prompt.
