import json

import pytest
from typer.testing import CliRunner

from fantread.cli import (
    _choose_model,
    _ensure_api_key,
    _looks_like_url,
    _parse_format,
    _prompt_for_url,
    app,
    read_command,
)
from fantread.config import ConfigError
from fantread.models import Article, ReadResult


def test_json_command_writes_unwrapped_machine_output(monkeypatch) -> None:
    captured: dict[str, object] = {}
    article = Article(
        url="https://example.com",
        final_url="https://example.com",
        title="长标题",
        text=("这是一行很长的正文，不能被终端宽度强制折行。" * 30),
    )
    monkeypatch.setattr(
        "fantread.cli.ArticleExtractor.fetch_and_extract",
        lambda self, url: article,
    )
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")

    def fake_run(self, article, **kwargs):
        captured.update(kwargs)
        return ReadResult(
            article=article,
            content="# 自动整理\n\n这是一行很长的结果。" * 20,
            model=self.client.model,
        )

    monkeypatch.setattr("fantread.cli.Summarizer.run", fake_run)
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "read",
            "https://example.com",
            "请尽量保持原文，只整理重点。",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["content"].startswith("# 自动整理")
    assert captured["user_prompt"] == "请尽量保持原文，只整理重点。"
    assert "note" not in payload
    assert "mode" not in payload


def test_fresh_interactive_run_always_asks_for_a_temporary_key(
    monkeypatch,
) -> None:
    class InteractiveInput:
        @staticmethod
        def isatty() -> bool:
            return True

    monkeypatch.setenv("DEEPSEEK_API_KEY", "stale-environment-key")
    monkeypatch.setattr("fantread.cli.sys.stdin", InteractiveInput())
    monkeypatch.setattr(
        "fantread.cli.Prompt.ask",
        lambda *args, **kwargs: "new-temporary-key",
    )

    assert _ensure_api_key(fresh_run=True) == "new-temporary-key"


def test_fresh_interactive_run_fetches_before_model_and_key(
    monkeypatch,
) -> None:
    events: list[str] = []
    article = Article(
        url="https://example.com",
        final_url="https://example.com",
        title="测试文章",
        text="有效正文。" * 40,
    )

    class InteractiveInput:
        @staticmethod
        def isatty() -> bool:
            return True

    def fetch(self, url):
        events.append("fetch")
        return article

    def choose_model(*, default):
        events.append("model")
        return default

    def ensure_key(*, fresh_run):
        events.append("key")
        return "temporary-key"

    def summarize(self, article, **kwargs):
        return ReadResult(
            article=article,
            content="# 结果\n\n正文",
            model=self.client.model,
        )

    monkeypatch.setenv("FANTREAD_FRESH", "1")
    monkeypatch.setattr("fantread.cli.sys.stdin", InteractiveInput())
    monkeypatch.setattr(
        "fantread.cli.ArticleExtractor.fetch_and_extract",
        fetch,
    )
    monkeypatch.setattr("fantread.cli._choose_model", choose_model)
    monkeypatch.setattr("fantread.cli._ensure_api_key", ensure_key)
    monkeypatch.setattr("fantread.cli.Summarizer.run", summarize)

    read_command(
        url="https://example.com",
        prompt=None,
        output_format=None,
        output=None,
        model=None,
        thinking=None,
        language=None,
        stream=False,
        timeout=25.0,
        force=False,
    )

    assert events == ["fetch", "model", "key"]


def test_first_persistent_run_saves_model_and_skips_later_picker(
    monkeypatch,
    tmp_path,
) -> None:
    events: list[str] = []
    article = Article(
        url="https://example.com",
        final_url="https://example.com",
        title="测试文章",
        text="有效正文。" * 40,
    )

    class InteractiveInput:
        @staticmethod
        def isatty() -> bool:
            return True

    def fetch(self, url):
        events.append("fetch")
        return article

    def choose_model(*, default):
        events.append("model")
        return "deepseek-v4-pro"

    def ensure_key(*, fresh_run):
        events.append("key")
        assert fresh_run is False
        return "stored-key"

    def summarize(self, article, **kwargs):
        return ReadResult(
            article=article,
            content="# 结果\n\n正文",
            model=self.client.model,
        )

    monkeypatch.delenv("FANTREAD_FRESH", raising=False)
    monkeypatch.setenv("FANTREAD_CONFIG_DIR", str(tmp_path))
    monkeypatch.setattr("fantread.cli.sys.stdin", InteractiveInput())
    monkeypatch.setattr("fantread.cli.ArticleExtractor.fetch_and_extract", fetch)
    monkeypatch.setattr("fantread.cli._choose_model", choose_model)
    monkeypatch.setattr("fantread.cli._ensure_api_key", ensure_key)
    monkeypatch.setattr("fantread.cli.Summarizer.run", summarize)

    read_command(
        url="https://example.com",
        prompt=None,
        output_format=None,
        output=None,
        model=None,
        thinking=None,
        language=None,
        stream=False,
        timeout=25.0,
        force=False,
    )

    assert events == ["fetch", "model", "key"]
    assert json.loads((tmp_path / "config.json").read_text())["model"] == (
        "deepseek-v4-pro"
    )

    events.clear()
    read_command(
        url="https://example.com",
        prompt=None,
        output_format=None,
        output=None,
        model=None,
        thinking=None,
        language=None,
        stream=False,
        timeout=25.0,
        force=False,
    )

    assert events == ["fetch", "key"]


