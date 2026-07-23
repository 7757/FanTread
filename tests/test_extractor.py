import json

import httpx
import pytest

from fantread.extractor import ArticleExtractor, ExtractionError


def test_extracts_wechat_article_and_metadata() -> None:
    html = """
    <html>
      <head>
        <meta property="og:site_name" content="微信公众平台">
      </head>
      <body>
        <h1 id="activity-name"> 一篇长文章 </h1>
        <span id="js_name"> 示例作者 </span>
        <div id="js_content">
          <p>第一段正文，包含一个重要事实。</p>
          <p>第二段正文，长度足够用于内容识别。</p>
          <p>第三段继续解释事情的来龙去脉，确保这是有效正文而不是导航。</p>
          <p>第四段提供结论以及一些必要细节，正文总长度应超过最小阈值，并继续补充更多可靠的上下文信息。</p>
          <p>第五段再次补充完整信息，确保真实的短文章不会被误判为空页面，也不会把导航文字当作主要正文。</p>
          <div class="rich_media_tool">点赞 分享</div>
        </div>
      </body>
    </html>
    """
    article = ArticleExtractor().extract_html(
        html,
        url="https://mp.weixin.qq.com/s/example",
    )
    assert article.title == "一篇长文章"
    assert article.author == "示例作者"
    assert article.extraction_method == "wechat"
    assert "第一段正文" in article.text
    assert "点赞 分享" not in article.text


def test_extracts_structured_forum_post_with_comments() -> None:
    payload = {
        "@context": "https://schema.org",
        "@type": "DiscussionForumPosting",
        "headline": "一个帖子",
        "author": {"name": "楼主"},
        "datePublished": "2026-01-02",
        "articleBody": "这是帖子正文。" * 20,
        "comment": [{"author": {"name": "读者甲"}, "text": "这是一条有内容的回复。"}],
    }
    html = (
        "<html><body><script type='application/ld+json'>"
        + json.dumps(payload, ensure_ascii=False)
        + "</script></body></html>"
    )
    article = ArticleExtractor().extract_html(
        html,
        url="https://forum.example/posts/1",
    )
    assert article.extraction_method == "structured-post"
    assert article.title == "一个帖子"
    assert article.author == "楼主"
    assert "## 评论" in article.text
    assert "读者甲" in article.text


def test_rejects_too_little_content() -> None:
    with pytest.raises(ExtractionError, match="没有识别到足够"):
        ArticleExtractor().extract_html(
            "<html><title>空页</title><body>只有几个字</body></html>",
            url="https://example.com/empty",
        )


def test_normalizes_and_validates_web_urls() -> None:
    assert (
        ArticleExtractor.normalize_url(" example.com/article ")
        == "https://example.com/article"
    )
    with pytest.raises(ExtractionError, match="http"):
        ArticleExtractor.normalize_url("ftp://example.com/file")
    with pytest.raises(ExtractionError, match="账号或密码"):
        ArticleExtractor.normalize_url("https://user:secret@example.com")
    with pytest.raises(ExtractionError, match="有效"):
        ArticleExtractor.normalize_url("https://broken[host/path")


def test_uses_clean_body_fallback_for_loose_static_pages(monkeypatch) -> None:
    monkeypatch.setattr(
        "fantread.extractor.trafilatura.extract",
        lambda *args, **kwargs: "过短",
    )
    html = f"""
    <html>
      <head><title>普通静态页面</title></head>
      <body>
        <nav>首页 产品 登录</nav>
        <div class="page-shell">
          <p>{"这是没有 article 或 main 标签的有效正文。" * 20}</p>
        </div>
        <footer>版权和站点导航</footer>
      </body>
    </html>
    """
    article = ArticleExtractor().extract_html(
        html,
        url="https://example.com/loose-page",
    )

    assert article.extraction_method == "body-fallback"
    assert "有效正文" in article.text
    assert "首页 产品 登录" not in article.text
    assert "版权和站点导航" not in article.text


