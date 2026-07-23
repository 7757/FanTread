from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import httpx

from fantread import __version__
from fantread.models import TokenUsage


class DeepSeekError(RuntimeError):
    pass


@dataclass(slots=True)
class Completion:
    content: str
    usage: TokenUsage


class DeepSeekClient:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str = "https://api.deepseek.com",
        thinking: bool = False,
        timeout: float = 180.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not api_key.strip():
            raise DeepSeekError("API Key 不能为空")
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.thinking = thinking
        self._client = httpx.Client(
            headers={
                "Authorization": f"Bearer {api_key.strip()}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": f"FanTread/{__version__}",
            },
            timeout=httpx.Timeout(timeout),
            transport=transport,
            http2=transport is None,
        )

    def __enter__(self) -> DeepSeekClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def validate(self) -> list[str]:
        try:
            response = self._client.get(f"{self.base_url}/models")
            self._raise_for_status(response)
            data = response.json()
        except httpx.HTTPError as exc:
            raise DeepSeekError(f"连接 DeepSeek 失败：{exc}") from exc
        except (ValueError, TypeError) as exc:
            raise DeepSeekError("DeepSeek 返回了无法解析的响应") from exc
        return [
            str(item["id"])
            for item in data.get("data", [])
            if isinstance(item, dict) and item.get("id")
        ]

    def complete(
        self,
        messages: Sequence[dict[str, str]],
        *,
        max_tokens: int = 6_000,
    ) -> Completion:
        payload = self._payload(messages, stream=False, max_tokens=max_tokens)
        try:
            response = self._client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
            )
            self._raise_for_status(response)
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except DeepSeekError:
            raise
        except httpx.TimeoutException as exc:
            raise DeepSeekError("DeepSeek 响应超时，请稍后重试") from exc
        except httpx.HTTPError as exc:
            raise DeepSeekError(f"连接 DeepSeek 失败：{exc}") from exc
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise DeepSeekError("DeepSeek 返回了无法解析的响应") from exc
        if not isinstance(content, str) or not content.strip():
            raise DeepSeekError("DeepSeek 返回了空内容")
        return Completion(
            content=content.strip(),
            usage=TokenUsage.from_api(data.get("usage")),
        )

    def stream_complete(
        self,
        messages: Sequence[dict[str, str]],
        *,
        on_delta: Callable[[str], None] | None = None,
        max_tokens: int = 6_000,
    ) -> Completion:
        payload = self._payload(messages, stream=True, max_tokens=max_tokens)
        pieces: list[str] = []
        usage = TokenUsage()
        try:
            with self._client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload,
            ) as response:
                if not response.is_success:
                    response.read()
                self._raise_for_status(response)
                for line in response.iter_lines():
                    if not line.startswith("data:"):
                        continue
                    value = line[5:].strip()
                    if not value or value == "[DONE]":
                        continue
                    try:
                        event = json.loads(value)
                    except json.JSONDecodeError:
                        continue
                    api_error = event.get("error")
                    if api_error:
                        if isinstance(api_error, dict):
                            detail = api_error.get("message") or api_error.get("code")
                        else:
                            detail = api_error
                        safe_detail = str(detail or "未知错误").replace("\n", " ")[:240]
                        raise DeepSeekError(f"DeepSeek 流式响应错误：{safe_detail}")
                    if event.get("usage"):
                        usage = TokenUsage.from_api(event["usage"])
                    choices = event.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    content = delta.get("content")
                    if isinstance(content, str) and content:
                        pieces.append(content)
                        if on_delta:
                            on_delta(content)
        except DeepSeekError:
            raise
        except httpx.TimeoutException as exc:
            raise DeepSeekError("DeepSeek 流式响应超时，请稍后重试") from exc
        except httpx.HTTPError as exc:
            raise DeepSeekError(f"连接 DeepSeek 失败：{exc}") from exc
        content = "".join(pieces).strip()
        if not content:
            raise DeepSeekError("DeepSeek 返回了空内容")
        return Completion(content=content, usage=usage)

    def _payload(
        self,
        messages: Sequence[dict[str, str]],
        *,
        stream: bool,
        max_tokens: int,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": list(messages),
            "stream": stream,
            "max_tokens": max_tokens,
            "thinking": {"type": "enabled" if self.thinking else "disabled"},
        }
        if not self.thinking:
            payload["temperature"] = 0.2
        if stream:
            payload["stream_options"] = {"include_usage": True}
        return payload

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        if response.is_success:
            return
        status = response.status_code
        if status == 401:
            message = "API Key 无效或已失效"
        elif status == 402:
            message = "账户余额不足"
        elif status == 429:
            message = "请求过于频繁，请稍后重试"
        elif status >= 500:
            message = f"DeepSeek 服务暂时异常（HTTP {status}）"
        else:
            message = f"DeepSeek 请求失败（HTTP {status}）"
        try:
            api_message = response.json().get("error", {}).get("message")
        except (ValueError, AttributeError):
            api_message = None
        if api_message and status not in {401}:
            safe_message = str(api_message).replace("\n", " ")[:240]
            message = f"{message}：{safe_message}"
        raise DeepSeekError(message)
