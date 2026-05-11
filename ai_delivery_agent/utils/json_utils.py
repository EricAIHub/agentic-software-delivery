from __future__ import annotations

import json
from typing import Any, Dict


def extract_json_object(text: str) -> Dict[str, Any]:
    """Extract the first plausible JSON object from an LLM response."""
    text = text.strip()
    if not text:
        return {}

    if text.startswith("```json"):
        text = text.removeprefix("```json").strip()
        text = text.removesuffix("```").strip()
    elif text.startswith("```"):
        text = text.removeprefix("```").strip()
        text = text.removesuffix("```").strip()

    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}

    try:
        value = json.loads(text[start : end + 1])
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        return {}
