from __future__ import annotations

import time
from typing import Any

import requests

from .config import SpectreConfig


class SpectreClient:
    def __init__(self, config: SpectreConfig):
        self.config = config
        self.session = requests.Session()
        self.last_error: str | None = None

        if config.api_token:
            self.session.headers.update({"Authorization": f"Bearer {config.api_token}"})

    def _url(self, path: str) -> str:
        return f"{self.config.backend_url.rstrip('/')}/{path.lstrip('/')}"

    def health(self) -> bool:
        try:
            response = self.session.get(self._url("/health"), timeout=5)
            response.raise_for_status()
            return True
        except requests.RequestException as exc:
            self.last_error = str(exc)
            return False

    def get_latest(self) -> dict[str, Any] | None:
        try:
            response = self.session.get(self._url("/latest"), timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            self.last_error = str(exc)
            return None

    def get_timeline(self) -> list[dict[str, str]]:
        try:
            response = self.session.get(self._url("/timeline"), timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            self.last_error = str(exc)
            return []

    def apply_fix(self, file_path: str, patch: str) -> dict[str, Any]:
        response = self.session.post(
            self._url("/apply-fix"),
            json={"file_path": file_path, "patch": patch},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def send_live_payload(self, payload: dict[str, Any], screenshot_path: str | None = None) -> None:
        endpoint = self.config.ingest_endpoint
        files = None

        try:
            if screenshot_path:
                files = {"screenshot": open(screenshot_path, "rb")}
                self.session.post(
                    self._url(endpoint),
                    data={"payload": str(payload)},
                    files=files,
                    timeout=5,
                )
            else:
                self.session.post(self._url(endpoint), json=payload, timeout=5)
        except requests.RequestException as exc:
            self.last_error = str(exc)
        finally:
            if files:
                files["screenshot"].close()

    def resilient_health_wait(self, retry_seconds: float = 2.0) -> None:
        while not self.health():
            print(f"[spectre-cli] backend unavailable, retrying in {retry_seconds:.1f}s: {self.last_error}")
            time.sleep(retry_seconds)
