import pytest

from fantread.cleaner import normalize_text, remove_noise, split_text


def test_remove_noise_trims_tail_recommendations_without_rewriting_body() -> None:
    text = "\n\n".join(
        [
            "标题",
            "第一段有关键数字 42。",
            "第二段保留作者原话。",
            "第三段。",
            "第四段。",
            "第五段。",
            "第六段。",
            "推荐阅读",
            "另一篇文章",
            "一键关注,明天见 看完点个赞",
        ]
    )
    cleaned = remove_noise(text)
    assert "第一段有关键数字 42。" in cleaned
    assert "第二段保留作者原话。" in cleaned
    assert "推荐阅读" not in cleaned
    assert "另一篇文章" not in cleaned


def test_normalize_text_collapses_layout_only() -> None:
    assert normalize_text(" A \r\n\r\n\r\n B\t C ") == "A\n\nB C"


def test_split_text_preserves_all_content_order() -> None:
    text = "\n\n".join(f"段落{i}。" + "内容" * 20 for i in range(12))
    chunks = split_text(text, target_chars=100)
    assert len(chunks) > 1
    rebuilt = "".join(chunks)
    assert rebuilt == normalize_text(text)
    assert all(len(chunk) <= 100 for chunk in chunks)


def test_split_text_rejects_non_positive_target() -> None:
    with pytest.raises(ValueError, match="大于 0"):
        split_text("正文", target_chars=0)


def test_noise_removal_is_idempotent_and_keeps_early_real_heading() -> None:
    text = "\n\n".join(
        [
            "标题",
            "推荐阅读",
            "这里是在正文前部讨论推荐系统，不是尾部导航。",
            "正文信息。" * 20,
            "推荐阅读",
            "另一篇广告文章",
        ]
    )
    cleaned = remove_noise(text)

    assert "这里是在正文前部讨论推荐系统" in cleaned
    assert cleaned == remove_noise(cleaned)
    assert "另一篇广告文章" not in cleaned


def test_split_text_preserves_single_newlines_and_long_paragraph_layout() -> None:
    text = (
        "第一步：安装依赖。\n"
        "npm install package\n"
        "第二步：运行命令。\n"
        "npm run start\n" + "没有标点的连续内容" * 40
    )
    normalized = normalize_text(text)
    chunks = split_text(text, target_chars=80)

    assert len(chunks) > 1
    assert "".join(chunks) == normalized
    assert all(0 < len(chunk) <= 80 for chunk in chunks)