def test_fetches_plain_text_pages() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/plain; charset=utf-8"},
            text="纯文本页面中的有效内容和完整信息。\n" * 20,
        )

    article = ArticleExtractor(
        transport=httpx.MockTransport(handler),
    ).fetch_and_extract("https://example.com/notes.txt")

    assert article.extraction_method == "body-fallback"
    assert "纯文本页面" in article.text


def test_rejects_pdf_with_a_clear_content_type_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "application/pdf"},
            content=b"%PDF-1.7",
        )

    with pytest.raises(ExtractionError, match="application/pdf"):
        ArticleExtractor(
            transport=httpx.MockTransport(handler),
        ).fetch_and_extract("https://example.com/report.pdf")


def test_rejects_javascript_only_shells() -> None:
    html = """
    <html>
      <head><title>客户端应用</title></head>
      <body><div id="app"></div><script>renderArticle()</script></body>
    </html>
    """
    with pytest.raises(ExtractionError, match="JavaScript"):
        ArticleExtractor().extract_html(
            html,
            url="https://example.com/app",
        )


def test_download_limit_stops_large_pages(monkeypatch) -> None:
    monkeypatch.setattr("fantread.extractor.MAX_DOWNLOAD_BYTES", 64)

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/plain"},
            content=b"x" * 65,
        )

    with pytest.raises(ExtractionError, match="超过"):
        ArticleExtractor(
            transport=httpx.MockTransport(handler),
        ).fetch_and_extract("https://example.com/large")


def test_follows_redirect_and_records_final_url() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/start":
            return httpx.Response(302, headers={"location": "/article"})
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            text=(
                "<html><head><title>跳转后的文章</title></head>"
                "<body><article>"
                + "跳转后取得的有效正文。" * 20
                + "</article></body></html>"
            ),
        )

    article = ArticleExtractor(
        transport=httpx.MockTransport(handler),
    ).fetch_and_extract("https://example.com/start")

    assert article.final_url == "https://example.com/article"
    assert article.title == "跳转后的文章"


def test_uses_longest_matching_dom_container(monkeypatch) -> None:
    monkeypatch.setattr(
        "fantread.extractor.trafilatura.extract",
        lambda *args, **kwargs: None,
    )
    html = (
        "<html><head><title>多个正文容器</title></head><body>"
        "<article>很短</article>"
        "<main>"
        + "真正的完整正文，应该选择这个更长的容器。" * 20
        + "</main></body></html>"
    )

    article = ArticleExtractor().extract_html(
        html,
        url="https://example.com/containers",
    )

    assert article.extraction_method == "dom-fallback"
    assert "真正的完整正文" in article.text
    assert article.char_count > 200


def test_detects_blocked_verification_pages() -> None:
    html = """
    <html>
      <head><title>Checking your browser</title></head>
      <body>Please complete verification. Checking your browser.</body>
    </html>
    """

    with pytest.raises(ExtractionError, match="验证"):
        ArticleExtractor().extract_html(
            html,
            url="https://example.com/challenge",
        )


def test_reads_nested_schema_post_and_multiple_authors() -> None:
    payload = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebSite", "name": "论坛"},
            {
                "@type": ["Article", "DiscussionForumPosting"],
                "headline": "嵌套帖子",
                "author": [{"name": "作者甲"}, {"name": "作者乙"}],
                "articleBody": "嵌套结构中的帖子正文。" * 20,
            },
        ],
    }
    html = (
        "<script type='application/ld+json'>"
        + json.dumps(payload, ensure_ascii=False)
        + "</script>"
    )

    article = ArticleExtractor().extract_html(
        html,
        url="https://forum.example/nested",
    )

    assert article.extraction_method == "structured-post"
    assert article.author == "作者甲、作者乙"
    assert article.title == "嵌套帖子"