def test_persistent_run_reads_key_without_prompt(monkeypatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setattr("fantread.cli.resolve_api_key", lambda: "stored-key")

    assert _ensure_api_key(fresh_run=False) == "stored-key"


def test_interactive_url_prompt_retries_invalid_input(monkeypatch) -> None:
    answers = iter(["ftp://example.com/file", "example.com/article"])
    monkeypatch.setattr(
        "fantread.cli.Prompt.ask",
        lambda *args, **kwargs: next(answers),
    )

    assert _prompt_for_url() == "https://example.com/article"


def test_noninteractive_fresh_key_uses_environment(monkeypatch) -> None:
    class NonInteractiveInput:
        @staticmethod
        def isatty() -> bool:
            return False

    monkeypatch.setattr("fantread.cli.sys.stdin", NonInteractiveInput())
    monkeypatch.setenv("DEEPSEEK_API_KEY", " automation-key ")

    assert _ensure_api_key(fresh_run=True) == "automation-key"


def test_noninteractive_fresh_key_has_actionable_missing_key_error(
    monkeypatch,
) -> None:
    class NonInteractiveInput:
        @staticmethod
        def isatty() -> bool:
            return False

    monkeypatch.setattr("fantread.cli.sys.stdin", NonInteractiveInput())
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    with pytest.raises(ConfigError, match="DEEPSEEK_API_KEY"):
        _ensure_api_key(fresh_run=True)


def test_model_picker_supports_builtin_and_custom_models(monkeypatch) -> None:
    monkeypatch.setattr(
        "fantread.cli.Prompt.ask",
        lambda *args, **kwargs: "2",
    )
    assert _choose_model() == "deepseek-v4-pro"

    answers = iter(["3", "deepseek-future"])
    monkeypatch.setattr(
        "fantread.cli.Prompt.ask",
        lambda *args, **kwargs: next(answers),
    )
    assert _choose_model() == "deepseek-future"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("md", "markdown"),
        ("MARKDOWN", "markdown"),
        ("plain", "text"),
        ("json", "json"),
    ],
)
def test_format_aliases(value, expected) -> None:
    assert _parse_format(value).value == expected


def test_invalid_format_and_url_detection() -> None:
    with pytest.raises(ValueError, match="未知格式"):
        _parse_format("pdf")

    assert _looks_like_url("https://example.com")
    assert _looks_like_url("example.com/article")
    assert not _looks_like_url("setup")


def test_setup_is_non_persistent_in_fresh_mode(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("FANTREAD_FRESH", "1")
    monkeypatch.setenv("FANTREAD_CONFIG_DIR", str(tmp_path))
    result = CliRunner().invoke(app, ["setup", "--no-check"])

    assert result.exit_code == 0
    assert "不读取或保存配置" in result.stdout
    assert not (tmp_path / "config.json").exists()


def test_setup_persists_model_and_key_by_default(monkeypatch, tmp_path) -> None:
    stored_keys: list[str] = []
    confirmations = iter([True, True])

    monkeypatch.delenv("FANTREAD_FRESH", raising=False)
    monkeypatch.setenv("FANTREAD_CONFIG_DIR", str(tmp_path))
    monkeypatch.setattr(
        "fantread.cli._choose_model",
        lambda *, default: "deepseek-v4-pro",
    )
    monkeypatch.setattr("fantread.cli.resolve_api_key", lambda: None)
    monkeypatch.setattr("fantread.cli.api_key_source", lambda: None)
    monkeypatch.setattr(
        "fantread.cli.Confirm.ask",
        lambda *args, **kwargs: next(confirmations),
    )
    monkeypatch.setattr(
        "fantread.cli.Prompt.ask",
        lambda *args, **kwargs: "test-key",
    )
    monkeypatch.setattr("fantread.cli.store_api_key", stored_keys.append)

    result = CliRunner().invoke(app, ["setup", "--no-check"])

    assert result.exit_code == 0
    assert json.loads((tmp_path / "config.json").read_text())["model"] == (
        "deepseek-v4-pro"
    )
    assert stored_keys == ["test-key"]
    assert "设置完成" in result.stdout
