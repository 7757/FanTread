from __future__ import annotations

import json
import re
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.text import Text

from fantread.models import OutputFormat, ReadResult


def render_terminal(console: Console, result: ReadResult) -> None:
    article = result.article
    heading = Text()
    heading.append("✓ ", style="green")
    heading.append(article.title, style="bold")
    console.print(heading)

    details: list[str] = []
    if article.author:
        details.append(article.author)
    if article.published_at:
        details.append(article.published_at)
    if result.model:
        thinking = " · 深度思考" if result.thinking else ""
        details.append(f"{result.model}{thinking}")
    details.append(f"{article.char_count:,} 字符")
    if details:
        console.print(Text(" · ".join(details), style="dim"))
    console.print(Text(article.final_url, style="dim"))
    console.print()
    console.print(Markdown(result.content))


def serialize(result: ReadResult, output_format: OutputFormat) -> str:
    if output_format is OutputFormat.JSON:
        return json.dumps(result.as_dict(), ensure_ascii=False, indent=2) + "\n"
    if output_format in {OutputFormat.MARKDOWN, OutputFormat.TERMINAL}:
        return _markdown_document(result)
    return _text_document(result)


def write_result(
    result: ReadResult,
    output_format: OutputFormat,
    path: Path,
    *,
    force: bool = False,
) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"文件已存在：{path}（使用 --force 覆盖）")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialize(result, output_format), encoding="utf-8")


def banner(*, fresh_run: bool = False) -> Text:
    title = Text("FanTread", style="bold cyan")
    title.append(" · 贴链接，读重点", style="dim")
    if fresh_run:
        title.append(" · 全新会话", style="yellow")
    return title


def _markdown_document(result: ReadResult) -> str:
    article = result.article
    rows = {
        "title": article.title,
        "source": article.final_url,
        "author": article.author,
        "published_at": article.published_at,
        "model": result.model,
    }
    frontmatter = "\n".join(
        f"{key}: {json.dumps(value, ensure_ascii=False)}"
        for key, value in rows.items()
        if value is not None
    )
    return f"---\n{frontmatter}\n---\n\n{result.content.strip()}\n"


def _text_document(result: ReadResult) -> str:
    article = result.article
    header = [
        article.title,
        f"来源：{article.final_url}",
        "处理：AI 自动整理",
    ]
    if article.author:
        header.insert(1, f"作者：{article.author}")
    return "\n".join(header) + "\n\n" + _markdown_to_text(result.content) + "\n"


def _markdown_to_text(value: str) -> str:
    """Remove presentation-only Markdown while keeping readable structure."""
    lines: list[str] = []
    for line in value.strip().splitlines():
        line = re.sub(r"^\s{0,3}#{1,6}\s+", "", line)
        line = re.sub(r"^\s{0,3}>\s?", "", line)
        if re.fullmatch(r"\s*[-*_]{3,}\s*", line):
            continue
        line = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", line)
        line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
        line = re.sub(r"(\*\*|__)(.*?)\1", r"\2", line)
        line = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", line)
        line = re.sub(r"`([^`]+)`", r"\1", line)
        lines.append(line.rstrip())
    return "\n".join(lines).strip()
