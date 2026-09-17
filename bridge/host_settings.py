"""Validated, persisted host settings and Xiaozhi config rendering."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import re
import yaml
from bridge.security import ensure_security, private_ipv4, write_private_text


@dataclass(frozen=True)
class HostSettings:
    pause_seconds: float = 6.0
    idle_minutes: int | None = None
    idle_farewell: bool = False
    active_profile: str = "lmstudio"

    def __post_init__(self):
        if not 1 <= self.pause_seconds <= 30:
            raise ValueError("pause_seconds must be between 1 and 30")
        if self.idle_minutes is not None and not 1 <= self.idle_minutes <= 1440:
            raise ValueError("idle_minutes must be 1..1440 or null (Never)")
        if self.active_profile not in {"lmstudio", "openrouter"}:
            raise ValueError("active_profile must be lmstudio or openrouter")


class SettingsStore:
    def __init__(self, path: Path):
        self.path = Path(path)

    def load(self) -> HostSettings:
        if not self.path.exists():
            return HostSettings()
        return HostSettings(**json.loads(self.path.read_text(encoding="utf-8")))

    def save(self, settings: HostSettings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(asdict(settings), indent=2) + "\n", encoding="utf-8")
        tmp.replace(self.path)


_ENV = re.compile(r"^\$\{([A-Z][A-Z0-9_]*)\}$")


def expand_env(value):
    if isinstance(value, dict):
        return {k: expand_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [expand_env(v) for v in value]
    if isinstance(value, str) and (match := _ENV.match(value)):
        name = match.group(1)
        resolved = os.environ.get(name)
        if not resolved:
            raise ValueError(f"required environment variable {name} is unset")
        return resolved
    return value


def validate_local_assets(model_root: Path) -> None:
    required = {
        "Silero VAD model": model_root / "silero/src/silero_vad/data/silero_vad.onnx",
        "Whisper model directory": model_root / "whisper",
        "Whisper model.bin": model_root / "whisper/model.bin",
        "Whisper config.json": model_root / "whisper/config.json",
        "Whisper tokenizer.json": model_root / "whisper/tokenizer.json",
        "Piper voice model": model_root / "piper/voice.onnx",
        "Piper voice config": model_root / "piper/voice.onnx.json",
    }
    missing = [label for label, path in required.items() if not path.exists()]
    if missing:
        raise ValueError("missing local speech assets: " + ", ".join(missing))


def render_server_config(settings: HostSettings, *, lan_host: str,
                         persona_path: Path | None = None, device_token: str = "") -> dict:
    lan_host = private_ipv4(lan_host)
    if len(device_token) != 64 or any(c not in "0123456789abcdef" for c in device_token):
        raise ValueError("Provision the local device credential before rendering configuration")
    profiles = {
        "lmstudio": {"type": "openai", "base_url": os.getenv("LMSTUDIO_BASE_URL", "http://host.docker.internal:1234/v1"),
                     "model_name": os.getenv("LMSTUDIO_MODEL", "local-model"), "api_key": os.getenv("LMSTUDIO_API_KEY", "lm-studio")},
        "openrouter": {"type": "openai", "base_url": "https://openrouter.ai/api/v1",
                       "model_name": os.getenv("OPENROUTER_MODEL", "openai/gpt-4.1-mini"), "api_key": "${OPENROUTER_API_KEY}"},
    }
    name = "LMStudio" if settings.active_profile == "lmstudio" else "OpenRouter"
    timeout = None if settings.idle_minutes is None else settings.idle_minutes * 60
    persona_path = persona_path or Path(__file__).parent.parent / "personas/feisty.md"
    try:
        prompt = persona_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise ValueError(f"local persona is unavailable: {persona_path}") from exc
    return expand_env({
        "standalone_config": True,
        "server": {"ip": "0.0.0.0", "port": 8000, "http_port": 0,
                   "websocket": f"wss://{lan_host}:8000/xiaozhi/v1/",
                   "auth": {"enabled": True, "token": device_token, "allowed_devices": []},
                   "tls": {"certfile": "/run/stakia/server-cert.pem",
                           "keyfile": "/run/stakia/server-key.pem"},
                   "mqtt_gateway": None, "udp_gateway": None},
        "manager-api": {"url": "", "secret": ""},
        "prompt_template": "/opt/xiaozhi-esp32-server/stakia-local-prompt.txt",
        "log": {"log_level": "INFO", "log_dir": "tmp", "log_file": "server.log"},
        "prompt": prompt,
        "delete_audio": True,
        "tts_timeout": 30,
        "tool_call_timeout": 30,
        "device_max_output_size": 0,
        "exit_commands": ["exit conversation", "goodbye stakia"],
        "mcp_endpoint": "",
        "voiceprint": {},
        "xiaozhi": {"type": "hello", "version": 1, "transport": "websocket",
                    "audio_params": {"format": "opus", "sample_rate": 24000,
                                     "channels": 1, "frame_duration": 60}},
        "close_connection_no_voice_time": timeout,
        "end_prompt": {"enable": settings.idle_farewell,
                       "prompt": "End the conversation with one brief, warm English farewell."},
        "selected_module": {"VAD": "SileroVAD", "ASR": "WhisperLocal", "LLM": name,
                            "VLLM": "none", "TTS": "PiperLocal",
                            "Memory": "nomem", "Intent": "nointent"},
        "VAD": {"SileroVAD": {"type": "silero", "model_dir": "/models/silero",
                               "min_silence_duration_ms": int(settings.pause_seconds * 1000)}},
        "ASR": {"WhisperLocal": {"type": "whisper_local", "model_dir": "/models/whisper",
                                  "language": "en", "device": "cpu", "compute_type": "int8",
                                  "output_dir": "tmp/"}},
        "TTS": {"PiperLocal": {"type": "piper_local", "voice": "stakia",
                                "language": "English",
                                "model_path": "/models/piper/voice.onnx",
                                "config_path": "/models/piper/voice.onnx.json",
                                "output_dir": "tmp/"}},
        "LLM": {name: profiles[settings.active_profile]},
        "Memory": {"nomem": {"type": "nomem"}},
        "Intent": {"nointent": {"type": "nointent"}},
        "plugins": {},
    })


def write_server_config(settings: HostSettings, *, lan_host: str, path: Path) -> None:
    identity = ensure_security(path.parent / "security", lan_host)
    rendered = render_server_config(settings, lan_host=lan_host, device_token=identity["device_token"])
    path.parent.mkdir(parents=True, exist_ok=True)
    content = yaml.safe_dump(rendered, sort_keys=False)
    write_private_text(path, content)
    write_private_text(path.parent / ".config.yaml", content)


def settings_from_form(profile, pause_seconds, idle_mode, idle_minutes, idle_farewell):
    if idle_mode not in {'never', 'finite'}:
        raise ValueError('Choose Never or Custom minutes')
    idle = None
    if idle_mode == 'finite':
        try:
            idle = int(idle_minutes)
        except (ValueError, TypeError) as exc:
            raise ValueError('Custom idle time requires minutes from 1 to 1440') from exc
    try:
        pause = float(pause_seconds)
    except (ValueError, TypeError) as exc:
        raise ValueError('Pause must be a number from 1 to 30 seconds') from exc
    return HostSettings(active_profile=profile, pause_seconds=pause,
                        idle_minutes=idle, idle_farewell=idle_farewell == 'on')
