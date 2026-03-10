from __future__ import annotations

import platform
import shutil
import subprocess


def speak(text: str) -> None:
    system = platform.system().lower()

    if system == "darwin" and shutil.which("say"):
        subprocess.Popen(["say", text])
        return

    if shutil.which("espeak"):
        subprocess.Popen(["espeak", text])
        return

    print("\a", end="")
