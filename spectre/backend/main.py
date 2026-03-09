"""FastAPI backend for S.P.E.C.T.R.E."""

from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ai_analyzer import AIAnalyzerError, analyze_image
from suggestion_engine import DEFAULT_SUGGESTION, generate_suggestion

app = FastAPI(title="S.P.E.C.T.R.E API", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LATEST_SUGGESTION: dict[str, str | None] = dict(DEFAULT_SUGGESTION)
LATEST_SUGGESTION.update(
    {
        "issue": "No issue detected yet.",
        "suggestion": "Upload a screenshot or start the capture loop.",
        "explanation": "S.P.E.C.T.R.E is waiting for its first analysis.",
    }
)
DEBUG_TIMELINE: list[dict[str, str]] = []
MAX_TIMELINE = 50


class ApplyFixRequest(BaseModel):
    file_path: str
    patch: str


def _record_timeline(issue: str) -> None:
    DEBUG_TIMELINE.append({"time": datetime.now().strftime("%H:%M:%S"), "issue": issue})
    if len(DEBUG_TIMELINE) > MAX_TIMELINE:
        del DEBUG_TIMELINE[0 : len(DEBUG_TIMELINE) - MAX_TIMELINE]


def _extract_patch_chunks(patch_text: str) -> tuple[str, str]:
    removed: list[str] = []
    added: list[str] = []

    for line in patch_text.splitlines():
        if line.startswith(("---", "+++", "@@")):
            continue
        if line.startswith("-"):
            removed.append(line[1:])
        elif line.startswith("+"):
            added.append(line[1:])

    return "\n".join(removed).strip(), "\n".join(added).strip()


def _apply_unified_patch(original: str, patch_text: str) -> str:
    removed_block, added_block = _extract_patch_chunks(patch_text)
    if not added_block:
        raise ValueError("Patch does not contain added lines.")

    if removed_block:
        if removed_block not in original:
            raise ValueError("Could not locate patch removal block in target file.")
        return original.replace(removed_block, added_block, 1)

    return f"{original.rstrip()}\n{added_block}\n"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/latest")
def latest() -> dict[str, str | None]:
    return LATEST_SUGGESTION


@app.get("/timeline")
def timeline() -> list[dict[str, str]]:
    return DEBUG_TIMELINE


@app.post("/analyze")
async def analyze(image: UploadFile = File(...)) -> dict[str, str | None]:
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    safe_name = image.filename or "upload.png"
    tmp_path = Path(tempfile.gettempdir()) / f"spectre_upload_{safe_name}"
    tmp_path.write_bytes(await image.read())

    try:
        ai_response = analyze_image(tmp_path)
        suggestion = generate_suggestion(ai_response)
    except AIAnalyzerError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    global LATEST_SUGGESTION
    LATEST_SUGGESTION = suggestion
    _record_timeline(suggestion["issue"] or "Unknown issue")
    return suggestion


@app.post("/apply-fix")
def apply_fix(payload: ApplyFixRequest) -> dict[str, str]:
    if not payload.patch.strip():
        raise HTTPException(status_code=400, detail="Patch cannot be empty.")

    target = Path(payload.file_path).expanduser().resolve()
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Target file not found.")

    try:
        original = target.read_text(encoding="utf-8")
        updated = _apply_unified_patch(original, payload.patch)
        target.write_text(updated, encoding="utf-8")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Could not apply patch: {exc}") from exc

    return {"status": "applied", "file_path": str(target)}
