import json
from pathlib import Path

import pytest

from bridge.host_settings import HostSettings, SettingsStore, expand_env, render_server_config, validate_local_assets


def test_defaults_give_six_second_pause_and_never_idle(tmp_path):
    settings = SettingsStore(tmp_path / "settings.json").load()
    assert settings.pause_seconds == 6.0
    assert settings.idle_minutes is None
    assert settings.idle_farewell is False
    assert settings.active_profile == "lmstudio"


def test_settings_persist_profile_and_independent_farewell(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")
    wanted = HostSettings(pause_seconds=8, idle_minutes=15,
                          idle_farewell=False, active_profile="openrouter")
    store.save(wanted)
    assert store.load() == wanted


def test_render_selects_profile_and_expands_secret_without_writing_placeholder(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "secret-value")
    settings = HostSettings(active_profile="openrouter")
    rendered = render_server_config(settings, lan_host="192.168.1.20")
    assert rendered["server"]["websocket"] == "ws://192.168.1.20:8000/xiaozhi/v1/"
    assert rendered["VAD"]["SileroVAD"]["min_silence_duration_ms"] == 6000
    assert rendered["close_connection_no_voice_time"] is None
    assert rendered["end_prompt"]["enable"] is False
    assert "English farewell" in rendered["end_prompt"]["prompt"]
    assert rendered["LLM"]["OpenRouter"]["api_key"] == "secret-value"
    assert rendered["selected_module"] == {
        "VAD": "SileroVAD", "ASR": "WhisperLocal", "LLM": "OpenRouter",
        "VLLM": "none", "TTS": "PiperLocal", "Memory": "nomem", "Intent": "nointent",
    }
    assert rendered["server"]["auth"]["enabled"] is False
    assert rendered["manager-api"]["url"] == ""
    assert rendered["standalone_config"] is True
    assert rendered["xiaozhi"]["audio_params"]["sample_rate"] == 24000
    assert rendered["prompt_template"] == "/opt/xiaozhi-esp32-server/stakia-local-prompt.txt"
    assert rendered["TTS"]["PiperLocal"]["language"] == "English"
    assert rendered["Intent"]["nointent"]["type"] == "nointent"
    assert "weather" not in str(rendered).lower()
    assert "server persona" not in rendered["prompt"]


def test_prompt_is_loaded_from_local_persona(tmp_path):
    persona = tmp_path / "stakia.md"
    persona.write_text("You are Stakia, locally hosted.", encoding="utf-8")
    rendered = render_server_config(HostSettings(), lan_host="10.0.0.5", persona_path=persona)
    assert rendered["prompt"] == "You are Stakia, locally hosted."


def test_local_assets_fail_clearly_when_missing(tmp_path):
    with pytest.raises(ValueError, match="Whisper model directory"):
        validate_local_assets(tmp_path)


def test_local_assets_require_whisper_and_piper_files(tmp_path):
    whisper = tmp_path / "whisper"
    piper = tmp_path / "piper"
    silero = tmp_path / "silero/src/silero_vad/data"
    whisper.mkdir(); piper.mkdir(); silero.mkdir(parents=True)
    (silero / "silero_vad.onnx").write_bytes(b"x")
    (whisper / "model.bin").write_bytes(b"x")
    (whisper / "config.json").write_text("{}")
    (whisper / "tokenizer.json").write_text("{}")
    (piper / "voice.onnx").write_bytes(b"x")
    (piper / "voice.onnx.json").write_text("{}")
    validate_local_assets(tmp_path)


def test_local_assets_reject_missing_whisper_tokenizer(tmp_path):
    whisper = tmp_path / "whisper"; whisper.mkdir()
    (whisper / "model.bin").write_bytes(b"x")
    (whisper / "config.json").write_text("{}")
    with pytest.raises(ValueError, match="tokenizer.json"):
        validate_local_assets(tmp_path)


def test_missing_required_secret_is_rejected(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        render_server_config(HostSettings(active_profile="openrouter"), lan_host="10.0.0.5")


def test_env_expansion_rejects_unresolved_placeholders(monkeypatch):
    monkeypatch.delenv("MISSING", raising=False)
    with pytest.raises(ValueError, match="MISSING"):
        expand_env({"key": "${MISSING}"})
