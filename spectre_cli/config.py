from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

CONFIG_DIR = Path.home() / ".spectre"
CONFIG_PATH = CONFIG_DIR / "config.json"


@dataclass
class SpectreConfig:
    backend_url: str = "http://localhost:8000"
    api_token: str = ""
    voice_enabled: bool = False
    screenshots_enabled: bool = False
    screenshot_interval_seconds: float = 2.0
    ingest_endpoint: str = "/cli/ingest"
    log_file: str = ""


def load_config() -> SpectreConfig:
    if not CONFIG_PATH.exists():
        return SpectreConfig()

    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    cfg = SpectreConfig()
    for key, value in data.items():
        if hasattr(cfg, key):
            setattr(cfg, key, value)
    return cfg


def save_config(config: SpectreConfig) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(asdict(config), indent=2), encoding="utf-8")


def interactive_setup() -> SpectreConfig:
    current = load_config()
    backend = input(f"Backend URL [{current.backend_url}]: ").strip() or current.backend_url
    token = input("API token (leave empty to keep current): ").strip() or current.api_token

    voice_raw = input(f"Enable voice alerts? (y/N) [{'y' if current.voice_enabled else 'n'}]: ").strip().lower()
    if voice_raw in {"y", "yes"}:
        voice = True
    elif voice_raw in {"n", "no", ""}:
        voice = current.voice_enabled if voice_raw == "" else False
    else:
        voice = current.voice_enabled

    screenshot_raw = input(
        f"Enable screenshots if permission granted? (y/N) [{'y' if current.screenshots_enabled else 'n'}]: "
    ).strip().lower()
    if screenshot_raw in {"y", "yes"}:
        screenshots = True
    elif screenshot_raw in {"n", "no", ""}:
        screenshots = current.screenshots_enabled if screenshot_raw == "" else False
    else:
        screenshots = current.screenshots_enabled

    cfg = SpectreConfig(
        backend_url=backend,
        api_token=token,
        voice_enabled=voice,
        screenshots_enabled=screenshots,
        screenshot_interval_seconds=current.screenshot_interval_seconds,
        ingest_endpoint=current.ingest_endpoint,
        log_file=current.log_file,
    )
    save_config(cfg)
    return cfg
