from __future__ import annotations

import json
from pathlib import Path
from typing import Any

VALIDATION_DATE = "2026-06-09"
VALIDATION_SCOPE = 'Evidence-tiered spatial regulatory graph construction with negative-control survival metrics.'
VALIDATION_SOURCE = "evidence/summary.json"


def evidence_summary_path() -> Path:
    return Path(__file__).resolve().parents[2] / "evidence" / "summary.json"


def load_evidence_summary(path: Path | None = None) -> dict[str, Any]:
    summary_path = path or evidence_summary_path()
    with summary_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("evidence summary must be a JSON object")
    return payload
