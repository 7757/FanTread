# FanTread

[English](README.md) | [简体中文](README.zh-CN.md)

[![npm](https://img.shields.io/npm/v/fantread?color=18a999)](https://www.npmjs.com/package/fantread)
[![CI](https://github.com/7757/FanTread/actions/workflows/ci.yml/badge.svg)](https://github.com/7757/FanTread/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/7757/FanTread)](LICENSE)

贴一个链接，FanTread 会在本地提取正文、去除页面噪音，再使用 DeepSeek
按照最适合原内容的结构自动整理。

用户不需要记忆任何总结模式。FanTread 会判断页面是新闻、长文、教程、观点文章
还是讨论帖子，并自动选择合适的信息密度和排版。

> [!IMPORTANT]
> FanTread 目前处于 Alpha 阶段。为了方便测试首次使用流程，当前默认每次交互运行
> 都会开启一个全新会话。

## 主要功能

- 自动选择合适的内容结构和详略程度
- 针对微信公众号文章进行定向提取和降噪
- 使用 Trafilatura 和 Beautiful Soup 提取通用网页正文
- 识别 Schema.org `DiscussionForumPosting` 和 `SocialMediaPosting`
- 支持追加一句自然语言要求，控制侧重点、语气、详略或排版
- 支持 DeepSeek V4 Flash、V4 Pro 和自定义模型 ID
- 使用 Rich 提供友好的终端界面和流式输出
- 支持终端、Markdown、纯文本和 JSON 四种输出
- 自动分片处理超长正文，再合并中间结果
- 将网页正文视为不可信来源数据，而不是模型指令

## 工作流程

```text
网页链接
 └─> 在本地抓取并提取正文
      └─> 去除导航、广告、引导关注和重复噪音
           └─> 将清理后的正文和用户补充要求发送给 DeepSeek
                └─> 自动组织并渲染结果
```

用户追加的要求会成为模型提示词的一部分，用于影响生成结果，但不会被追加到文章
末尾，也不会作为独立评论写入导出文件。

## 环境要求

- 通过 npm 安装时需要 Node.js 18 或更新版本
- Python 3.11 或更新版本
- 一个 [DeepSeek API Key](https://platform.deepseek.com/api_keys)
- 能够访问原网页和 DeepSeek API 的网络环境

## 安装

### npm

全局安装后直接运行 `fan`：

```bash
npm install -g fantread
fan
```

首次运行 `fan` 时，FanTread 会自动检测 Python 3.11 或更新版本，并在包内
建立独立运行环境，无需再手动执行 pip。如果支持的 Python 不在 `PATH` 中，
可以通过 `FANTREAD_PYTHON` 指定解释器路径。

也可以不保留全局安装，直接体验：

```bash
npx fantread
```

### 使用 pipx 从源码安装

克隆本仓库并进入项目目录，然后使用
[pipx](https://pipx.pypa.io/) 安装命令行工具：

```bash
pipx install .
fan --version
```

开发时建议使用可编辑虚拟环境：

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 发布到 PyPI 以后

FanTread 发布到 PyPI 后，用户可以通过以下任意一种方式全局安装：

```bash
pipx install fantread
```

```bash
uv tool install fantread
```

## 快速开始

启动交互向导：

```bash
fan
```

向导会依次询问：

```text
网页链接
可选的补充要求
本次使用的 DeepSeek 模型
本次使用的临时 API Key（遮罩显示且不会保存）
```

也可以直接传入链接：

```bash
fan "https://mp.weixin.qq.com/s/Rqv-4yFGUTuLxMaRSt1XDg"
```

需要补充要求时，直接放在链接后面：

```bash
fan "https://example.com/article" \
  "尽量保留原文表达，只去除噪音并整理重点。"
```

```bash
fan "https://example.com/tutorial" \
  "重点告诉我具体步骤、前置条件和常见错误。"
```

FanTread 会自行判断结果应该精简、详细、按步骤排列，还是按照帖子讨论结构整理，
用户不需要选择模式。

## 输出

默认在终端中显示：

```bash
fan "https://example.com/article"
```

保存为 Markdown：

```bash
fan "https://example.com/article" --format md --output result.md
```

输出纯文本：

```bash
fan "https://example.com/article" --format text
```

输出可供程序读取的 JSON：

```bash
fan "https://example.com/article" --format json
```

支持的输出格式：

| 格式 | 内容 |
| --- | --- |
| `terminal` | Rich 元信息面板和 Markdown 渲染结果 |
| `markdown` / `md` | 带 YAML front matter 的 Markdown |
| `text` | 纯文本 |
| `json` | 来源信息、模型、Token 用量和生成内容 |

进度和错误信息写入 stderr；Markdown、纯文本和 JSON 写入 stdout，因此可以安全地
重定向或接入管道。

## 模型

FanTread 当前提供：

| 模型 | 适用场景 |
| --- | --- |
| `deepseek-v4-flash` | 更快、成本更低，适合日常阅读；默认选择 |
| `deepseek-v4-pro` | 质量优先，适合长文和复杂材料 |
| 自定义模型 ID | 兼容 DeepSeek 后续发布的模型 |

使用 `--thinking` 开启 DeepSeek 深度思考：

```bash
fan "https://example.com/complex-article" --thinking
```

查看内置模型：

```bash
fan models
```

当前可用模型和价格请以
[DeepSeek 官方文档](https://api-docs.deepseek.com/quick_start/pricing/)为准。

## 全新运行开发模式

FanTread 在开发阶段默认开启全新运行模式。每次交互运行都会：

- 忽略已保存的 FanTread 配置
- 忽略系统密钥环中保存的 Key
- 重新选择模型
- 重新输入经过遮罩的临时 API Key
- 只在当前进程内存中保留 Key

进行非交互自动化测试时，可以只为当前环境提供 Key：

```bash
export DEEPSEEK_API_KEY="你的 Key"
fan "https://example.com/article" --format json
```

正常交互运行仍会重新询问 Key，即使环境变量已经存在。

以后进入生产阶段，可以开启持久配置：

```bash
export FANTREAD_FRESH=0
fan setup
```

`fan setup` 会引导用户选择默认模型，并允许用户将 API Key 保存到操作系统密钥环。
Key 永远不会写入 FanTread 的 JSON 配置文件。

## 隐私与安全

FanTread 会在本地下载并清理页面，再将清理后的正文和用户补充要求发送给
DeepSeek 生成结果。

- API Key 输入经过遮罩
- 全新交互会话不会持久保存 Key
- 持久模式只在用户同意后使用操作系统密钥环
- Key 不会写入项目文件或导出结果
- 网页正文会在提示词中被明确标记为来源材料，以降低提示词注入风险

不要提交真实 API Key。如果 Key 曾经出现在 Issue、聊天记录、终端录像或公开日志
中，请立即撤销并重新创建。

## 当前限制

- 目前只处理 HTML 和文本网页
- 暂不支持 PDF、音视频转录和图片 OCR
- 需要登录、验证码或强 JavaScript 渲染的页面可能无法提取
- 不会绕过付费墙或其他访问控制
- 提取质量会受到原网页结构影响

## 开发

安装开发依赖：

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

运行测试：

```bash
pytest
npm test
```

构建并检查 Python 与 npm 安装包：

```bash
python -m pip wheel . --no-deps --wheel-dir dist
npm pack --dry-run
```

项目会安装两个等价命令：

```text
fan
fantread
```

推荐用户使用更短的 `fan`。

## 参与贡献

欢迎提交 Issue 和 Pull Request。提交 PR 前请：

1. 保持改动范围清晰。
2. 为行为变化添加或更新测试。
3. 运行 `pytest`。
4. 不要提交 API Key、抓取到的私密内容或本地生成的配置。

## 许可证

FanTread 使用 [MIT License](LICENSE) 开源。
