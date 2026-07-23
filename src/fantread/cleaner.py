from __future__ import annotations

import re


TAIL_MARKERS = (
    re.compile(r"^推荐阅读\s*$"),
    re.compile(r"^(?:更多|往期|相关阅读)(?:精彩)?(?:内容|文章|推荐)?\s*$"),
    re.compile(r"^你可能还喜欢\s*$"),
)

NOISE_LINES = (
    re.compile(r"^(?:点击|长按).{0,16}(?:关注|识别二维码|阅读全文|阅读原文).{0,8}$"),
    re.compile(r"^(?:点个|欢迎).{0,12}(?:赞|在看|关注|转发|分享|收藏).{0,8}$"),
    re.compile(r"^(?:一键关注|扫码关注|关注我们|设为星标).{0,12}$"),
    re.compile(r"^(?:阅读原文|点赞|在看|分享|收藏|转发|评论)\s*$"),
    re.compile(r"^(?:END|THE END)\s*$", re.IGNORECASE),
    re.compile(r"^本文(?:来源|转载)[：:].{0,80}$"),
)


def normalize_text(text: str) -> str:
    """Normalize layout without rewriting any words."""
    value = text.replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")
    lines: list[str] = []
    blank = False
    for raw_line in value.splitlines():
        line = re.sub(r"[\t ]+", " ", raw_line).strip()
        if not line:
            if lines and not blank:
                lines.append("")
            blank = True
            continue
        lines.append(line)
        blank = False
    return "\n".join(lines).strip()


def remove_noise(text: str) -> str:
    """Remove common CTA/recommendation noise while preserving body wording."""
    normalized = normalize_text(text)
    lines = normalized.splitlines()
    if not lines:
        return ""

    # Tail sections titled “推荐阅读” are almost always navigation cards. Only
    # trim them when they appear late enough to avoid deleting a real section.
    earliest_tail = max(2, int(len(lines) * 0.65))
    for index in range(earliest_tail, len(lines)):
        body_before_marker = "\n".join(lines[:index])
        if len(body_before_marker) >= 40 and any(
            pattern.fullmatch(lines[index].strip()) for pattern in TAIL_MARKERS
        ):
            lines = lines[:index]
            break

    cleaned: list[str] = []
    late_section = max(4, int(len(lines) * 0.75))
    for index, line in enumerate(lines):
        stripped = line.strip()
        if index >= late_section and any(
            pattern.fullmatch(stripped) for pattern in NOISE_LINES
        ):
            continue
        if stripped and cleaned and stripped == cleaned[-1].strip():
            continue
        cleaned.append(line)

    return normalize_text("\n".join(cleaned))


def split_text(text: str, target_chars: int = 40_000) -> list[str]:
    """Split long prose on paragraph/sentence boundaries without losing text."""
    if target_chars <= 0:
        raise ValueError("target_chars 必须大于 0")
    normalized = normalize_text(text)
    if len(normalized) <= target_chars:
        return [normalized] if normalized else []

    chunks: list[str] = []
    start = 0
    total = len(normalized)
    while start < total:
        hard_end = min(start + target_chars, total)
        if hard_end == total:
            chunks.append(normalized[start:])
            break

        # Avoid tiny chunks by looking for a natural boundary only in the
        # latter half of the target window. Delimiters stay in the preceding
        # chunk, so joining all chunks reproduces the normalized source exactly.
        soft_start = start + max(1, target_chars // 2)
        end = normalized.rfind("\n\n", soft_start, hard_end)
        if end >= soft_start:
            end += 2
        else:
            window = normalized[soft_start:hard_end]
            sentence_ends = list(re.finditer(r"[。！？.!?][\"'”’）】》]*\s*", window))
            if sentence_ends:
                end = soft_start + sentence_ends[-1].end()
            else:
                line_end = normalized.rfind("\n", soft_start, hard_end)
                end = line_end + 1 if line_end >= soft_start else hard_end

        chunks.append(normalized[start:end])
        start = end
    return chunks
