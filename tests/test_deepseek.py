import json

import httpx
import pytest

from fantread.deepseek import DeepSeekClient, DeepSeekError


def test_complete_uses_current_model_and_hides_thinking() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "# 总结\n内容"}}],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 4,
                    "total_tokens": 14,
                },
            },
        )

    client = DeepSeekClient(
        api_key="test-key",
        model="deepseek-v4-flash",
        transport=httpx.MockTransport(handler),
    )
    try:
        result = client.complete([{"role": "user", "content": "hello"}])
    finally:
        client.close()
    assert result.content == "# 总结\n内容"
    assert result.usage.total_tokens == 14
    assert captured["model"] == "deepseek-v4-flash"
    assert captured["thinking"] == {"type": "disabled"}


def test_stream_complete_collects_sse() -> None:
    body = "\n".join(
        [
            'data: {"choices":[{"delta":{"content":"你"}}]}',
            'data: {"choices":[{"delta":{"content":"好"}}]}',
            'data: {"choices":[],"usage":{"total_tokens":7}}',
            "data: [DONE]",
            "",
        ]
    )

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=body)

    pieces: list[str] = []
    client = DeepSeekClient(
        api_key="test-key",
        model="deepseek-v4-flash",
        transport=httpx.MockTransport(handler),
    )
    try:
        result = client.stream_complete(
            [{"role": "user", "content": "hello"}],
            on_delta=pieces.append,
        )
    finally:
        client.close()
    assert result.content == "你好"
    assert pieces == ["你", "好"]
    assert result.usage.total_tokens == 7


def test_stream_error_preserves_friendly_api_message() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            429,
            json={"error": {"message": "rate limit reached"}},
        )

    client = DeepSeekClient(
        api_key="test-key",
        model="deepseek-v4-flash",
        transport=httpx.MockTransport(handler),
    )
    try:
        with pytest.raises(DeepSeekError, match="请求过于频繁.*rate limit"):
            client.stream_complete(
                [{"role": "user", "content": "hello"}],
            )
    finally:
        client.close()


def test_stream_handles_error_events_inside_successful_response() -> None:
    body = "\n".join(
        [
            'data: {"error":{"message":"upstream interrupted"}}',
            "data: [DONE]",
            "",
        ]
    )

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            text=body,
        )

    client = DeepSeekClient(
        api_key="test-key",
        model="deepseek-v4-flash",
        transport=httpx.MockTransport(handler),
    )
    try:
        with pytest.raises(DeepSeekError, match="upstream interrupted"):
            client.stream_complete(
                [{"role": "user", "content": "hello"}],
            )
    finally:
        client.close()


def test_thinking_payload_omits_temperature() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "结果"}}]},
        )

    client = DeepSeekClient(
        api_key="test-key",
        model="deepseek-v4-pro",
        thinking=True,
        transport=httpx.MockTransport(handler),
    )
    try:
        client.complete([{"role": "user", "content": "hello"}])
    finally:
        client.close()

    assert captured["thinking"] == {"type": "enabled"}
    assert "temperature" not in captured


def test_validate_filters_invalid_model_entries() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": [
                    {"id": "deepseek-v4-flash"},
                    {"id": ""},
                    "invalid",
                    {"owned_by": "deepseek"},
                ]
            },
        )

    client = DeepSeekClient(
        api_key="test-key",
        model="deepseek-v4-flash",
        base_url="https://api.deepseek.com/",
        transport=httpx.MockTransport(handler),
    )
    try:
        assert client.validate() == ["deepseek-v4-flash"]
    finally:
        client.close()


@pytest.mark.parametrize(
    ("status", "message"),
    [
        (401, "API Key 无效"),
        (402, "余额不足"),
        (429, "请求过于频繁"),
        (500, "服务暂时异常"),
    ],
)
def test_http_errors_have_actionable_messages(status, message) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status,
            json={"error": {"message": "provider detail"}},
        )

    client = DeepSeekClient(
        api_key="test-key",
        model="deepseek-v4-flash",
        transport=httpx.MockTransport(handler),
    )
    try:
        with pytest.raises(DeepSeekError, match=message):
            client.complete([{"role": "user", "content": "hello"}])
    finally:
        client.close()


def test_timeout_has_a_short_user_facing_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    client = DeepSeekClient(
        api_key="test-key",
        model="deepseek-v4-flash",
        transport=httpx.MockTransport(handler),
    )
    try:
        with pytest.raises(DeepSeekError, match="响应超时"):
            client.complete([{"role": "user", "content": "hello"}])
    finally:
        client.close()
