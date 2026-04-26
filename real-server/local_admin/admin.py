from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any

import aiohttp
from aiohttp import web
from ruamel.yaml import YAML

WEB_DIR = Path(__file__).resolve().parent / "web"

DEFAULT_PROMPT = """You are StackChan, a small desktop robot assistant.
Keep replies short, natural, and TTS-friendly.
Always begin with exactly one supported emotion emoji:
😊 😆 😢 😮 🤔 😠 😐 😍 😴
Do not use markdown, lists, code blocks, or long paragraphs."""

DEFAULT_CONFIG: dict[str, Any] = {
    "server": {
        "ip": "0.0.0.0",
        "port": 8000,
        "http_port": 8003,
        "websocket": "ws://192.168.0.250:8000/xiaozhi/v1/",
        "vision_explain": "http://192.168.0.250:8003/mcp/vision/explain",
        "auth_key": "stackchan-local-dev-auth-key",
    },
    "manager-api": {"url": "", "secret": ""},
    "log": {"log_level": "INFO", "log_dir": "tmp"},
    "delete_audio": True,
    "prompt": DEFAULT_PROMPT,
    "stackchan_gui": {
        "agent_name": "StackChan",
        "llm_provider": "openai",
        "asr_provider": "openai",
        "tts_provider": "edge",
        "restart_required": False,
    },
    "selected_module": {
        "VAD": "SileroVAD",
        "ASR": "OpenaiASR",
        "LLM": "StackChanOpenAI",
        "VLLM": "ChatGLMVLLM",
        "TTS": "EdgeTTS",
        "Memory": "nomem",
        "Intent": "nointent",
    },
    "ASR": {
        "OpenaiASR": {
            "type": "openai",
            "api_key": "",
            "base_url": "https://api.openai.com/v1/audio/transcriptions",
            "model_name": "gpt-4o-mini-transcribe",
            "output_dir": "tmp/",
        }
    },
    "LLM": {
        "StackChanOpenAI": {
            "type": "openai",
            "base_url": "https://api.openai.com/v1",
            "model_name": "gpt-5-mini",
            "api_key": "",
            "temperature": 0.7,
            "max_tokens": 256,
            "top_p": 1,
            "frequency_penalty": 0,
        }
    },
    "TTS": {
        "EdgeTTS": {
            "type": "edge",
            "voice": "en-US-AriaNeural",
            "output_dir": "tmp/",
            "format": "mp3",
        }
    },
    "VAD": {
        "SileroVAD": {
            "type": "silero",
            "threshold": 0.5,
            "threshold_low": 0.3,
            "model_dir": "models/snakers4_silero-vad",
            "min_silence_duration_ms": 700,
        }
    },
    "Intent": {"nointent": {"type": "nointent"}},
    "Memory": {"nomem": {"type": "nomem"}},
}

yaml = YAML()
yaml.preserve_quotes = True
yaml.indent(mapping=2, sequence=4, offset=2)


def config_path() -> Path:
    return Path.cwd() / "data" / ".config.yaml"


def deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def read_local_config() -> dict[str, Any]:
    path = config_path()
    if not path.exists():
        return copy.deepcopy(DEFAULT_CONFIG)
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.load(handle) or {}
    if not isinstance(loaded, dict):
        loaded = {}
    return deep_merge(DEFAULT_CONFIG, loaded)


def write_local_config(config: dict[str, Any]) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.dump(config, handle)


def redact(value: Any) -> dict[str, Any]:
    text = str(value or "")
    return {
        "present": bool(text),
        "preview": f"...{text[-4:]}" if len(text) >= 4 else "",
    }


def public_config(config: dict[str, Any]) -> dict[str, Any]:
    server = config["server"]
    selected = config["selected_module"]
    llm = config["LLM"][selected["LLM"]]
    asr = config["ASR"][selected["ASR"]]
    tts = config["TTS"][selected["TTS"]]
    gui = config.get("stackchan_gui", {})

    return {
        "agent_name": gui.get("agent_name", "StackChan"),
        "system_prompt": config.get("prompt", DEFAULT_PROMPT),
        "restart_required": bool(gui.get("restart_required", False)),
        "server": {
            "ota_url": f"http://192.168.0.250:{server.get('http_port', 8003)}/xiaozhi/ota/",
            "websocket_url": server.get("websocket", "ws://192.168.0.250:8000/xiaozhi/v1/"),
            "http_port": server.get("http_port", 8003),
            "websocket_port": server.get("port", 8000),
        },
        "llm": {
            "provider": gui.get("llm_provider", "openai"),
            "base_url": llm.get("base_url") or llm.get("url") or "",
            "model": llm.get("model_name", ""),
            "temperature": llm.get("temperature", 0.7),
            "max_tokens": llm.get("max_tokens", 256),
            "api_key": redact(llm.get("api_key")),
        },
        "asr": {
            "provider": gui.get("asr_provider", "openai"),
            "api_url": asr.get("base_url") or asr.get("api_url") or "",
            "model": asr.get("model_name", ""),
            "api_key": redact(asr.get("api_key")),
        },
        "tts": {
            "provider": gui.get("tts_provider", "edge"),
            "voice": tts.get("voice", ""),
            "api_url": tts.get("api_url") or "",
            "model": tts.get("model", ""),
            "api_key": redact(tts.get("api_key")),
        },
    }


