# StackChan Local Agent

Self-hosted voice-agent stack for the M5Stack StackChan desktop robot.
Forked from [BrettKinny/dotty-stackchan][1] with ZeroClaw replaced by a
direct OpenAI-compatible LLM call. The kid-mode and household / family
plumbing have been removed — this is a single-user feisty desk robot.

## Architecture

```text
StackChan firmware  (ESP32-S3, xiaozhi protocol)
   │ WiFi WebSocket
   ▼
xiaozhi-esp32-server  (Docker container on this PC)
   ├─ ASR: OpenAI cloud (cheap) → swap to FunASR / faster-whisper later
   ├─ TTS: EdgeTTS (free) → swap to LocalPiper later
   └─ LLM: HTTP relay to bridge.py at host.docker.internal:8080
          │
          ▼
    bridge.py  (Python, native on host, port 8080)
       ├─ persona injection (personas/feisty.md)
       ├─ context injection (date / weather / calendar — opt-in)
       ├─ perception bus (face / sound / state events from firmware)
       ├─ vision (room-view via OpenRouter Gemini)
       ├─ dashboard at /ui (htmx + Tailwind/DaisyUI)
       └─ direct OpenAI-compatible chat completions call
              │
              ▼
        OpenRouter / OpenAI / LM Studio / Ollama  (your pick)
```

## What lives where

```text
.
├── bridge.py                # FastAPI: LLM proxy + perception + dashboard
├── bridge/                  # bridge helper modules (dashboard, metrics, …)
├── personas/                # markdown persona files (feisty, default, …)
├── custom-providers/        # xiaozhi-server overrides (LLM/ASR/TTS)
│   ├── zeroclaw/            # the HTTP relay used by xiaozhi → bridge
│   ├── openai_compat/       # alternate: skip bridge, call cloud directly
│   ├── piper_local/         # local Piper TTS (offline)
│   ├── asr/                 # FunASR + faster-whisper local providers
│   ├── edge_stream/         # streaming EdgeTTS
│   ├── xiaozhi-patches/     # core xiaozhi-server patches (perception relay,
│   │                        #   admin /inject-text, OTA path fix)
│   └── textUtils.py         # emoji + format constants shared with bridge
├── config/
│   └── xiaozhi-stackchan.yaml   # bind-mounted live config for the container
├── docker-compose.yml       # spins up xiaozhi-esp32-server
├── ota-shim/                # legacy: minimal OTA-bypass shim from Codex
│                            #   (provisioning helper; not in the LLM path)
├── real-server/local_admin/ # Codex's live-config admin GUI
├── firmware-patches/        # firmware patches (currently stale — refresh
│                            #   against current 2026 stock before flashing)
├── scripts/                 # PowerShell / batch helpers (Windows-first)
└── third_party/             # attribution + (deprecated) vendored snapshot
```

## Prerequisites

- Windows 10/11 (this fork is Windows-first; Linux / macOS work too)
- **Docker Desktop** (running)
- **Python 3.13+** with venv support
- **OpenRouter API key** (default LLM backend; swap to OpenAI / LM Studio /
  Ollama by editing `.env.local`)
- The StackChan robot, on the same LAN

## First-boot setup

```powershell
# 1. Clone + venv
git clone https://github.com/rustyorb/stackchan-local-agent.git
cd stackchan-local-agent
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r bridge\requirements.txt

# 2. Configure secrets
cp .env.local.example .env.local
# Edit .env.local — paste your OpenRouter key into LLM_API_KEY=…

# 3. Bring up xiaozhi-esp32-server (Docker)
docker compose up -d
docker compose logs -f xiaozhi-esp32-server   # watch it boot

# 4. Run the bridge
python bridge.py
# (or: uvicorn bridge:app --host 0.0.0.0 --port 8080 --reload)

# 5. Smoke test
curl http://127.0.0.1:8080/health
curl -X POST http://127.0.0.1:8080/api/message ^
     -H "Content-Type: application/json" ^
     -d "{\"content\":\"hello\"}"
```

The bridge dashboard lives at <http://127.0.0.1:8080/ui>.
xiaozhi-esp32-server's OTA endpoint is at <http://127.0.0.1:8003/xiaozhi/ota/>.

## Pointing the robot at this server

After `docker compose up -d`:

1. Find your Windows machine's LAN IP (`ipconfig`).
2. Edit `config/xiaozhi-stackchan.yaml` →
   `server.websocket: ws://<LAN_IP>:8000/xiaozhi/v1/`.
3. `docker compose restart xiaozhi-esp32-server`.
4. Boot the StackChan into provisioning mode and point its OTA URL at
   `http://<LAN_IP>:8003/xiaozhi/ota/`.

## Swapping the LLM backend

Everything is one URL change. Edit `.env.local`:

| Backend | LLM_API_URL | Notes |
|---|---|---|
| OpenRouter (default) | `https://openrouter.ai/api/v1/chat/completions` | Wide model selection, paid |
| OpenAI cloud | `https://api.openai.com/v1/chat/completions` | `gpt-4o-mini` recommended |
| LM Studio (local) | `http://localhost:1234/v1/chat/completions` | Load model in LM Studio UI first |
| Ollama (local) | `http://localhost:11434/v1/chat/completions` | `ollama pull llama3.1:8b` first |

No bridge restart needed if you use the dashboard's persona swap; for
URL/model changes, restart the bridge process.

## What was forked from dotty

- `bridge.py` (kept; ZeroClaw subprocess client + kid-mode logic stripped,
  smart-mode toggle removed, single LLM call promoted to primary)
- `bridge/` helpers (dashboard, metrics, perception consumers, security
  watch, server-push, etc. — kid-mode plumbing stubbed)
- `custom-providers/` (xiaozhi-server LLM/ASR/TTS provider overrides)
- `personas/` (added `feisty.md` for this fork's default persona)

## Attribution

This project includes work derived from:

- [BrettKinny/dotty-stackchan][1] (MIT) — the bulk of the bridge,
  perception, and dashboard
- [xinnan-tech/xiaozhi-esp32-server][2] (MIT) — voice pipeline server
- [m5stack/StackChan][3] (MIT) — hardware + reference firmware

See `NOTICE.md` for full attribution and license text.

[1]: https://github.com/BrettKinny/dotty-stackchan
[2]: https://github.com/xinnan-tech/xiaozhi-esp32-server
[3]: https://github.com/m5stack/StackChan

## Local secrets

Never commit. The `.env.local` file is gitignored. Provider keys live
only in `.env.local`; the bind-mounted `config/xiaozhi-stackchan.yaml`
uses `${ENV_VAR}` substitution so the YAML itself stays clean.
