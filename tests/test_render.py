import json

import pytest
from rich.console import Console

from fantread.models import Article, OutputFormat, ReadResult
from fantread.render import banner, render_terminal, serialize, write_result


def result() -> ReadResult:
    return ReadResult(
        article=Article(
            url="https://example.com/a",
            final_url="https://example.com/a",
            title='标题 "A"',
            author="作者",
            text="正文",
        ),
        content="# 一句话总结\n\n这是结果。",
        model="deepseek-v4-flash",
    )


def test_json_serialization_is_machine_readable() -> None:
    value = json.loads(serialize(result(), OutputFormat.JSON))
    assert value["title"] == '标题 "A"'
    assert value["content"].startswith("# 一句话")
    assert "note" not in value
    assert "mode" not in value


def test_markdown_has_frontmatter_and_source() -> None:
    value = serialize(result(), OutputFormat.MARKDOWN)
    assert value.startswith("---\n")
    assert 'title: "标题 \\"A\\""' in value
    assert 'source: "https://example.com/a"' in value
    assert "# 一句话总结" in value


def test_text_format_removes_presentation_markdown() -> None:
    value = serialize(result(), OutputFormat.TEXT)
    assert "# 一句话总结" not in value
    assert "一句话总结" in value


def test_terminal_ui_is_compact_and_borderless() -> None:
    console = Console(record=True, color_system=None, width=100)
    console.print(banner(fresh_run=True))
    render_terminal(console, result())
    value = console.export_text()

    assert "FanTread · 贴链接，读重点 · 全新会话" in value
    assert '✓ 标题 "A"' in value
    assert "deepseek-v4-flash" in value
    assert "╭" not in value
    assert "处理：AI 自动整理" not in value


def test_write_result_refuses_overwrite_unless_forced(tmp_path) -> None:
    path = tmp_path / "nested" / "result.md"
    write_result(result(), OutputFormat.MARKDOWN, path)
    original = path.read_text(encoding="utf-8")

    with pytest.raises(FileExistsError, match="--force"):
        write_result(result(), OutputFormat.TEXT, path)

    assert path.read_text(encoding="utf-8") == original
    write_result(result(), OutputFormat.TEXT, path, force=True)
    assert path.read_text(encoding="utf-8").startswith('标题 "A"')


def test_text_output_removes_links_images_and_emphasis() -> None:
    value = result()
    value.content = (
        "# 标题\n\n"
        "**重点**与[链接](https://example.com)，"
        "以及![示意图](https://example.com/image.png)。"
    )

    rendered = serialize(value, OutputFormat.TEXT)

    assert "**" not in rendered
    assert "https://example.com/image.png" not in rendered
    assert "重点与链接" in rendered
    assert "示意图" in rendered


@pytest.mark.parametrize("width", [32, 48, 80, 120])
def test_terminal_rendering_handles_narrow_widths(width) -> None:
    console = Console(record=True, color_system=None, width=width)
    render_terminal(console, result())

    assert "一句话总结" in console.export_text()
