# Stakia self-hosted voice hub

This host stack connects StackChan directly to a LAN Xiaozhi-compatible server. It does not require a vendor account, OTA bootstrap service, manager API, or China-hosted model service. Authentication is deliberately disabled for this first private-LAN integration; do not expose ports 8000, 8003, or 8080 to the internet.

The server source is pinned to `6afc54a17def47578a4b3efc4680873689d3168b`. Default speech is fully local: faster-whisper ASR and Piper TTS. The default LLM profile is LM Studio. OpenRouter is an explicit optional model profile and is never selected automatically.

## Existing installation upgrade

Keep your existing `.env.local` and `.venv`. Do not copy the example over them. Add or review these values:

```dotenv
STAKIA_LAN_HOST=192.168.1.20
LMSTUDIO_BASE_URL=http://host.docker.internal:1234/v1
LMSTUDIO_MODEL=your-loaded-model-id
LMSTUDIO_API_KEY=lm-studio
```

Only add `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` if you deliberately select OpenRouter.

Place local model assets at these exact paths before startup:

```text
data/models/silero/src/silero_vad/data/silero_vad.onnx
data/models/whisper/model.bin
data/models/whisper/config.json
data/models/whisper/tokenizer.json
data/models/whisper/                         # remaining CTranslate2 model files
data/models/piper/voice.onnx
data/models/piper/voice.onnx.json
```

The startup validator stops with a list of missing assets. It does not download a model or fall back to cloud speech.

Model acquisition is an explicit setup action. Install the Hugging Face CLI,
review the model licenses, and run these commands yourself (startup never runs
them):

```powershell
pip install "huggingface_hub[cli]"
huggingface-cli download Systran/faster-whisper-small.en --local-dir data/models/whisper
Invoke-WebRequest https://raw.githubusercontent.com/snakers4/silero-vad/master/src/silero_vad/data/silero_vad.onnx -OutFile data/models/silero/src/silero_vad/data/silero_vad.onnx
Invoke-WebRequest https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx -OutFile data/models/piper/voice.onnx
Invoke-WebRequest https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json -OutFile data/models/piper/voice.onnx.json
```

For a strictly reproducible installation, replace `main`/`master` in those
URLs with a reviewed repository commit and record it alongside the model
files. The required Whisper files include `model.bin`, `config.json`, and
`tokenizer.json`; the last file prevents faster-whisper from contacting
Hugging Face during startup.

## Fresh Windows setup

```powershell
if (-not (Test-Path .env.local)) { Copy-Item .env.local.example .env.local }
py -m venv .venv
.venv\Scripts\pip install -r bridge\requirements.txt
scripts\start-host.bat -Build
scripts\doctor-host.bat
```

`start-host` renders a complete runtime configuration, builds/starts the pinned server, and launches `python bridge.py`. `doctor-host` reports credentials only as set or unset. The dashboard is at `http://localhost:8080/ui`.

Dashboard changes persist immediately. Apply model/timing changes after the current turn by recreating the service so it reopens the generated configuration:

```powershell
docker compose --env-file .env.local up -d --force-recreate xiaozhi-esp32-server
```

Defaults are a six-second speech pause, conversation idle set to Never, and idle farewell disabled. Never disables both silence-close guards while network, provider, authentication, and stalled-request timeouts remain distinct.

## Local-only boundaries

The generated server configuration explicitly selects `WhisperLocal`, `PiperLocal`, `LMStudio`, `nomem`, and `nointent`; disables manager API and server authentication; provides no weather/search/news functions; and loads the local persona file. OpenRouter affects only the LLM when selected. Optional bridge vision variables remain commented out and no vision provider is selected by the voice server.

The firmware connects directly to:

```text
ws://<STAKIA_LAN_HOST>:8000/xiaozhi/v1/
```

OTA and official activation are not part of this path.

## Validation

Run host regressions with:

```powershell
.venv\Scripts\python -m pytest -q
```

No test performs a paid model call or accesses the robot.
