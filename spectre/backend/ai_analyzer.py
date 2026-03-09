"""AI analysis module for S.P.E.C.T.R.E."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_PROMPT = """You are a senior software engineer reviewing a developer screen.

Analyze the screenshot and detect:
- coding errors
- terminal errors
- UI layout issues
- bad practices

Use the previous analyses as context to avoid repeating identical advice and to track progression.

Recent analysis history:
{history}

Return ONLY JSON:

{
 "issue": "short description",
 "suggestion": "how to fix it",
 "severity": "low | medium | high",
 "fix_code": "corrected code snippet",
 "explanation": "technical explanation",
 "patch": "diff style patch",
 "language": "detected language"
}
"""

ANALYSIS_HISTORY: list[dict[str, str | None]] = []
MAX_HISTORY = 5


class AIAnalyzerError(RuntimeError):
    """Raised when the multimodal API call fails."""


def _normalize_result(parsed: dict[str, object]) -> dict[str, str | None]:
    issue = str(parsed.get("issue", "No obvious issue detected.")).strip()
    suggestion = str(parsed.get("suggestion", "No suggestion generated.")).strip()
    severity = str(parsed.get("severity", "low")).strip().lower()
    if severity not in {"low", "medium", "high"}:
        severity = "low"

    def optional_text(key: str) -> str | None:
        value = parsed.get(key)
        if isinstance(value, str):
            return value.strip() or None
        return None

    explanation = str(parsed.get("explanation", "No explanation provided.")).strip()
    language = optional_text("language") or "unknown"

    return {
        "issue": issue,
        "suggestion": suggestion,
        "severity": severity,
        "fix_code": optional_text("fix_code"),
        "explanation": explanation,
        "patch": optional_text("patch"),
        "language": language,
    }


def _extract_json_from_text(raw_text: str) -> dict[str, str | None]:
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise AIAnalyzerError(f"Model response does not contain JSON: {raw_text}")

    parsed = json.loads(cleaned[start : end + 1])
    if not isinstance(parsed, dict):
        raise AIAnalyzerError(f"Model JSON is not an object: {parsed}")

    return _normalize_result(parsed)


def _build_history_context() -> str:
    if not ANALYSIS_HISTORY:
        return "[]"
    return json.dumps(ANALYSIS_HISTORY[-MAX_HISTORY:], ensure_ascii=False, indent=2)


def _push_history(result: dict[str, str | None]) -> None:
    ANALYSIS_HISTORY.append(result)
    if len(ANALYSIS_HISTORY) > MAX_HISTORY:
        del ANALYSIS_HISTORY[0 : len(ANALYSIS_HISTORY) - MAX_HISTORY]


def analyze_image(image_path: str | Path) -> dict[str, str | None]:
    """Analyze screenshot with Gemini and return structured debugging feedback."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        result = {
            "issue": "Missing Gemini API key",
            "suggestion": "Set GEMINI_API_KEY in your environment or .env file.",
            "severity": "high",
            "fix_code": None,
            "explanation": "The backend cannot call Gemini without an API key.",
            "patch": None,
            "language": "unknown",
        }
        _push_history(result)
        return result

    path = Path(image_path)
    if not path.exists():
        raise AIAnalyzerError(f"Screenshot file not found: {path}")

    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={api_key}"
    )

    prompt = DEFAULT_PROMPT.format(history=_build_history_context())
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/png", "data": encoded}},
                ]
            }
        ]
    }

    response = requests.post(url, json=payload, timeout=30)
    if response.status_code >= 400:
        raise AIAnalyzerError(
            f"Gemini request failed ({response.status_code}): {response.text}"
        )

    data = response.json()
    try:
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise AIAnalyzerError(f"Unexpected Gemini response: {data}") from exc

    try:
        result = _extract_json_from_text(raw_text)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise AIAnalyzerError(f"Failed to parse model JSON: {raw_text}") from exc

    _push_history(result)
    return result
