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
