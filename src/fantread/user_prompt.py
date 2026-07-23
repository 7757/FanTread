from __future__ import annotations

import re


MAX_USER_PROMPT_CHARS = 500


def prepare_user_prompt(value: str | None) -> str | None:
    """Normalize a short user-supplied instruction before sending it to the model."""
    if value is None:
        return None
    text = re.sub(r"\s+", " ", value).strip()
    if not text:
        return None
    if len(text) > MAX_USER_PROMPT_CHARS:
        raise ValueError(f"补充要求不能超过 {MAX_USER_PROMPT_CHARS} 个字符")
    return text
