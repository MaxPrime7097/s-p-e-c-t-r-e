"""Suggestion cleanup logic for S.P.E.C.T.R.E."""

from __future__ import annotations

from typing import Any


DEFAULT_SUGGESTION: dict[str, str | None] = {
    "issue": "No issue detected",
    "suggestion": "No suggestion generated.",
    "severity": "low",
    "fix_code": None,
    "explanation": "No explanation available.",
    "patch": None,
    "language": "unknown",
}


def generate_suggestion(ai_response: dict[str, Any] | None) -> dict[str, str | None]:
    """Normalize the structured AI response into a stable payload."""
    if not ai_response:
        return dict(DEFAULT_SUGGESTION)

    severity = str(ai_response.get("severity", "low")).strip().lower()
    if severity not in {"low", "medium", "high"}:
        severity = "low"

    def optional_text(key: str) -> str | None:
        value = ai_response.get(key)
        if isinstance(value, str):
            return value.strip() or None
        return None

    return {
        "issue": str(ai_response.get("issue", DEFAULT_SUGGESTION["issue"])).strip(),
        "suggestion": str(
            ai_response.get("suggestion", DEFAULT_SUGGESTION["suggestion"])
        ).strip(),
        "severity": severity,
        "fix_code": optional_text("fix_code"),
        "explanation": str(
            ai_response.get("explanation", DEFAULT_SUGGESTION["explanation"])
        ).strip(),
        "patch": optional_text("patch"),
        "language": optional_text("language") or "unknown",
    }
