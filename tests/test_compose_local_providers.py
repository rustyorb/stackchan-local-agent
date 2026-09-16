from pathlib import Path
import yaml


def test_compose_mounts_piper_as_importable_provider_file():
    compose = yaml.safe_load(Path("docker-compose.yml").read_text())
    volumes = compose["services"]["xiaozhi-esp32-server"]["volumes"]
    assert "./custom-providers/piper_local/piper_local.py:/opt/xiaozhi-esp32-server/core/providers/tts/piper_local.py:ro" in volumes


def test_owned_prompt_template_has_no_external_context_placeholders():
    text = Path("config/stakia-local-prompt.txt").read_text(encoding="utf-8")
    assert "{{ base_prompt }}" in text
    assert "local_address" not in text
    assert "weather_info" not in text
    assert "dynamic_context" not in text
