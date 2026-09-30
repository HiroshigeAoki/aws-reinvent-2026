"""Path constants for gitignored local-data layout (Phase B products)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL_DATA = ROOT / "local-data"


def local_data_root() -> Path:
    return LOCAL_DATA


def transcript_path(year: int, session_id: str) -> Path:
    return LOCAL_DATA / "transcripts" / str(year) / f"{session_id}.md"


def summary_path(year: int, session_id: str) -> Path:
    return LOCAL_DATA / "summaries" / str(year) / f"{session_id}.json"


def streams_path() -> Path:
    return LOCAL_DATA / "streams.json"
