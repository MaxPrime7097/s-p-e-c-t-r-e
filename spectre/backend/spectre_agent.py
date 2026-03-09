"""Terminal autonomous agent mode for S.P.E.C.T.R.E."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from ai_analyzer import analyze_image
from main import _apply_unified_patch
from screen_capture import INTERVAL_SECONDS, capture_screen
from suggestion_engine import generate_suggestion


def run_agent(auto_apply: bool = False, target_file: str | None = None) -> None:
    """Run capture/analyze loop and optionally auto-apply generated patches."""
    while True:
        screenshot = capture_screen()
        result = generate_suggestion(analyze_image(screenshot))

        print("[SPECTRE]\n")
        print(f"Issue: {result['issue']}")
        print(f"Severity: {str(result['severity']).upper()}\n")
        print(f"Fix: {result['suggestion']}")

        if auto_apply and target_file and result.get("patch"):
            path = Path(target_file)
            try:
                updated = _apply_unified_patch(path.read_text(encoding="utf-8"), result["patch"] or "")
                path.write_text(updated, encoding="utf-8")
                print(f"[SPECTRE] Patch auto-applied to {path}")
            except Exception as exc:  # noqa: BLE001
                print(f"[SPECTRE] Auto-apply failed: {exc}")

        print()
        time.sleep(INTERVAL_SECONDS)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run S.P.E.C.T.R.E terminal agent mode")
    parser.add_argument("--auto-apply", action="store_true", help="Apply generated patch automatically")
    parser.add_argument("--target-file", help="Target file path used with --auto-apply")
    args = parser.parse_args()

    if args.auto_apply and not args.target_file:
        raise SystemExit("--target-file is required when --auto-apply is enabled")

    run_agent(auto_apply=args.auto_apply, target_file=args.target_file)


if __name__ == "__main__":
    main()
