import json
import stat

import pytest
from keyring.errors import KeyringError

from fantread.config import (
    AppConfig,
    ConfigError,
    api_key_source,
    config_file,
    fresh_run_enabled,
    load_config,
    resolve_api_key,
    save_config,
    store_api_key,
)


def test_config_file_never_contains_api_key(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("FANTREAD_CONFIG_DIR", str(tmp_path))
    path = save_config(AppConfig(model="deepseek-v4-pro"))
    raw = path.read_text(encoding="utf-8")
    payload = json.loads(raw)

    assert path == config_file()
    assert payload["model"] == "deepseek-v4-pro"
    assert "api_key" not in payload
    assert "mode" not in payload
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert load_config().model == "deepseek-v4-pro"


def test_fresh_run_is_the_development_default(monkeypatch) -> None:
    monkeypatch.delenv("FANTREAD_FRESH", raising=False)
    assert fresh_run_enabled() is True

    monkeypatch.setenv("FANTREAD_FRESH", "0")
    assert fresh_run_enabled() is False


@pytest.mark.parametrize("value", ["0", "false", "NO", "off"])
def test_fresh_run_false_values(monkeypatch, value) -> None:
    monkeypatch.setenv("FANTREAD_FRESH", value)
    assert fresh_run_enabled() is False


def test_load_config_rejects_invalid_json(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("FANTREAD_CONFIG_DIR", str(tmp_path))
    config_file().write_text("{broken", encoding="utf-8")

    with pytest.raises(ConfigError, match="无法读取"):
        load_config()


def test_load_config_ignores_unknown_future_fields(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("FANTREAD_CONFIG_DIR", str(tmp_path))
    config_file().write_text(
        json.dumps(
            {
                "model": "deepseek-v4-pro",
                "future_setting": True,
            }
        ),
        encoding="utf-8",
    )

    assert load_config().model == "deepseek-v4-pro"


def test_save_config_validates_values(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("FANTREAD_CONFIG_DIR", str(tmp_path))

    with pytest.raises(ConfigError, match="base_url"):
        save_config(AppConfig(base_url="file:///tmp/api"))
    assert not config_file().exists()


def test_keyring_failures_are_safe_and_actionable(monkeypatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    def fail_get(*args):
        raise KeyringError("unavailable")

    def fail_set(*args):
        raise KeyringError("unavailable")

    monkeypatch.setattr("fantread.config.keyring.get_password", fail_get)
    monkeypatch.setattr("fantread.config.keyring.set_password", fail_set)

    assert resolve_api_key() is None
    assert api_key_source() is None
    with pytest.raises(ConfigError, match="系统密钥环不可用"):
        store_api_key("test-key")
