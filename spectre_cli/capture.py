from __future__ import annotations

import os
import tempfile
from pathlib import Path

try:
    import mss
    from PIL import Image
except Exception:  # noqa: BLE001
    mss = None
    Image = None


def get_environment_context() -> dict[str, str]:
    return {
        "cwd": str(Path.cwd()),
        "shell": os.getenv("SHELL", ""),
        "editor": os.getenv("EDITOR", ""),
        "term": os.getenv("TERM", ""),
    }


def read_log_tail(log_file: str, lines: int = 30) -> str:
    if not log_file:
        return ""
    path = Path(log_file).expanduser()
    if not path.exists():
        return ""
    content = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    return "\n".join(content[-lines:])


def capture_screenshot_if_enabled(enabled: bool) -> str | None:
    if not enabled or mss is None or Image is None:
        return None

    target = Path(tempfile.gettempdir()) / "spectre_cli_capture.png"
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        shot = sct.grab(monitor)
    image = Image.frombytes("RGB", shot.size, shot.rgb)
    image.save(target)
    return str(target)
