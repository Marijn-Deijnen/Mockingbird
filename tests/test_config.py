import json
import pytest


@pytest.fixture
def tmp_config(tmp_path, monkeypatch):
    """Patch CONFIG_PATH to a temp file."""
    import src.config as cfg_mod
    monkeypatch.setattr(cfg_mod, "CONFIG_PATH", tmp_path / "config.json")
    return tmp_path / "config.json"


def test_load_defaults_when_no_file(tmp_config):
    import src.config as cfg_mod
    result = cfg_mod.load()
    assert result["cfg_value"] == 2.0
    assert result["inference_timesteps"] == 10
    assert result["use_denoiser"] is False
    assert result["last_voice_id"] == ""


def test_load_merges_with_defaults(tmp_config):
    import src.config as cfg_mod
    tmp_config.write_text(json.dumps({"cfg_value": 5.0}))
    result = cfg_mod.load()
    assert result["cfg_value"] == 5.0
    assert result["inference_timesteps"] == 10  # default still present


def test_save_and_reload(tmp_config):
    import src.config as cfg_mod
    cfg = cfg_mod.load()
    cfg["cfg_value"] = 3.5
    cfg_mod.save(cfg)
    reloaded = cfg_mod.load()
    assert reloaded["cfg_value"] == 3.5


def test_load_returns_defaults_on_corrupted_file(tmp_config):
    import src.config as cfg_mod
    tmp_config.write_bytes(b"not valid json{{{{")
    result = cfg_mod.load()
    assert result["cfg_value"] == 2.0
    assert result["last_voice_id"] == ""


def test_load_includes_ollama_defaults(tmp_config):
    import src.config as cfg_mod
    result = cfg_mod.load()
    assert result["ollama_enabled"] is False
    assert result["ollama_host"] == "127.0.0.1"
    assert result["ollama_port"] == 11434
    assert result["ollama_model"] == ""
    assert result["show_ai_prompt"] is True


def test_load_includes_voice_profiles_default(tmp_config):
    import src.config as cfg_mod
    result = cfg_mod.load()
    assert result["voice_profiles"] == {}


def test_load_includes_general_settings_defaults(tmp_config):
    import src.config as cfg_mod
    result = cfg_mod.load()
    assert result["style_prefix"] == ""
    assert result["auto_play"] is False
    assert "{voice_name}" in result["ai_system_prompt"]
