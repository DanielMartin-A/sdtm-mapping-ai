"""Tests for the shared LLM client (C1 fix)."""

import json

import pytest

from sdtm_mapping_ai.models.llm_client import LLMClient, sanitize_for_prompt


def test_parse_json_clean():
    result = LLMClient.parse_json('{"key": "value", "num": 42}')
    assert result == {"key": "value", "num": 42}


def test_parse_json_with_markdown_fences():
    raw = '```json\n{"domain": "AE", "confidence": 0.9}\n```'
    result = LLMClient.parse_json(raw)
    assert result["domain"] == "AE"
    assert result["confidence"] == 0.9


def test_parse_json_with_bare_fences():
    raw = '```\n{"x": 1}\n```'
    result = LLMClient.parse_json(raw)
    assert result["x"] == 1


def test_parse_json_invalid_raises():
    with pytest.raises(json.JSONDecodeError):
        LLMClient.parse_json("not json at all")


def test_sanitize_for_prompt_basic():
    result = sanitize_for_prompt(["hello", "world"])
    assert result == "hello, world"


def test_sanitize_for_prompt_strips_braces():
    result = sanitize_for_prompt(["value{injection}", "normal"])
    assert "{" not in result
    assert "}" not in result


def test_sanitize_for_prompt_limits_items():
    values = [f"val{i}" for i in range(20)]
    result = sanitize_for_prompt(values, max_items=3)
    assert result.count(",") == 2  # 3 items = 2 commas


def test_sanitize_for_prompt_truncates_length():
    result = sanitize_for_prompt(["a" * 200], max_chars=50)
    assert len(result) <= 50


def test_sanitize_for_prompt_empty():
    assert sanitize_for_prompt([]) == "(none)"
    assert sanitize_for_prompt(None or []) == "(none)"
