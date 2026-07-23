# FanTread

[English](README.md) | [简体中文](README.zh-CN.md)

[Official website](https://7757.github.io/FanTread/) ·
[npm](https://www.npmjs.com/package/fantread) ·
[GitHub](https://github.com/7757/FanTread)

[![npm](https://img.shields.io/npm/v/fantread?color=18a999)](https://www.npmjs.com/package/fantread)
[![CI](https://github.com/7757/FanTread/actions/workflows/ci.yml/badge.svg)](https://github.com/7757/FanTread/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/7757/FanTread)](LICENSE)

Paste a link. FanTread extracts the readable content, removes page noise, and
uses DeepSeek to organize it in the format that best fits the source.

There are no summary modes to memorize. FanTread decides whether a page is a
news story, long-form article, tutorial, opinion piece, or discussion post, then
adapts the information density and layout automatically.

> [!IMPORTANT]
> FanTread is currently in alpha. The default configuration intentionally starts
> a fresh session on every interactive run so the onboarding flow is easy to
> test.

## Highlights

- Automatically chooses the right structure and level of detail
- Purpose-built cleanup for WeChat Official Account articles
- General article extraction powered by Trafilatura and Beautiful Soup
- Recognizes Schema.org `DiscussionForumPosting` and `SocialMediaPosting` pages
- Accepts one optional instruction for emphasis, tone, detail, or formatting
- Supports DeepSeek V4 Flash, V4 Pro, and custom model IDs
- Streams results in a friendly Rich terminal interface
- Exports terminal, Markdown, plain-text, and JSON output
- Splits long pages into chunks and merges the intermediate results
- Treats webpage text as untrusted source data rather than model instructions

## How it works

```text
URL
 └─> fetch and extract locally
      └─> remove navigation, ads, calls to action, and repeated noise
           └─> send the cleaned content and optional user instruction to DeepSeek
                └─> automatically organize and render the result
```

The optional instruction is part of the model prompt. It influences the result,
but is not appended to the generated article or exported as a separate comment.

## Requirements

- Node.js 18 or newer when installing through npm
- Python 3.11 or newer
- A [DeepSeek API key](https://platform.deepseek.com/api_keys)
- Network access to the source page and the DeepSeek API

## Installation

### npm

Install FanTread globally, then run `fan`:

```bash
npm install -g fantread
fan
```

On the first `fan` run, FanTread detects Python 3.11 or newer and creates a
private environment inside the package automatically. No separate pip command
is required. Set `FANTREAD_PYTHON` if a supported Python interpreter is not on
your `PATH`.

You can also try it without keeping a global installation:

```bash
npx fantread
```

### From source with pipx

Clone this repository, enter its directory, and install the CLI with
[pipx](https://pipx.pypa.io/):

```bash
pipx install .
fan --version
```

For development, use an editable virtual environment:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### After a PyPI release

Once FanTread has been published to PyPI, users will be able to install it
globally with either command:

```bash
pipx install fantread
```

```bash
uv tool install fantread
```

## Quick start

Launch the interactive guide:

```bash
fan
```

The guide asks for:

```text
Link
Optional instruction
DeepSeek model
Temporary API key (masked and not saved)
```

Or pass a link directly:

```bash
fan "https://mp.weixin.qq.com/s/Rqv-4yFGUTuLxMaRSt1XDg"
```

Add one plain-language instruction after the link:

```bash
fan "https://example.com/article" \
  "Preserve as much of the original wording as possible and only remove noise."
```

```bash
fan "https://example.com/tutorial" \
  "Focus on the exact steps, prerequisites, and common mistakes."
```

FanTread decides whether the result should be concise, detailed, step-by-step,
or discussion-oriented. Users do not select a mode.

## Output

The default output is rendered in the terminal:

```bash
fan "https://example.com/article"
```

Save Markdown:

```bash
fan "https://example.com/article" --format md --output result.md
```

Print plain text:

```bash
fan "https://example.com/article" --format text
```

Produce machine-readable JSON:

```bash
fan "https://example.com/article" --format json
```

Available output formats:

| Format | Contents |
| --- | --- |
| `terminal` | Rich metadata panels and rendered Markdown |
| `markdown` / `md` | Markdown with YAML front matter |
| `text` | Plain text |
| `json` | Source metadata, model, token usage, and generated content |

Progress and errors are written to stderr. Markdown, text, and JSON output are
written to stdout, so they can safely be redirected or piped.

## Models

FanTread currently offers:

| Model | Best for |
| --- | --- |
| `deepseek-v4-flash` | Faster, lower-cost everyday reading; the default |
| `deepseek-v4-pro` | Higher-quality processing for long or complex material |
| Custom model ID | Compatibility with later DeepSeek releases |

Use `--thinking` to enable DeepSeek thinking mode:

```bash
fan "https://example.com/complex-article" --thinking
```

List the built-in choices:

```bash
fan models
```

See the
[official DeepSeek model documentation](https://api-docs.deepseek.com/quick_start/pricing/)
for current availability and pricing.

## Fresh development sessions

Fresh mode is enabled by default while FanTread is under development. Every
interactive run:

- ignores saved FanTread configuration
- ignores keys stored in the system keyring
- asks for a model again
- asks for a temporary masked API key again
- keeps the key only in process memory

For non-interactive automation, provide a key only for the current environment:

```bash
export DEEPSEEK_API_KEY="your-key"
fan "https://example.com/article" --format json
```

Interactive fresh runs still prompt for a key even if that environment variable
exists.

To enable persistent production-style configuration later:

```bash
export FANTREAD_FRESH=0
fan setup
```

`fan setup` lets the user choose a default model and optionally store the API key
in the operating system keyring. The key is never written to FanTread's JSON
configuration file.

## Privacy and security

FanTread downloads and cleans the page locally, then sends the cleaned text and
the optional user instruction to DeepSeek to generate the result.

- API key input is masked.
- Fresh interactive sessions do not persist the key.
- Persistent mode uses the operating system keyring when the user opts in.
- Keys are not written to project files or exported results.
- Page content is delimited as source material in the model prompt to reduce
  prompt-injection risk.

Never commit a real API key. If a key has been pasted into an issue, chat,
terminal recording, or public log, revoke it and create a new one.

## Current limitations

- HTML and text pages only
- No PDF, audio/video transcription, or image OCR yet
- Pages requiring authentication, CAPTCHA, or heavy client-side rendering may
  not be extractable
- FanTread does not bypass paywalls or access controls
- Extraction quality depends on the structure of the source page

## Development

Install the development dependencies:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run the test suite:

```bash
pytest
npm test
```

Build and inspect the Python and npm packages:

```bash
python -m pip wheel . --no-deps --wheel-dir dist
npm pack --dry-run
```

The package exposes two equivalent commands:

```text
fan
fantread
```

`fan` is the recommended user-facing command.

## Contributing

Issues and pull requests are welcome. Before opening a pull request:

1. Keep changes focused.
2. Add or update tests for behavior changes.
3. Run `pytest`.
4. Do not include API keys, fetched private content, or generated local
   configuration.

## License

FanTread is released under the [MIT License](LICENSE).
