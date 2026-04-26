# Real XiaoZhi Server Bring-Up

The first real local voice server is checked out beside this repo:

```text
U:\_Projects\xiaozhi-esp32-server
```

Python dependencies are installed in:

```text
U:\_Projects\xiaozhi-esp32-server\main\xiaozhi-server\.venv
```

The live local config is intentionally ignored by the upstream server repo:

```text
U:\_Projects\xiaozhi-esp32-server\main\xiaozhi-server\data\.config.yaml
```

It uses the native upstream providers for the first boot path:

- `OpenaiASR` for speech-to-text
- `StackChanOpenAI` using upstream `type: openai` for LLM
- `EdgeTTS` for speech output
- `SileroVAD`, `nomem`, and `nointent`

## Commands

Start:

```powershell
U:\_Projects\stackchan-local-agent\scripts\start-real-server.bat
```

Stop:

```powershell
U:\_Projects\stackchan-local-agent\scripts\stop-real-server.bat
```

Doctor:

```powershell
U:\_Projects\stackchan-local-agent\scripts\doctor-real-server.bat
```

Install or refresh the local admin GUI without starting the server:

```powershell
U:\_Projects\stackchan-local-agent\scripts\install-real-server-gui.bat
```

The real server admin GUI is served from:

```text
http://192.168.0.250:8003/
```

It edits the ignored live config at:

```text
U:\_Projects\xiaozhi-esp32-server\main\xiaozhi-server\data\.config.yaml
```

Editable fields include robot name, personality prompt, LLM provider/base
URL/key/model, ASR URL/key/model, and TTS voice/options. API keys are write-only
in the browser; saved keys are returned only as a redacted presence marker.
Changes are written immediately, but the XiaoZhi server must be restarted before
provider changes are loaded.

After saving keys, the GUI can refresh provider metadata without exposing the
keys back to the browser:

- `Fetch` beside the LLM model calls the saved OpenAI-compatible `/models`
  endpoint and fills the model suggestions.
- `Fetch` beside the ASR model does the same, filtered toward transcription
  models.
- `Voices` loads the Edge TTS voice catalog.
- `Play` generates a short Edge TTS preview through the local server.

Expected OTA response:

```text
OTA接口运行正常，向设备发送的websocket地址是：ws://192.168.0.250:8000/xiaozhi/v1/
```

## Notes

- The old `bridge/server-xz` stub must be stopped before this server starts,
  because both want HTTP port `8003`.
- Windows needs an Opus DLL for `opuslib_next`; this setup copies `opus.dll`
  into the server venv from the installed NoMachine `libopus.dll`.
- Dotty providers are synced into `custom-providers/` for staging. This
  checkpoint uses upstream native providers first because they boot cleanly.
- The admin GUI source is tracked in `real-server/local_admin/` and installed
  into the external XiaoZhi checkout by the start/install scripts. The live
  `.config.yaml`, logs, PID files, venvs, and provider secrets stay out of git.
