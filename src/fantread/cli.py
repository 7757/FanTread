from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

from fantread import __version__
from fantread.config import (
    ENV_API_KEY,
    ENV_BASE_URL,
    AppConfig,
    ConfigError,
    api_key_source,
    config_file,
    fresh_run_enabled,
    load_config,
    resolve_api_key,
    safe_config_dict,
    save_config,
    store_api_key,
)
from fantread.deepseek import DeepSeekClient, DeepSeekError
from fantread.extractor import ArticleExtractor, ExtractionError
from fantread.models import MODEL_CATALOG, Article, OutputFormat
from fantread.render import banner, render_terminal, serialize, write_result
from fantread.summarizer import Summarizer
from fantread.user_prompt import prepare_user_prompt


app = typer.Typer(
    name="fantread",
    help="贴一个链接，让 AI 自动整理成最适合阅读的样子。",
    epilog=(
        '**常用：** `fan` · `fan "链接" "补充要求"` · '
        '`fan "链接" -f md -o result.md`；完整选项：'
        '`fan "链接" --help`'
    ),
    no_args_is_help=False,
    invoke_without_command=True,
    add_completion=False,
    rich_markup_mode="markdown",
)
console = Console()
err_console = Console(stderr=True)


@app.callback()
def app_callback(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            help="显示版本。",
            is_eager=True,
        ),
    ] = False,
) -> None:
    if version:
        console.print(f"FanTread {__version__}")
        raise typer.Exit()


@app.command("read", help="读取并处理一个链接。", hidden=True)
def read_command(
    url: Annotated[str, typer.Argument(help="http(s) 网页链接。")],
    prompt: Annotated[
        str | None,
        typer.Argument(help="可选：告诉 AI 你希望如何处理。"),
    ] = None,
    output_format: Annotated[
        str | None,
        typer.Option("--format", "-f", help="terminal/markdown/md/text/json"),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="保存到文件；不指定则输出到终端。"),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option("--model", help="DeepSeek 模型 ID。"),
    ] = None,
    thinking: Annotated[
        bool | None,
        typer.Option(
            "--thinking/--no-thinking",
            help="开启或关闭 DeepSeek 深度思考。",
        ),
    ] = None,
    language: Annotated[
        str | None,
        typer.Option("--language", help="auto/zh/en"),
    ] = None,
    stream: Annotated[
        bool,
        typer.Option("--stream/--no-stream", help="流式显示 AI 输出。"),
    ] = True,
    timeout: Annotated[
        float,
        typer.Option("--timeout", min=5.0, help="网页读取超时（秒）。"),
    ] = 25.0,
    force: Annotated[
        bool,
        typer.Option("--force", help="允许覆盖已有输出文件。"),
    ] = False,
) -> None:
    try:
        fresh_run = fresh_run_enabled()
        choose_model_interactively = False
        persistent_config: AppConfig | None = None
        if fresh_run:
            defaults = AppConfig()
            selected_format = _parse_format(
                output_format or OutputFormat.TERMINAL.value
            )
            selected_model = model or defaults.model
            choose_model_interactively = model is None and sys.stdin.isatty()
            selected_thinking = False if thinking is None else thinking
            selected_language = language or "auto"
            selected_base_url = os.getenv(ENV_BASE_URL, defaults.base_url)
        else:
            first_run = not config_file().exists()
            persistent_config = load_config()
            selected_format = _parse_format(
                output_format or persistent_config.output_format
            )
            selected_model = model or persistent_config.model
            selected_thinking = (
                persistent_config.thinking if thinking is None else thinking
            )
            selected_language = language or persistent_config.language
            selected_base_url = persistent_config.base_url
            choose_model_interactively = (
                first_run and model is None and sys.stdin.isatty()
            )
        if selected_language not in {"auto", "zh", "en"}:
            raise ValueError("--language 只能是 auto、zh 或 en")
        user_prompt = prepare_user_prompt(prompt)

        with err_console.status("[cyan]正在读取并清理页面…[/cyan]"):
            article = ArticleExtractor(timeout=timeout).fetch_and_extract(url)
        _show_article_ready(article)

        if choose_model_interactively:
            selected_model = _choose_model(default=selected_model)
            if persistent_config is not None:
                persistent_config.model = selected_model
                save_config(persistent_config)
                err_console.print("[green]✓[/green] 默认模型已保存")
        api_key = _ensure_api_key(fresh_run=fresh_run)

        live_stream: _LiveStream | None = None
        if (
            stream
            and selected_format is OutputFormat.TERMINAL
            and output is None
            and console.is_terminal
        ):
            live_stream = _LiveStream(console)

        with DeepSeekClient(
            api_key=api_key,
            model=selected_model,
            base_url=selected_base_url,
            thinking=selected_thinking,
        ) as client:
            summarizer = Summarizer(client)
            if live_stream:
                live_stream.start()
            try:
                result = summarizer.run(
                    article,
                    language=selected_language,
                    user_prompt=user_prompt,
                    stream=stream,
                    on_delta=live_stream.append if live_stream else None,
                    on_progress=_progress_message,
                )
            finally:
                if live_stream:
                    live_stream.stop()

        if output:
            write_result(result, selected_format, output, force=force)
            err_console.print(f"[green]✓[/green] 已保存到 [bold]{output}[/bold]")
        elif selected_format is OutputFormat.TERMINAL:
            render_terminal(console, result)
        else:
            # Rich wraps long lines for terminal display. Machine-readable
            # formats must go to stdout byte-for-byte, especially JSON strings.
            sys.stdout.write(serialize(result, selected_format))
            sys.stdout.flush()
    except (
        ConfigError,
        ExtractionError,
        DeepSeekError,
        ValueError,
        FileExistsError,
    ) as exc:
        err_console.print(f"[bold red]错误：[/bold red]{exc}")
        raise typer.Exit(1) from exc
    except KeyboardInterrupt as exc:
        err_console.print("\n[yellow]已取消。[/yellow]")
        raise typer.Exit(130) from exc


