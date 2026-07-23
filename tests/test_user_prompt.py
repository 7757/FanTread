import pytest

from fantread.user_prompt import prepare_user_prompt


def test_prepare_user_prompt_normalizes_short_instruction() -> None:
    assert prepare_user_prompt("  尽量   保持原文。  ") == "尽量 保持原文。"
    assert prepare_user_prompt("") is None
    assert prepare_user_prompt(None) is None


def test_prepare_user_prompt_limits_length() -> None:
    with pytest.raises(ValueError, match="不能超过"):
        prepare_user_prompt("很" * 501)
