from __future__ import annotations

from typing import Any


CONTEXT_FIELDS = [
    "project",
    "goal",
    "context",
    "environment",
    "workflow",
    "rules",
    "git_rules",
    "versioning_rules",
    "dependency_rules",
    "ignore_rules",
    "constraints",
    "forbidden",
    "verification",
    "output_format",
    "files",
    "warnings",
]


def empty_context() -> dict[str, list[str]]:
    return {field: [] for field in CONTEXT_FIELDS}


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, list):
        items = value
    else:
        items = [str(value)]

    cleaned: list[str] = []
    for item in items:
        text = str(item).strip()
        if text:
            cleaned.append(text)
    return cleaned


def dedupe(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        key = " ".join(item.lower().split())
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def normalize_context(data: dict[str, Any] | None) -> dict[str, list[str]]:
    normalized = empty_context()
    if not data:
        return normalized

    for field in CONTEXT_FIELDS:
        normalized[field] = dedupe(as_list(data.get(field)))

    # Older converter outputs used "project" as the default bucket.
    if not normalized["context"] and normalized["project"]:
        normalized["context"] = []

    return normalized


def estimate_tokens(text: str) -> int:
    """Small offline estimate for UI feedback, not a tokenizer replacement."""
    if not text:
        return 0
    ascii_chars = sum(1 for char in text if ord(char) < 128)
    non_ascii_chars = len(text) - ascii_chars
    return max(1, round((ascii_chars / 4) + (non_ascii_chars / 2)))