@app.command("interactive", hidden=True)
def interactive_command() -> None:
    fresh_run = fresh_run_enabled()
    err_console.print(banner(fresh_run=fresh_run))
    err_console.print()
    url = _prompt_for_url()
    prompt = (
        Prompt.ask(
            "[cyan]要求[/cyan] [dim]（可选）[/dim]",
            default="",
            show_default=False,
            console=err_console,
        ).strip()
        or None
    )

    read_command(
        url=url,
        prompt=prompt,
        output_format=None,
        output=None,
        model=None,
        thinking=None,
        language=None,
        stream=True,
        timeout=25.0,
        force=False,
    )


def _prompt_for_url() -> str:
    while True:
        value = Prompt.ask("[cyan]链接[/cyan]", console=err_console)
        try:
            return ArticleExtractor.normalize_url(value)
        except ExtractionError as exc:
            err_console.print(f"[red]✗[/red] {exc}")


@app.command("setup", help="配置默认模型和 API Key。")
def setup_command(
    check: Annotated[
        bool,
        typer.Option("--check/--no-check", help="配置后测试 API 连接。"),
    ] = True,
) -> None:
    try:
        fresh_run = fresh_run_enabled()
        console.print(banner(fresh_run=fresh_run))
        if fresh_run:
            console.print(
                "\n[yellow]当前为全新运行开发模式，不读取或保存配置。"
                "\n直接运行 `fan` 即可测试完整首次使用流程。[/yellow]"
            )
            return
        console.print("\n[bold]首次使用设置[/bold]\n")
        config = load_config()
        config.model = _choose_model(default=config.model)
        config.output_format = OutputFormat.TERMINAL.value
        config.thinking = False
        path = save_config(config)
        console.print(f"[green]✓[/green] 默认设置已保存：{path}")

        key = resolve_api_key()
        source = api_key_source()
        if key and source:
            console.print(f"[green]✓[/green] 已从{source}找到 API Key")
            replace = Confirm.ask("要更换这个 Key 吗？", default=False)
        else:
            replace = Confirm.ask("现在输入 DeepSeek API Key？", default=True)

        if replace:
            key = Prompt.ask(
                "DeepSeek API Key",
                password=True,
            ).strip()
            if not key:
                raise ConfigError("API Key 不能为空")
            if Confirm.ask("保存到系统密钥环？", default=True):
                store_api_key(key)
                console.print("[green]✓[/green] Key 已安全存入系统密钥环")
            else:
                console.print(
                    f"[yellow]Key 未保存。下次可设置环境变量 {ENV_API_KEY}。[/yellow]"
                )

        if check and key:
            with err_console.status("[cyan]正在测试 DeepSeek 连接…[/cyan]"):
                with DeepSeekClient(
                    api_key=key,
                    model=config.model,
                    base_url=config.base_url,
                    thinking=config.thinking,
                    timeout=30,
                ) as client:
                    models = client.validate()
            suffix = f"（检测到 {len(models)} 个可用模型）" if models else ""
            console.print(f"[green]✓[/green] DeepSeek 连接正常{suffix}")
        console.print("\n[bold cyan]设置完成。[/bold cyan] 直接运行 `fan` 即可开始。")
    except (ConfigError, DeepSeekError, ValueError) as exc:
        err_console.print(f"[bold red]错误：[/bold red]{exc}")
        raise typer.Exit(1) from exc
    except KeyboardInterrupt as exc:
        err_console.print("\n[yellow]已取消。[/yellow]")
        raise typer.Exit(130) from exc