def as_str(payload: dict[str, Any], key: str, default: str = "") -> str:
    value = payload.get(key, default)
    return value if isinstance(value, str) else default


def as_float(payload: dict[str, Any], key: str, default: float) -> float:
    try:
        return float(payload.get(key, default))
    except (TypeError, ValueError):
        return default


def as_int(payload: dict[str, Any], key: str, default: int) -> int:
    try:
        return int(payload.get(key, default))
    except (TypeError, ValueError):
        return default


def update_key(target: dict[str, Any], payload: dict[str, Any], field: str, clear_field: str) -> None:
    if payload.get(clear_field) is True:
        target["api_key"] = ""
        return
    value = as_str(payload, field).strip()
    if value:
        target["api_key"] = value


def selected_provider_config(config: dict[str, Any], provider: str) -> dict[str, Any]:
    selected = config["selected_module"]
    if provider == "llm":
        return config["LLM"][selected["LLM"]]
    if provider == "asr":
        return config["ASR"][selected["ASR"]]
    if provider == "tts":
        return config["TTS"][selected["TTS"]]
    return {}


def models_url(base_url: str) -> str:
    cleaned = base_url.strip().rstrip("/")
    cleaned = re.sub(r"/audio/transcriptions$", "", cleaned)
    cleaned = re.sub(r"/chat/completions$", "", cleaned)
    if cleaned.endswith("/models"):
        return cleaned
    return f"{cleaned}/models"


def auth_headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}"} if api_key else {}


def model_allowed(provider: str, model_id: str) -> bool:
    lower = model_id.lower()
    if provider == "asr":
        return "transcribe" in lower or "whisper" in lower
    if provider == "llm":
        return not any(token in lower for token in ("embedding", "transcribe", "tts", "realtime", "image"))
    return True


async def index_handler(_: web.Request) -> web.FileResponse:
    return web.FileResponse(WEB_DIR / "index.html")


async def get_config_handler(_: web.Request) -> web.Response:
    return web.json_response(public_config(read_local_config()))


async def save_config_handler(request: web.Request) -> web.Response:
    try:
        payload = await request.json()
    except Exception:
        return web.json_response({"error": "invalid json"}, status=400)
    if not isinstance(payload, dict):
        return web.json_response({"error": "expected object"}, status=400)

    config = read_local_config()
    config.setdefault("stackchan_gui", {})
    config["stackchan_gui"]["agent_name"] = as_str(payload, "agent_name", "StackChan").strip() or "StackChan"
    config["stackchan_gui"]["llm_provider"] = as_str(payload, "llm_provider", "openai")
    config["stackchan_gui"]["asr_provider"] = as_str(payload, "asr_provider", "openai")
    config["stackchan_gui"]["tts_provider"] = as_str(payload, "tts_provider", "edge")
    config["stackchan_gui"]["restart_required"] = True
    config["prompt"] = as_str(payload, "system_prompt", DEFAULT_PROMPT)

    config["selected_module"].update(
        {
            "VAD": "SileroVAD",
            "ASR": "OpenaiASR",
            "LLM": "StackChanOpenAI",
            "TTS": "EdgeTTS",
            "Memory": "nomem",
            "Intent": "nointent",
        }
    )

    llm = config["LLM"]["StackChanOpenAI"]
    llm["type"] = "openai"
    llm["base_url"] = as_str(payload, "llm_base_url", "https://api.openai.com/v1").strip()
    llm["model_name"] = as_str(payload, "llm_model", "gpt-5-mini").strip()
    llm["temperature"] = as_float(payload, "llm_temperature", 0.7)
    llm["max_tokens"] = as_int(payload, "llm_max_tokens", 256)
    update_key(llm, payload, "llm_api_key", "clear_llm_api_key")

    asr = config["ASR"]["OpenaiASR"]
    asr["type"] = "openai"
    asr["base_url"] = as_str(
        payload,
        "asr_api_url",
        "https://api.openai.com/v1/audio/transcriptions",
    ).strip()
    asr["model_name"] = as_str(payload, "asr_model", "gpt-4o-mini-transcribe").strip()
    asr["output_dir"] = "tmp/"
    update_key(asr, payload, "asr_api_key", "clear_asr_api_key")

    tts = config["TTS"]["EdgeTTS"]
    tts["type"] = "edge"
    tts["voice"] = as_str(payload, "tts_voice", "en-US-AriaNeural").strip()
    tts["api_url"] = as_str(payload, "tts_api_url").strip()
    tts["model"] = as_str(payload, "tts_model").strip()
    tts["output_dir"] = "tmp/"
    tts["format"] = "mp3"
    update_key(tts, payload, "tts_api_key", "clear_tts_api_key")

    write_local_config(config)
    return web.json_response(public_config(config))


