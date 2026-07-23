from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any
from urllib.parse import urlparse

import httpx
import trafilatura
from bs4 import BeautifulSoup, Tag

from fantread import __version__
from fantread.cleaner import normalize_text
from fantread.models import Article


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    f"Chrome/131.0 Safari/537.36 FanTread/{__version__}"
)
MAX_DOWNLOAD_BYTES = 12 * 1024 * 1024
MIN_CONTENT_CHARS = 120

REMOVE_SELECTORS = (
    "script",
    "style",
    "noscript",
    "svg",
    "canvas",
    "iframe",
    "form",
    "button",
    "nav",
    "footer",
    "aside",
    "[aria-hidden='true']",
    ".advertisement",
    ".ads",
    ".ad",
    ".share",
    ".social-share",
    ".related",
    ".recommend",
    ".rich_media_tool",
    ".rich_media_extra",
    ".qr_code_pc",
    "#js_pc_qr_code",
    "#js_tags",
    "#js_toobar3",
)


class ExtractionError(RuntimeError):
    pass


class ArticleExtractor:
    def __init__(
        self,
        *,
        timeout: float = 25.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.timeout = timeout
        self._transport = transport

    def fetch_and_extract(self, url: str) -> Article:
        normalized_url = self.normalize_url(url)
        try:
            with httpx.Client(
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.5",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.7",
                },
                follow_redirects=True,
                timeout=httpx.Timeout(self.timeout),
                transport=self._transport,
                http2=self._transport is None,
            ) as client:
                with client.stream("GET", normalized_url) as response:
                    response.raise_for_status()
                    content_type = response.headers.get("content-type", "").lower()
                    if content_type and not any(
                        kind in content_type
                        for kind in ("html", "text/", "xhtml", "xml")
                    ):
                        raise ExtractionError(
                            f"暂不支持这种内容类型：{content_type.split(';', 1)[0]}"
                        )
                    body = bytearray()
                    for chunk in response.iter_bytes():
                        body.extend(chunk)
                        if len(body) > MAX_DOWNLOAD_BYTES:
                            raise ExtractionError("页面超过 12 MB，已停止下载")
                    final_url = str(response.url)
                    encoding = response.encoding or "utf-8"
        except ExtractionError:
            raise
        except httpx.TimeoutException as exc:
            raise ExtractionError("读取页面超时，请稍后重试或增大 --timeout") from exc
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            raise ExtractionError(f"页面返回 HTTP {status}") from exc
        except httpx.HTTPError as exc:
            raise ExtractionError(f"无法连接页面：{exc}") from exc

        try:
            html = bytes(body).decode(encoding, errors="replace")
        except LookupError:
            html = bytes(body).decode("utf-8", errors="replace")
        return self.extract_html(html, url=normalized_url, final_url=final_url)

    def extract_html(
        self,
        html: str,
        *,
        url: str,
        final_url: str | None = None,
    ) -> Article:
        final_url = final_url or url
        soup = BeautifulSoup(html, "html.parser")
        host = (urlparse(final_url).hostname or "").lower()
        metadata = self._metadata(soup)

        text = ""
        method = "generic"
        structured = self._structured_post(soup)
        if host.endswith("mp.weixin.qq.com"):
            container = soup.select_one("#js_content, .rich_media_content")
            if container:
                text = self._element_text(container)
                method = "wechat"
        elif structured and structured.get("text"):
            text = str(structured["text"])
            method = "structured-post"
            for key in ("title", "author", "published_at"):
                if structured.get(key):
                    metadata[key] = structured[key]

        text = normalize_text(text)
        if len(text) < MIN_CONTENT_CHARS:
            text = ""

        if not text:
            extracted = trafilatura.extract(
                html,
                url=final_url,
                output_format="txt",
                include_comments=method == "structured-post",
                include_links=False,
                include_images=False,
                favor_precision=True,
                deduplicate=True,
            )
            candidate = normalize_text(extracted or "")
            if len(candidate) >= MIN_CONTENT_CHARS:
                text = candidate
                method = "trafilatura"

        if not text:
            containers = soup.select(
                "[itemprop='articleBody'], article, main, "
                ".post-content, .entry-content, .article-content, "
                ".content, [role='main']"
            )
            if containers:
                container = max(
                    containers,
                    key=lambda node: len(node.get_text(" ", strip=True)),
                )
                candidate = self._element_text(container)
                if len(candidate) >= MIN_CONTENT_CHARS:
                    text = candidate
                    method = "dom-fallback"

        if not text:
            container = soup.body or soup
            candidate = self._element_text(container)
            if len(candidate) >= MIN_CONTENT_CHARS:
                text = candidate
                method = "body-fallback"

        text = normalize_text(text)

        if self._looks_blocked(soup, text):
            raise ExtractionError("页面要求验证、登录或启用浏览器，当前无法取得正文")
        if len(text) < MIN_CONTENT_CHARS:
            raise ExtractionError(
                "没有识别到足够的正文；页面可能依赖 JavaScript、登录或反爬验证"
            )

        title = normalize_text(str(metadata.get("title") or "")) or "未命名页面"
        return Article(
            url=url,
            final_url=final_url,
            title=title,
            text=text,
            author=self._optional(metadata.get("author")),
            published_at=self._optional(metadata.get("published_at")),
            site_name=self._optional(metadata.get("site_name")),
            extraction_method=method,
        )

    @staticmethod
    def normalize_url(url: str) -> str:
        value = url.strip()
        if not value:
            raise ExtractionError("链接不能为空")
        if "://" not in value:
            value = f"https://{value}"
        try:
            parsed = urlparse(value)
            hostname = parsed.hostname
            parsed.port
        except ValueError as exc:
            raise ExtractionError("请输入有效的 http(s) 链接") from exc
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or not hostname:
            raise ExtractionError("请输入有效的 http(s) 链接")
        if parsed.username or parsed.password:
            raise ExtractionError("链接中不能包含账号或密码")
        return value

    @staticmethod
    def _element_text(element: Tag) -> str:
        # Work on a detached copy so metadata extraction remains unaffected.
        clone = BeautifulSoup(str(element), "html.parser")
        for selector in REMOVE_SELECTORS:
            for node in clone.select(selector):
                node.decompose()
        return normalize_text(clone.get_text("\n", strip=True))

    @staticmethod
    def _meta(soup: BeautifulSoup, *selectors: str) -> str | None:
        for selector in selectors:
            node = soup.select_one(selector)
            if not node:
                continue
            value = (
                node.get("content")
                if node.name == "meta"
                else node.get_text(" ", strip=True)
            )
            if value:
                return str(value).strip()
        return None

    def _metadata(self, soup: BeautifulSoup) -> dict[str, str | None]:
        title = self._meta(
            soup,
            "#activity-name",
            "meta[property='og:title']",
            "meta[name='twitter:title']",
            "h1",
            "title",
        )
        author = self._meta(
            soup,
            "#js_name",
            "meta[name='author']",
            "meta[property='article:author']",
            "[rel='author']",
        )
        published_at = self._meta(
            soup,
            "#publish_time",
            "meta[property='article:published_time']",
            "meta[name='publishdate']",
            "meta[name='date']",
            "time[datetime]",
        )
        time_node = soup.select_one("time[datetime]")
        if time_node and time_node.get("datetime"):
            published_at = str(time_node["datetime"])
        site_name = self._meta(
            soup,
            "meta[property='og:site_name']",
            "meta[name='application-name']",
        )
        return {
            "title": title,
            "author": author,
            "published_at": published_at,
            "site_name": site_name,
        }

    def _structured_post(self, soup: BeautifulSoup) -> dict[str, str] | None:
        for node in soup.select("script[type='application/ld+json']"):
            raw = node.string or node.get_text()
            if not raw.strip():
                continue
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                continue
            for item in self._walk_json_ld(payload):
                type_value = item.get("@type", "")
                types = (
                    {str(value) for value in type_value}
                    if isinstance(type_value, list)
                    else {str(type_value)}
                )
                if not types.intersection(
                    {
                        "DiscussionForumPosting",
                        "SocialMediaPosting",
                        "BlogPosting",
                        "Article",
                        "NewsArticle",
                    }
                ):
                    continue
                body = item.get("articleBody") or item.get("text")
                if not isinstance(body, str) or len(body.strip()) < 20:
                    continue
                parts = [normalize_text(body)]
                comments = item.get("comment", [])
                if isinstance(comments, dict):
                    comments = [comments]
                if isinstance(comments, list) and comments:
                    rendered_comments: list[str] = []
                    for comment in comments:
                        if not isinstance(comment, dict):
                            continue
                        comment_text = comment.get("text")
                        if (
                            not isinstance(comment_text, str)
                            or not comment_text.strip()
                        ):
                            continue
                        author = self._author_name(comment.get("author")) or "匿名"
                        rendered_comments.append(
                            f"### {author}\n{normalize_text(comment_text)}"
                        )
                    if rendered_comments:
                        parts.extend(["## 评论", "\n\n".join(rendered_comments)])
                return {
                    "title": str(item.get("headline") or item.get("name") or ""),
                    "author": self._author_name(item.get("author")) or "",
                    "published_at": str(item.get("datePublished") or ""),
                    "text": "\n\n".join(parts),
                }
        return None

    @staticmethod
    def _walk_json_ld(payload: Any) -> Iterable[dict[str, Any]]:
        if isinstance(payload, dict):
            yield payload
            graph = payload.get("@graph")
            if isinstance(graph, (dict, list)):
                yield from ArticleExtractor._walk_json_ld(graph)
        elif isinstance(payload, list):
            for item in payload:
                yield from ArticleExtractor._walk_json_ld(item)

    @staticmethod
    def _author_name(author: Any) -> str | None:
        if isinstance(author, str):
            return author.strip()
        if isinstance(author, dict):
            value = author.get("name")
            return str(value).strip() if value else None
        if isinstance(author, list):
            names = [ArticleExtractor._author_name(item) for item in author]
            return "、".join(name for name in names if name) or None
        return None

    @staticmethod
    def _looks_blocked(soup: BeautifulSoup, text: str) -> bool:
        if len(text) >= 800:
            return False
        body_text = normalize_text(soup.get_text("\n", strip=True))
        indicators = (
            "环境异常",
            "访问过于频繁",
            "请完成验证",
            "登录后查看",
            "enable javascript",
            "checking your browser",
        )
        sample = f"{body_text[:1000]}\n{text[:1000]}".lower()
        return any(indicator.lower() in sample for indicator in indicators)

    @staticmethod
    def _optional(value: Any) -> str | None:
        if value is None:
            return None
        normalized = normalize_text(str(value))
        return normalized or None