@app.command("models", help="列出内置 DeepSeek 模型。")
def models_command() -> None:
    config = AppConfig() if fresh_run_enabled() else load_config()
    table = Table(title="DeepSeek 模型", border_style="cyan")
    table.add_column("默认", justify="center")
    table.add_column("模型 ID", style="bold")
    table.add_column("定位")
    for item in MODEL_CATALOG:
        table.add_row("●" if item.id == config.model else "", item.id, item.description)
    console.print(table)
    console.print("[dim]也可用 --model 传入官方 API 当前支持的其他模型 ID。[/dim]")


@app.command("config", help="查看当前配置（不会显示 Key）。")
def config_command() -> None:
    if fresh_run_enabled():
        console.print(
            Panel(
                "当前为全新运行开发模式。\n已保存的模型、Key 和配置不会被读取。",
                title="FanTread 配置",
                border_style="yellow",
            )
        )
        return
    config = load_config()
    values = safe_config_dict(config)
    table = Table.grid(padding=(0, 2))
    table.add_column(style="dim")
    for key, value in values.items():
        table.add_row(key, str(value if value is not None else "—"))
    console.print(Panel(table, title="FanTread 配置", border_style="cyan"))
    console.print(f"[dim]配置文件：{config_file()}[/dim]")


def _ensure_api_key(*, fresh_run: bool) -> str:
    environment_key = os.getenv(ENV_API_KEY)
    if fresh_run:
        if sys.stdin.isatty():
            key = Prompt.ask(
                "[yellow]DeepSeek Key[/yellow] [dim]（仅本次，不保存）[/dim]",
                password=True,
                console=err_console,
            ).strip()
            if not key:
                raise ConfigError("API Key 不能为空")
            return key
        if environment_key:
            return environment_key.strip()
        else:
            raise ConfigError(
                f"开发模式需要本次运行的 API Key；请在交互终端输入，"
                f"或临时设置环境变量 {ENV_API_KEY}"
            )
    if environment_key:
        return environment_key.strip()

    key = resolve_api_key()
    if key:
        return key
    if not sys.stdin.isatty():
        raise ConfigError(
            f"自动整理需要 API Key。请运行 fan setup，或设置环境变量 {ENV_API_KEY}"
        )
    err_console.print(
        Panel(
            "自动整理需要 DeepSeek API Key。\n"
            "输入内容会被隐藏；你可以选择存入系统密钥环。\n"
            "清理后的正文会发送给 DeepSeek 生成结果。",
            title="首次使用",
            border_style="yellow",
        )
    )
    key = Prompt.ask("DeepSeek API Key", password=True).strip()
    if not key:
        raise ConfigError("API Key 不能为空")
    if Confirm.ask("保存到系统密钥环，免去下次输入？", default=True):
        store_api_key(key)
        err_console.print("[green]✓[/green] Key 已存入系统密钥环")
    return key


