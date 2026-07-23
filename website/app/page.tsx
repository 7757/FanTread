"use client";

import { useEffect, useState } from "react";

type Locale = "zh" | "en";

const INSTALL_COMMAND = "npm install -g fantread";

const copy = {
  zh: {
    nav: {
      features: "功能",
      experience: "体验",
      install: "安装",
      author: "作者",
    },
    github: "GitHub",
    eyebrow: "DeepSeek 驱动 · 开源 CLI · npm 即装即用",
    heroTitleA: "把网页，读成",
    heroTitleB: "你真正需要的内容。",
    heroBody:
      "给 FanTread 一个链接。它会提取正文、去除噪音、理解你的补充要求，再把内容整理成最合适的结构。",
    installNow: "复制安装命令",
    copied: "已复制",
    viewSource: "查看源码",
    heroMeta: "Node.js 18+ · Python 3.11+ · MIT",
    noteTitle: "不用记模式",
    noteBody: "只说你想要什么，FanTread 自己判断怎么整理。",
    terminalModel: "DeepSeek V4 Pro",
    terminalPrompt: "补充一句（可选）",
    terminalPromptValue: "尽量保留原文，只去掉噪音",
    terminalStatus: "已提取 10,914 字 · 已去噪 · 正在组织",
    terminalOutputTitle: "这篇文章真正讲了什么",
    terminalOutputBody:
      "核心观点被保留下来，广告、菜单、重复段落与无关引导已自动移除。",
    workflowKicker: "从链接到成文",
    workflowTitle: "三步，读完一篇网页。",
    workflowBody:
      "不需要先研究参数，也不用在六种模式里做选择。FanTread 会根据网页类型和你的那句话自动决定输出。",
    steps: [
      {
        number: "01",
        title: "抓到真正的正文",
        body: "识别普通网页、文章、帖子和微信公众号内容，尽可能保留原始结构。",
      },
      {
        number: "02",
        title: "理解你的意图",
        body: "你追加的评论、tips 或要求会进入模型提示词，而不是被机械贴在结果末尾。",
      },
      {
        number: "03",
        title: "自动组织成文",
        body: "该精简时精简，该保留时保留；文章、提纲或帖子格式由内容本身决定。",
      },
    ],
    experienceKicker: "更少操作，更快得到结果",
    experienceTitle: "你只需要做一件事：粘贴链接。",
    experienceBody:
      "首次运行会引导你选择 DeepSeek 模型并填写 Key。之后每次启动都是干净、直接的阅读流程。",
    promptLabel: "你的补充要求会参与理解",
    promptExample: "例如：帮我保留案例，最后给出三条可执行建议",
    promptFootnote: "它不会出现在结果末尾，只会影响模型如何提取和整理。",
    featuresKicker: "为真实阅读而做",
    featuresTitle: "该有的能力，一个不少。",
    features: [
      {
        mark: "TXT",
        title: "正文优先",
        body: "菜单、广告、推荐位、版权尾巴和重复内容会被自动清理。",
      },
      {
        mark: "AI",
        title: "自动判断表达方式",
        body: "无需记住 brief、outline 或 clean 等模式，模型会选择合适格式。",
      },
      {
        mark: "TIP",
        title: "一句话补充意图",
        body: "评论、提示和临时要求直接进入提示词，真正参与模型判断。",
      },
      {
        mark: "WX",
        title: "覆盖文章与帖子",
        body: "支持普通网页、微信公众号文章，以及常见的长文和帖子页面。",
      },
      {
        mark: "CLI",
        title: "键盘里的完整体验",
        body: "友好的终端引导、清晰进度和可直接复制保存的 Markdown 输出。",
      },
      {
        mark: "KEY",
        title: "自己的模型，自己的 Key",
        body: "在本机完成 DeepSeek 模型选择与 Key 配置，不写入开源仓库。",
      },
    ],
    installKicker: "一分钟开始",
    installTitle: "装好，然后输入 fan。",
    installBody:
      "全局安装后，在任何终端输入 fan 即可。第一次启动会自动准备项目私有运行环境。",
    copyCommand: "复制",
    installSteps: [
      ["1", "安装", "在终端运行上面的 npm 命令"],
      ["2", "启动", "输入 fan，跟随简短引导"],
      ["3", "阅读", "粘贴链接，也可以再补充一句要求"],
    ],
    requirements: "需要 Node.js 18+ 和 Python 3.11+",
    npmPackage: "在 npm 查看",
    authorKicker: "关于作者",
    authorRole: "FanTread 与 FastCut 作者",
    authorName: "musk",
    authorHandle: "@7757",
    authorBio: "热爱技术，也认真生活。持续分享，持续成长。",
    authorSource:
      "FanTread 是一个开放、克制的小工具：让信息少一点噪音，让阅读多一点掌控。",
    profile: "GitHub 主页",
    fastcut: "另一个开源项目 FastCut",
    ctaTitle: "下一篇长文，交给 fan。",
    ctaBody: "开源、轻量、没有模式负担。只留下你真正想读的内容。",
    footerTag: "DeepSeek 驱动的开源终端阅读器",
    license: "MIT 协议",
  },
  en: {
    nav: {
      features: "Features",
      experience: "Experience",
      install: "Install",
      author: "Author",
    },
    github: "GitHub",
    eyebrow: "DeepSeek-powered · Open-source CLI · One npm install",
    heroTitleA: "Turn any link into",
    heroTitleB: "what you actually need.",
    heroBody:
      "Give FanTread a link. It extracts the real content, removes the noise, understands your extra instruction, and shapes the result for you.",
    installNow: "Copy install command",
    copied: "Copied",
    viewSource: "View source",
    heroMeta: "Node.js 18+ · Python 3.11+ · MIT",
    noteTitle: "No modes to memorize",
    noteBody: "Say what you need. FanTread decides how the content should be shaped.",
    terminalModel: "DeepSeek V4 Pro",
    terminalPrompt: "Extra instruction (optional)",
    terminalPromptValue: "Keep the original voice. Remove only the noise.",
    terminalStatus: "10,914 characters extracted · noise removed · organizing",
    terminalOutputTitle: "What this article is really saying",
    terminalOutputBody:
      "The core argument stays intact while ads, navigation, repeated blocks, and unrelated prompts disappear.",
    workflowKicker: "From link to clarity",
    workflowTitle: "Three steps. One finished read.",
    workflowBody:
      "No parameter study and no menu of summary modes. FanTread decides from the page, the content, and the one sentence you add.",
    steps: [
      {
        number: "01",
        title: "Find the real article",
        body: "Recognize webpages, posts, articles, and WeChat content while preserving useful structure.",
      },
      {
        number: "02",
        title: "Understand your intent",
        body: "Your comment, tip, or request becomes part of the model prompt—not a note pasted onto the end.",
      },
      {
        number: "03",
        title: "Shape the right output",
        body: "Condense when useful, preserve when needed, and let the content choose its natural format.",
      },
    ],
    experienceKicker: "Less input. Better output.",
    experienceTitle: "Your only job is to paste the link.",
    experienceBody:
      "The first run guides you through choosing a DeepSeek model and adding your key. Every read after that stays focused.",
    promptLabel: "Your instruction changes the interpretation",
    promptExample:
      "Example: keep the examples and finish with three practical actions",
    promptFootnote:
      "It does not appear at the end of the result. It guides how the model extracts and organizes.",
    featuresKicker: "Built for real reading",
    featuresTitle: "The useful parts, all in one command.",
    features: [
      {
        mark: "TXT",
        title: "Content first",
        body: "Navigation, ads, recommendations, repeated blocks, and boilerplate are removed.",
      },
      {
        mark: "AI",
        title: "Automatic format judgment",
        body: "No brief, outline, or clean modes to remember. The model chooses the right shape.",
      },
      {
        mark: "TIP",
        title: "One-sentence direction",
        body: "Comments, tips, and temporary requests go straight into the model prompt.",
      },
      {
        mark: "WX",
        title: "Articles and posts",
        body: "Works with regular webpages, WeChat articles, long reads, and post-style pages.",
      },
      {
        mark: "CLI",
        title: "A complete terminal flow",
        body: "Friendly guidance, readable progress, and clean Markdown you can copy or save.",
      },
      {
        mark: "KEY",
        title: "Your model, your key",
        body: "Choose DeepSeek and configure your key locally. It never enters the open-source repo.",
      },
    ],
    installKicker: "Start in a minute",
    installTitle: "Install it. Then type fan.",
    installBody:
      "Install globally and run fan from any terminal. The first launch prepares a private runtime automatically.",
    copyCommand: "Copy",
    installSteps: [
      ["1", "Install", "Run the npm command above in your terminal"],
      ["2", "Launch", "Type fan and follow the short setup"],
      ["3", "Read", "Paste a link and optionally add one instruction"],
    ],
    requirements: "Requires Node.js 18+ and Python 3.11+",
    npmPackage: "View on npm",
    authorKicker: "About the author",
    authorRole: "Creator of FanTread and FastCut",
    authorName: "musk",
    authorHandle: "@7757",
    authorBio:
      "Passionate about tech, obsessed with life. Always sharing, always growing.",
    authorSource:
      "FanTread is intentionally open and focused: less noise in the information, more control in the reading.",
    profile: "GitHub profile",
    fastcut: "Another open-source project: FastCut",
    ctaTitle: "Give your next long read to fan.",
    ctaBody:
      "Open-source, lightweight, and free from mode fatigue. Keep only what is worth reading.",
    footerTag: "An open-source terminal reader powered by DeepSeek",
    license: "MIT License",
  },
} as const;

