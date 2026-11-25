"""samples/b1_output/sample_week.json이 공통 스키마(WeeklySelection)와 맞는지 확인."""

import json
from pathlib import Path

from app.core.schema import WeeklySelection

SAMPLE = Path(__file__).resolve().parents[3] / "samples" / "b1_output" / "sample_week.json"


def test_sample_week_matches_schema() -> None:
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    ws = WeeklySelection.model_validate(data)
    assert len(ws.items) == 4
    assert len(ws.law_changes) == 1
