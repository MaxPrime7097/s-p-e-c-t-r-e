from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from .capture import capture_screenshot_if_enabled, get_environment_context, read_log_tail
from .client import SpectreClient
from .config import CONFIG_DIR, SpectreConfig, interactive_setup, load_config
from .display import render_suggestion
from .voice import speak

STATE_PATH = CONFIG_DIR / "state.json"


def _save_state(last_suggestion: dict[str, Any] | None) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"last_suggestion": last_suggestion or {}}
    STATE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {}
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def cmd_live(config: SpectreConfig, voice_enabled: bool) -> None:
    client = SpectreClient(config)
    client.resilient_health_wait()

    last_issue = ""
    print("[spectre-cli] connected. Press Ctrl+C to stop.")

    try:
        while True:
            payload = {
                "timestamp": time.time(),
                "environment": get_environment_context(),
                "logs": read_log_tail(config.log_file),
            }

            screenshot = capture_screenshot_if_enabled(config.screenshots_enabled)
            client.send_live_payload(payload, screenshot)

            suggestion = client.get_latest()
            if suggestion:
                print(render_suggestion(suggestion))
                _save_state(suggestion)

                issue = str(suggestion.get("issue", ""))
                severity = str(suggestion.get("severity", "low")).lower()
                if voice_enabled and severity == "high" and issue and issue != last_issue:
                    speak(f"Warning. {issue}")
                    last_issue = issue

            time.sleep(max(1.0, float(config.screenshot_interval_seconds)))
    except KeyboardInterrupt:
        print("\n[spectre-cli] stopped.")


def cmd_status(config: SpectreConfig) -> None:
    client = SpectreClient(config)
    connected = client.health()
    state = _load_state()

    print(f"Backend: {config.backend_url}")
    print(f"Connected: {'yes' if connected else 'no'}")
    if not connected and client.last_error:
        print(f"Last error: {client.last_error}")

    last = state.get("last_suggestion")
    if last:
        print("\nLast suggestion:")
        print(render_suggestion(last))


def cmd_apply(config: SpectreConfig, file_path: str | None) -> None:
    state = _load_state()
    suggestion = state.get("last_suggestion") or {}
    patch = suggestion.get("patch")

    if not patch:
        print("No patch in latest suggestion. Run live mode first.")
        return

    target_file = file_path or input("Target file path: ").strip()
    if not target_file:
        print("File path is required.")
        return

    client = SpectreClient(config)
    try:
        result = client.apply_fix(target_file, patch)
        print(f"Patch applied: {result}")
    except Exception as exc:  # noqa: BLE001
        print(f"Apply failed: {exc}")


def cmd_timeline(config: SpectreConfig) -> None:
    client = SpectreClient(config)
    rows = client.get_timeline()
    if not rows:
        print("No timeline data available.")
        if client.last_error:
            print(f"Error: {client.last_error}")
        return

    for item in rows:
        print(f"[{item.get('time', '--:--:--')}] {item.get('issue', '-')}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="spectre-cli", description="S.P.E.C.T.R.E terminal CLI")
    sub = parser.add_subparsers(dest="command")

    live = sub.add_parser("live", help="Run realtime terminal loop")
    live.add_argument("--voice", action="store_true", help="Enable terminal voice alerts")

    sub.add_parser("status", help="Show backend status and latest suggestion")

    apply_cmd = sub.add_parser("apply", help="Apply latest patch via backend /apply-fix")
    apply_cmd.add_argument("--file", dest="file_path", help="Target file path")

    sub.add_parser("timeline", help="Show backend issue timeline")
    sub.add_parser("config", help="Interactive configuration setup")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    command = args.command or "live"

    if command == "config":
        cfg = interactive_setup()
        print(f"Saved config to {cfg.backend_url}")
        return

    config = load_config()

    if command == "live":
        cmd_live(config, voice_enabled=args.voice or config.voice_enabled)
    elif command == "status":
        cmd_status(config)
    elif command == "apply":
        cmd_apply(config, file_path=args.file_path)
    elif command == "timeline":
        cmd_timeline(config)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