export default function Home() {
  const [locale, setLocale] = useState<Locale>("zh");
  const [copied, setCopied] = useState(false);
  const t = copy[locale];

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem("fantread-locale");
      if (saved === "zh" || saved === "en") {
        setLocale(saved);
        return;
      }
    } catch {
      // Local storage is optional.
    }

    if (!window.navigator.language.toLowerCase().startsWith("zh")) {
      setLocale("en");
    }
  }, []);

  const switchLocale = () => {
    const next = locale === "zh" ? "en" : "zh";
    setLocale(next);
    try {
      window.localStorage.setItem("fantread-locale", next);
    } catch {
      // Local storage is optional.
    }
  };

  const copyInstall = async () => {
    try {
      await window.navigator.clipboard.writeText(INSTALL_COMMAND);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  };

  return (
    <div className="site-shell">
      <header className="nav-shell">
        <nav className="top-nav" aria-label="Primary navigation">
          <a className="brand" href="#top" aria-label="FanTread home">
            <span className="brand-mark" aria-hidden="true">
              F_
            </span>
            <span>FanTread</span>
          </a>

          <div className="nav-links">
            <a href="#features">{t.nav.features}</a>
            <a href="#experience">{t.nav.experience}</a>
            <a href="#install">{t.nav.install}</a>
            <a href="#author">{t.nav.author}</a>
          </div>

          <div className="nav-actions">
            <button
              className="language-button"
              type="button"
              onClick={switchLocale}
              aria-label={locale === "zh" ? "Switch to English" : "切换到中文"}
            >
              {locale === "zh" ? "EN" : "中"}
            </button>
            <a
              className="nav-github"
              href="https://github.com/7757/FanTread"
              target="_blank"
              rel="noreferrer"
            >
              {t.github} <span aria-hidden="true">↗</span>
            </a>
          </div>
        </nav>
      </header>

      <main>
        <section className="hero section-wrap" id="top">
          <div className="hero-copy">
            <p className="eyebrow">
              <span className="eyebrow-dot" aria-hidden="true" />
              {t.eyebrow}
            </p>
            <h1>
              {t.heroTitleA}
              <br />
              <span className="highlight">{t.heroTitleB}</span>
            </h1>
            <p className="hero-body">{t.heroBody}</p>

            <div className="hero-actions">
              <button className="button button-primary" type="button" onClick={copyInstall}>
                <span className="button-command" aria-hidden="true">
                  $
                </span>
                {copied ? t.copied : t.installNow}
              </button>
              <a
                className="button button-secondary"
                href="https://github.com/7757/FanTread"
                target="_blank"
                rel="noreferrer"
              >
                {t.viewSource} <span aria-hidden="true">↗</span>
              </a>
            </div>

            <p className="hero-meta">{t.heroMeta}</p>
          </div>

          <div className="hero-visual">
            <div className="paper-note">
              <span className="paper-pin" aria-hidden="true" />
              <strong>{t.noteTitle}</strong>
              <p>{t.noteBody}</p>
            </div>

            <div className="terminal-window">
              <div className="terminal-bar">
                <div className="terminal-dots" aria-hidden="true">
                  <span />
                  <span />
                  <span />
                </div>
                <span className="terminal-title">fan · {t.terminalModel}</span>
                <span className="terminal-status-dot" aria-hidden="true" />
              </div>
              <div className="terminal-body">
                <div className="terminal-command">
                  <span className="terminal-arrow">➜</span>
                  <span className="terminal-cmd">fan</span>
                  <span className="terminal-url">
                    &quot;https://mp.weixin.qq.com/s/...&quot;
                  </span>
                </div>

                <div className="terminal-question">
                  <span>{t.terminalPrompt}</span>
                  <strong>› {t.terminalPromptValue}</strong>
                </div>

                <div className="terminal-progress">
                  <span className="progress-check" aria-hidden="true">
                    ✓
                  </span>
                  {t.terminalStatus}
                </div>

                <article className="terminal-output">
                  <div className="output-label">OUTPUT.md</div>
                  <h2>{t.terminalOutputTitle}</h2>
                  <p>{t.terminalOutputBody}</p>
                  <div className="output-lines" aria-hidden="true">
                    <span />
                    <span />
                    <span />
                  </div>
                </article>
              </div>
            </div>
          </div>
        </section>

        <section className="workflow section-wrap" aria-labelledby="workflow-title">
          <div className="section-heading">
            <p className="section-kicker">{t.workflowKicker}</p>
            <h2 id="workflow-title">{t.workflowTitle}</h2>
            <p>{t.workflowBody}</p>
          </div>

          <div className="step-grid">
            {t.steps.map((step) => (
              <article className="step-card" key={step.number}>
                <span className="step-number">{step.number}</span>
                <div>
                  <h3>{step.title}</h3>
                  <p>{step.body}</p>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="experience" id="experience">
          <div className="section-wrap experience-grid">
            <div className="experience-copy">
              <p className="section-kicker">{t.experienceKicker}</p>
              <h2>{t.experienceTitle}</h2>
              <p>{t.experienceBody}</p>

              <div className="prompt-card">
                <div className="prompt-card-top">
                  <span className="prompt-spark" aria-hidden="true">
                    ✦
                  </span>
                  <strong>{t.promptLabel}</strong>
                </div>
                <p>{t.promptExample}</p>
                <small>{t.promptFootnote}</small>
              </div>
            </div>

            <div className="flow-panel" aria-label="FanTread reading flow">
              <div className="flow-row">
                <span className="flow-index">01</span>
                <div>
                  <small>URL</small>
                  <strong>mp.weixin.qq.com/s/...</strong>
                </div>
                <span className="flow-state">READY</span>
              </div>
              <div className="flow-connector" aria-hidden="true">
                <span />
              </div>
              <div className="flow-row active">
                <span className="flow-index">02</span>
                <div>
                  <small>PROMPT</small>
                  <strong>{t.terminalPromptValue}</strong>
                </div>
                <span className="flow-state">ADDED</span>
              </div>
              <div className="flow-connector" aria-hidden="true">
                <span />
              </div>
              <div className="flow-row">
                <span className="flow-index">03</span>
                <div>
                  <small>RESULT</small>
                  <strong>article-clean.md</strong>
                </div>
                <span className="flow-state done">DONE</span>
              </div>
            </div>
          </div>
        </section>

        <section className="features section-wrap" id="features" aria-labelledby="features-title">
          <div className="section-heading compact">
            <p className="section-kicker">{t.featuresKicker}</p>
            <h2 id="features-title">{t.featuresTitle}</h2>
          </div>

          <div className="feature-grid">
            {t.features.map((feature) => (
              <article className="feature-card" key={feature.mark}>
                <span className="feature-mark">{feature.mark}</span>
                <h3>{feature.title}</h3>
                <p>{feature.body}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="install-section" id="install">
          <div className="section-wrap">
            <div className="install-panel">
              <div className="install-copy">
                <p className="section-kicker light">{t.installKicker}</p>
                <h2>{t.installTitle}</h2>
                <p>{t.installBody}</p>

                <div className="install-command">
                  <code>
                    <span>$</span> {INSTALL_COMMAND}
                  </code>
                  <button type="button" onClick={copyInstall}>
                    {copied ? t.copied : t.copyCommand}
                  </button>
                </div>

                <div className="install-links">
                  <span>{t.requirements}</span>
                  <a
                    href="https://www.npmjs.com/package/fantread"
                    target="_blank"
                    rel="noreferrer"
                  >
                    {t.npmPackage} ↗
                  </a>
                </div>
              </div>

              <div className="install-steps">
                {t.installSteps.map(([number, title, body]) => (
                  <div className="install-step" key={number}>
                    <span>{number}</span>
                    <div>
                      <strong>{title}</strong>
                      <p>{body}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="author section-wrap" id="author" aria-labelledby="author-name">
          <div className="author-card">
            <div className="author-avatar-wrap">
              <img
                className="author-avatar"
                src="https://avatars.githubusercontent.com/u/48285391?v=4"
                alt="musk on GitHub"
                width="160"
                height="160"
              />
              <span className="author-online" aria-hidden="true" />
            </div>

            <div className="author-copy">
              <p className="section-kicker">{t.authorKicker}</p>
              <p className="author-role">{t.authorRole}</p>
              <h2 id="author-name">
                {t.authorName} <span>{t.authorHandle}</span>
              </h2>
              <p className="author-bio">{t.authorBio}</p>
              <p className="author-note">{t.authorSource}</p>

              <div className="author-links">
                <a
                  className="button button-dark"
                  href="https://github.com/7757"
                  target="_blank"
                  rel="noreferrer"
                >
                  {t.profile} ↗
                </a>
                <a
                  className="text-link"
                  href="https://7757.github.io/FastCut/"
                  target="_blank"
                  rel="noreferrer"
                >
                  {t.fastcut} ↗
                </a>
              </div>
            </div>

            <div className="author-stamp" aria-hidden="true">
              <span>OPEN</span>
              <span>SOURCE</span>
              <strong>MIT</strong>
            </div>
          </div>
        </section>

        <section className="final-cta section-wrap">
          <div>
            <p className="section-kicker">{t.footerTag}</p>
            <h2>{t.ctaTitle}</h2>
            <p>{t.ctaBody}</p>
          </div>
          <button className="button button-primary" type="button" onClick={copyInstall}>
            <span className="button-command" aria-hidden="true">
              $
            </span>
            {copied ? t.copied : INSTALL_COMMAND}
          </button>
        </section>
      </main>

      <footer className="footer">
        <div className="section-wrap footer-inner">
          <a className="brand" href="#top" aria-label="FanTread home">
            <span className="brand-mark" aria-hidden="true">
              F_
            </span>
            <span>FanTread</span>
          </a>
          <p>{t.footerTag}</p>
          <div>
            <a href="https://github.com/7757" target="_blank" rel="noreferrer">
              © {new Date().getFullYear()} musk
            </a>
            <span>·</span>
            <a
              href="https://github.com/7757/FanTread/blob/main/LICENSE"
              target="_blank"
              rel="noreferrer"
            >
              {t.license}
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
