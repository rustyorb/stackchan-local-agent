# server-xz — minimal xiaozhi-protocol backend

Drops in for the `api.tenclass.net` cloud. Skips activation. Lets the
device connect locally so we can iterate on the real backend
(OpenRouter LLM + STT/TTS) without the China RTT.

## Run

```bash
cd server-xz
pip install -r requirements.txt
python app.py --public-url http://192.168.0.250:8003
```

Or use the helper scripts:

```powershell
cd U:\_Projects\StackChan\server-xz
.\start.bat
.\stop.bat
```

Then open the local dashboard:

```text
http://192.168.0.250:8003/
```

The dashboard writes provider, API URL, API key, voice, agent name,
and prompt settings to `config.local.json`. That file is ignored by git
and should stay local.

For the first end-to-end path, use the **OpenAI defaults** button in the
dashboard. OpenRouter is only the chat/LLM part, and ElevenLabs is only
the TTS part, so those are better follow-up integrations after the
OpenAI path is working.

## Point the device at it

Use the NVS provisioning helper. This writes Wi-Fi credentials and the
`wifi/ota_url` key that the firmware already honours in
`firmware/xiaozhi-esp32/main/ota.cc` `GetCheckVersionUrl`:

```bash
SSID="your-wifi" PASSWORD="your-password" \
OTA_URL=http://192.168.0.250:8003/xiaozhi/ota/ \
  bash ../tools/provision_wifi.sh COM5
```

PowerShell:

```powershell
cd U:\_Projects\StackChan
.\tools\provision_wifi.ps1 -Ssid "your-wifi" -Password "your-password" -OtaUrl "http://192.168.0.250:8003/xiaozhi/ota/" -Port COM5
```

Reboot the device. The boot log should show
`Ota: Current version: 1.2.6-dev` followed by an HTTP call to
`192.168.0.250:8003` instead of `api.tenclass.net`, then
`Application: Network connected` → **no `Activating...` loop** →
`Opening audio channel: url=ws://192.168.0.250:8003/xiaozhi/v1/`.

## What this doesn't do yet

- No real STT / LLM / TTS audio yet. The WebSocket now replies to
  `hello`, logs listen/audio events, and sends protocol-correct
  `stt`/`llm`/`tts` JSON so the device screen shows local activity.
  The dashboard captures the provider settings needed for the next
  step: OpenRouter/OpenAI-compatible LLM + STT + TTS that can emit Opus
  frames.
