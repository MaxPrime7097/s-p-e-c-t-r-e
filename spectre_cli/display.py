from __future__ import annotations

RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
CYAN = "\033[36m"


def _severity_color(severity: str) -> str:
    sev = severity.lower()
    if sev == "high":
        return RED
    if sev == "medium":
        return YELLOW
    return GREEN


def render_suggestion(suggestion: dict[str, object]) -> str:
    severity = str(suggestion.get("severity", "low"))
    color = _severity_color(severity)

    issue = suggestion.get("issue", "-")
    fix = suggestion.get("suggestion", "-")
    explanation = suggestion.get("explanation", "-")
    patch = suggestion.get("patch") or "No patch available"

    return (
        f"{BOLD}{CYAN}[SPECTRE]{RESET}\n"
        f"Issue: {issue}\n"
        f"Severity: {color}{severity.upper()}{RESET}\n"
        f"Suggestion: {fix}\n"
        f"Explanation: {explanation}\n"
        f"Patch:\n{patch}\n"
    )