async def restart_ack_handler(_: web.Request) -> web.Response:
    config = read_local_config()
    config.setdefault("stackchan_gui", {})["restart_required"] = False
    write_local_config(config)
    return web.json_response({"restart_required": False})


async def models_handler(request: web.Request) -> web.Response:
    provider = request.match_info.get("provider", "llm")
    if provider not in {"llm", "asr"}:
        return web.json_response({"error": "unsupported provider"}, status=400)

    config = read_local_config()
    provider_config = selected_provider_config(config, provider)
    base_url = provider_config.get("base_url") or provider_config.get("api_url") or ""
    api_key = provider_config.get("api_key") or ""
    if not base_url:
        return web.json_response({"error": "missing provider URL"}, status=400)

    try:
        timeout = aiohttp.ClientTimeout(total=12)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(models_url(base_url), headers=auth_headers(api_key)) as response:
                payload = await response.json(content_type=None)
                if response.status >= 400:
                    message = payload.get("error", payload) if isinstance(payload, dict) else payload
                    return web.json_response({"error": str(message)}, status=response.status)
    except Exception as exc:
        return web.json_response({"error": str(exc)}, status=502)

    items = payload.get("data", []) if isinstance(payload, dict) else []
    models = sorted(
        {
            str(item.get("id"))
            for item in items
            if isinstance(item, dict) and item.get("id") and model_allowed(provider, str(item.get("id")))
        }
    )
    return web.json_response({"models": models})


async def edge_voices_handler(_: web.Request) -> web.Response:
    try:
        import edge_tts

        voices = await edge_tts.list_voices()
    except Exception as exc:
        return web.json_response({"error": str(exc)}, status=502)

    english_first = sorted(
        voices,
        key=lambda voice: (
            0 if str(voice.get("ShortName", "")).startswith("en-") else 1,
            str(voice.get("Locale", "")),
            str(voice.get("ShortName", "")),
        ),
    )
    return web.json_response(
        {
            "voices": [
                {
                    "name": voice.get("ShortName", ""),
                    "locale": voice.get("Locale", ""),
                    "gender": voice.get("Gender", ""),
                    "display_name": voice.get("FriendlyName", ""),
                }
                for voice in english_first
                if voice.get("ShortName")
            ]
        }
    )


async def edge_voice_preview_handler(request: web.Request) -> web.StreamResponse:
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    voice = as_str(payload, "voice", "en-US-AriaNeural").strip() or "en-US-AriaNeural"
    text = as_str(payload, "text", "Hi, I am StackChan. This is my voice preview.").strip()
    if len(text) > 180:
        text = text[:180]

    try:
        import edge_tts

        communicate = edge_tts.Communicate(text, voice)
        audio = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio.extend(chunk["data"])
    except Exception as exc:
        return web.json_response({"error": str(exc)}, status=502)

    return web.Response(body=bytes(audio), content_type="audio/mpeg")


def setup_admin_routes(app: web.Application) -> None:
    app.add_routes(
        [
            web.get("/", index_handler),
            web.get("/api/local-config", get_config_handler),
            web.post("/api/local-config", save_config_handler),
            web.post("/api/restart-needed", restart_ack_handler),
            web.get("/api/provider-models/{provider}", models_handler),
            web.get("/api/tts-voices/edge", edge_voices_handler),
            web.post("/api/tts-preview/edge", edge_voice_preview_handler),
            web.static("/admin-assets", WEB_DIR),
        ]
    )
