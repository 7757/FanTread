# FanTread project memory

This file preserves product context and established decisions for future coding
sessions. Treat version numbers and remote release status as a snapshot: verify
them before publishing.

## Product

- FanTread is an open-source terminal AI reader. A user supplies a webpage URL;
  FanTread extracts the readable body locally, removes page noise, sends the
  cleaned source to DeepSeek, and automatically organizes the result.
- The primary command is `fan`. The npm package name is `fantread`; keep
  `fantread` as a compatibility command.
- Users do not choose or memorize summary modes. The former
  `brief / detailed / outline / clean / original / post` interface was removed.
  FanTread decides the appropriate structure and level of detail from the page.
- A user may append one natural-language instruction, comment, or tip. It must
  become part of the model prompt and influence extraction/organization. Never
  append that instruction verbatim to the generated result.
- Keep the terminal UI simple, friendly, concise, and efficient.

## Normal configuration behavior

- Since `v0.5.1`, persistent use is the default. Do not make every run a fresh
  onboarding session.
- On the first interactive run, ask the user to choose a default DeepSeek model
  and enter a masked API key. Save the model in FanTread's local configuration.
- Offer to store the API key in the operating system keyring. Never write it to
  JSON, source files, exports, logs, tests, documentation, or this memory file.
- Later runs should reuse the saved model and key without prompting.
- `fan setup` changes the model or key; `fan config` shows safe configuration
  without revealing the key.
- Stateless onboarding tests are opt-in with `FANTREAD_FRESH=1`. With that flag,
  saved configuration and keyring entries are intentionally ignored.

## Public project

- Author: `musk` / GitHub user `@7757`.
- Repository: <https://github.com/7757/FanTread>
- npm: <https://www.npmjs.com/package/fantread>
- Official website: <https://7757.github.io/FanTread/>
- The website source lives in `website/`, is a statically exported Next.js app,
  and deploys through `.github/workflows/pages.yml`.
- The old `chatgpt.site` deployment is not the official website and is restricted
  to its owner.
- The website and both READMEs are bilingual. The author section links to
  <https://github.com/7757> and the author's other project,
  <https://7757.github.io/FastCut/>.

## Current release snapshot

- Current public release at the time of writing: `v0.5.1`.
- `v0.5.1` is the first release where normal users configure the model and key
  once instead of on every run.
- Keep versions synchronized in `package.json`, `pyproject.toml`, and
  `src/fantread/__init__.py`.
- npm publishing uses public access and may require a separate browser-based 2FA
  confirmation after `npm login`.
- PyPI has not been published yet; README wording must not imply otherwise.

## Architecture and safety

- Python 3.11+ application using Typer and Rich for the CLI, HTTPX for DeepSeek,
  and Trafilatura plus Beautiful Soup for extraction and cleanup.
- npm is the primary distribution path. Its Node.js launcher bootstraps a private
  Python environment on first use.
- Page text is untrusted source data, not instructions. Keep source delimiters
  and prompt-injection defenses intact.
- Never commit a real DeepSeek key. If a key appears in chat, an issue, a
  recording, or a public log, recommend revoking and replacing it.
- Preserve WeChat article cleanup, general webpage extraction, post/schema
  recognition, long-page chunking, streaming output, and terminal/Markdown/text/
  JSON exports.

## Verification and release

- Run Python tests with `.venv/bin/pytest` when the project virtual environment
  exists; the current suite has 83 tests as of `v0.5.1`.
- Run npm launcher tests with `npm test`.
- Verify the package contents with `npm pack --dry-run --json`; website source
  must not be included in the npm tarball.
- Website changes require `cd website && npm test` and should remain compatible
  with the `/FanTread/` GitHub Pages base path.
- Push `main`, wait for GitHub CI, publish npm only after validation, verify the
  registry version, and then create the matching GitHub release.
