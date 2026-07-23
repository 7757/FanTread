from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class OutputFormat(str, Enum):
    TERMINAL = "terminal"
    MARKDOWN = "markdown"
    TEXT = "text"
    JSON = "json"


@dataclass(frozen=True, slots=True)
class ModelInfo:
    id: str
    label: str
    description: str


MODEL_CATALOG: tuple[ModelInfo, ...] = (
    ModelInfo(
        id="deepseek-v4-flash",
        label="快速",
        description="速度更快、成本更低，适合日常摘要（推荐）",
    ),
    ModelInfo(
        id="deepseek-v4-pro",
        label="高质量",
        description="质量优先，适合长文与复杂结构整理",
    ),
)

MODEL_IDS = {item.id for item in MODEL_CATALOG}


@dataclass(slots=True)
class Article:
    url: str
    final_url: str
    title: str
    text: str
    author: str | None = None
    published_at: str | None = None
    site_name: str | None = None
    extraction_method: str = "generic"

    @property
    def char_count(self) -> int:
        return len(self.text)

    def metadata(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "final_url": self.final_url,
            "author": self.author,
            "published_at": self.published_at,
            "site_name": self.site_name,
            "extraction_method": self.extraction_method,
            "char_count": self.char_count,
        }


@dataclass(slots=True)
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def add(self, other: TokenUsage) -> None:
        self.prompt_tokens += other.prompt_tokens
        self.completion_tokens += other.completion_tokens
        self.total_tokens += other.total_tokens

    @classmethod
    def from_api(cls, value: dict[str, Any] | None) -> TokenUsage:
        value = value or {}
        return cls(
            prompt_tokens=int(value.get("prompt_tokens", 0) or 0),
            completion_tokens=int(value.get("completion_tokens", 0) or 0),
            total_tokens=int(value.get("total_tokens", 0) or 0),
        )


@dataclass(slots=True)
class ReadResult:
    article: Article
    content: str
    model: str | None = None
    thinking: bool = False
    usage: TokenUsage = field(default_factory=TokenUsage)

    def as_dict(self) -> dict[str, Any]:
        return {
            **self.article.metadata(),
            "model": self.model,
            "thinking": self.thinking if self.model else None,
            "usage": asdict(self.usage) if self.model else None,
            "content": self.content,
        }
