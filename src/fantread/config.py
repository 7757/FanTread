from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any

import keyring
from keyring.errors import KeyringError
from platformdirs import user_config_path

from fantread.models import OutputFormat


ENV_API_KEY = "DEEPSEEK_API_KEY"
ENV_CONFIG_DIR = "FANTREAD_CONFIG_DIR"
ENV_BASE_URL = "DEEPSEEK_BASE_URL"
ENV_FRESH_RUN = "FANTREAD_FRESH"
KEYRING_SERVICE = "fantread.deepseek"
KEYRING_ACCOUNT = "default"


class ConfigError(RuntimeError):
    pass


@dataclass(slots=True)
class AppConfig:
    model: str = "deepseek-v4-flash"
    output_format: str = OutputFormat.TERMINAL.value
    thinking: bool = False
    base_url: str = "https://api.deepseek.com"
    language: str = "auto"


def fresh_run_enabled() -> bool:
    """Default to stateless runs while the application is under development."""
    value = os.getenv(ENV_FRESH_RUN, "1").strip().lower()
    return value not in {"0", "false", "no", "off"}


def config_dir() -> Path:
    override = os.getenv(ENV_CONFIG_DIR)
    if override:
        return Path(override).expanduser()
    return user_config_path("fantread", appauthor=False)


def config_file() -> Path:
    return config_dir() / "config.json"


def load_config() -> AppConfig:
    path = config_file()
    if not path.exists():
        return AppConfig()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"配置文件无法读取：{path}") from exc
    if not isinstance(raw, dict):
        raise ConfigError(f"配置文件格式无效：{path}")

    allowed = {item.name for item in fields(AppConfig)}
    values = {key: value for key, value in raw.items() if key in allowed}
    config = AppConfig(**values)
    _validate_config(config)
    return config


def save_config(config: AppConfig) -> Path:
    _validate_config(config)
    path = config_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    try:
        temporary.write_text(
            json.dumps(asdict(config), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.chmod(0o600)
        temporary.replace(path)
        path.chmod(0o600)
    except OSError as exc:
        raise ConfigError(f"配置无法保存到：{path}") from exc
    return path


def api_key_source() -> str | None:
    if os.getenv(ENV_API_KEY):
        return f"环境变量 {ENV_API_KEY}"
    try:
        if keyring.get_password(KEYRING_SERVICE, KEYRING_ACCOUNT):
            return "系统密钥环"
    except KeyringError:
        pass
    return None


def resolve_api_key() -> str | None:
    value = os.getenv(ENV_API_KEY)
    if value:
        return value.strip()
    try:
        value = keyring.get_password(KEYRING_SERVICE, KEYRING_ACCOUNT)
    except KeyringError:
        return None
    return value.strip() if value else None


def store_api_key(api_key: str) -> None:
    value = api_key.strip()
    if not value:
        raise ConfigError("API Key 不能为空")
    try:
        keyring.set_password(KEYRING_SERVICE, KEYRING_ACCOUNT, value)
    except KeyringError as exc:
        raise ConfigError(f"系统密钥环不可用，请改用环境变量 {ENV_API_KEY}") from exc


def _validate_config(config: AppConfig) -> None:
    if not config.model.strip():
        raise ConfigError("model 不能为空")
    if config.output_format not in {item.value for item in OutputFormat}:
        raise ConfigError(f"未知输出格式：{config.output_format}")
    if not config.base_url.startswith(("https://", "http://")):
        raise ConfigError("base_url 必须是 http(s) 地址")
    if config.language not in {"auto", "zh", "en"}:
        raise ConfigError("language 只能是 auto、zh 或 en")


def safe_config_dict(config: AppConfig) -> dict[str, Any]:
    return {
        **asdict(config),
        "api_key": "已配置" if api_key_source() else "未配置",
        "api_key_source": api_key_source(),
    }
