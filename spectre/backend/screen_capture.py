"""Screen capture module for S.P.E.C.T.R.E."""

from __future__ import annotations

import tempfile
import time
from pathlib import Path

import mss
from PIL import Image

from ai_analyzer import analyze_image
from suggestion_engine import generate_suggestion

INTERVAL_SECONDS = 2


def capture_screen(output_dir: str | Path | None = None) -> Path:
    """Capture the primary monitor and return the saved image path."""
    folder = Path(output_dir) if output_dir else Path(tempfile.gettempdir())
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "spectre_latest.png"

    with mss.mss() as sct:
        monitor = sct.monitors[1]
        shot = sct.grab(monitor)

    image = Image.frombytes("RGB", shot.size, shot.rgb)
    image.save(target)
    return target


def capture_loop(output_dir: str | Path | None = None) -> None:
    """Capture screen every 2 seconds and print structured AI analysis."""
    while True:
        path = capture_screen(output_dir=output_dir)
        result = generate_suggestion(analyze_image(path))

        print("[SPECTRE]\n")
        print(f"Issue: {result['issue']}")
        print(f"Severity: {str(result['severity']).upper()}\n")
        print(f"Fix: {result['suggestion']}")
        if result.get("patch"):
            print("\nPatch:")
            print(result["patch"])
        print()

        time.sleep(INTERVAL_SECONDS)