def _choose_model(default: str = "deepseek-v4-flash") -> str:
    labels: list[str] = []
    for index, item in enumerate(MODEL_CATALOG, start=1):
        marker = "（默认）" if item.id == default else ""
        labels.append(f"{index} {item.label}{marker}")
    labels.append(f"{len(MODEL_CATALOG) + 1} 自定义")
    default_index = next(
        (
            str(index)
            for index, item in enumerate(MODEL_CATALOG, start=1)
            if item.id == default
        ),
        "1",
    )
    selected = Prompt.ask(
        f"[cyan]模型[/cyan] [dim]{' · '.join(labels)}[/dim]",
        choices=[str(index) for index in range(1, len(MODEL_CATALOG) + 2)],
        default=default_index,
        show_choices=False,
        console=err_console,
    )
    if int(selected) == len(MODEL_CATALOG) + 1:
        model = Prompt.ask("模型 ID", console=err_console).strip()
        if not model:
            raise ValueError("模型 ID 不能为空")
        return model
    return MODEL_CATALOG[int(selected) - 1].id


def _show_article_ready(article: Article) -> None:
    if not err_console.is_terminal:
        return
    title = article.title
    if len(title) > 72:
        title = title[:71].rstrip() + "…"
    message = Text()
    message.append("✓ ", style="green")
    message.append(title, style="bold")
    message.append(f" · {article.char_count:,} 字符", style="dim")
    err_console.print(message)


def _parse_format(value: str) -> OutputFormat:
    aliases = {"md": "markdown", "plain": "text"}
    normalized = aliases.get(value.lower(), value.lower())
    try:
        return OutputFormat(normalized)
    except ValueError as exc:
        choices = ", ".join(item.value for item in OutputFormat)
        raise ValueError(f"未知格式 {value!r}；可选：{choices}") from exc


def _progress_message(message: str) -> None:
    if err_console.is_terminal:
        err_console.print(f"[dim]› {message}[/dim]")


class _LiveStream:
    def __init__(self, output_console: Console) -> None:
        self.console = output_console
        self.content = ""
        self._last_update = 0.0
        self._live: Live | None = None

    def start(self) -> None:
        self._live = Live(
            Text("DeepSeek 正在整理…", style="dim"),
            console=self.console,
            refresh_per_second=8,
            transient=True,
        )
        self._live.start()

    def append(self, delta: str) -> None:
        self.content += delta
        now = time.monotonic()
        if self._live and (now - self._last_update > 0.08 or delta.endswith("\n")):
            self._live.update(Markdown(self.content))
            self._last_update = now

    def stop(self) -> None:
        if self._live:
            self._live.stop()
            self._live = None


def _looks_like_url(value: str) -> bool:
    if value.startswith(("http://", "https://")):
        return True
    return "." in value and not value.startswith(("-", "."))


def main() -> None:
    args = sys.argv[1:]
    if not args:
        args = ["interactive"]
    elif _looks_like_url(args[0]):
        args = ["read", *args]
    executable = Path(sys.argv[0]).name
    program_name = executable if executable in {"fan", "fantread"} else "fan"
    app(prog_name=program_name, args=args)


if __name__ == "__main__":
    main()
