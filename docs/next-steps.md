# Next Steps

## 1. Fetch Dotty Reference Files

Run from normal PowerShell, not the Codex-hosted shell:

```powershell
cd U:\_Projects\stackchan-local-agent
.\scripts\fetch-dotty.ps1
```

The Codex shell currently cannot initialize the Windows network provider for
raw downloads, but normal PowerShell should work.

## 2. Bring Up XiaoZhi Server

Use `xiaozhi-esp32-server` as the real voice pipeline host. The minimal
`bridge/server-xz` server remains useful for device boot/provisioning tests,
but it should not become the production STT/TTS stack.

## 3. Install Dotty Providers

Copy or mount these files into the XiaoZhi server provider tree:

- `custom-providers/openai_compat/openai_compat.py`
- `custom-providers/asr/whisper_local.py`
- `custom-providers/asr/fun_local.py`
- `custom-providers/piper_local/piper_local.py`
- `custom-providers/edge_stream/edge_stream.py`
- `custom-providers/zeroclaw/zeroclaw.py`
- `custom-providers/textUtils.py`

Start with `OpenAICompat` + `StreamingEdgeTTS`. Move to local Piper or
faster-whisper once the cloud path speaks end-to-end.

## 4. Use The Example Config

Start from:

```text
config/xiaozhi-dotty.example.yaml
```

Replace IPs, model names, and environment variables as needed.

## 5. Keep Repo Boundaries Clean

- Firmware fork: ESP-IDF firmware and app-slot flashing.
- This repo: local server, provider config, bridge UI, Dotty integration notes.
- Do not commit full flash dumps, Wi-Fi credentials, API keys, or runtime DBs.
