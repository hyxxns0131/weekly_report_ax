"""b1 결과 읽기 (KHW). b1 코드를 import하지 않고 API 응답만 쓴다 (AGENTS.md 5-6).

- 기본: 같은 PC의 FastAPI에 GET /api/b1/runs/{run_id}/result (로그인 토큰을 그대로 넘긴다).
- source="sample"이면 samples/b1_output/sample_week.json (b1 준비 전 개발·테스트용).
"""

import json
from pathlib import Path
from typing import Any

import httpx

from app.core.config import REPO_ROOT, get_settings
from app.core.schema import WeeklySelection

SAMPLE = REPO_ROOT / "samples" / "b1_output" / "sample_week.json"


class B1Unavailable(Exception):
    pass


def _base() -> str:
    s = get_settings()
    return f"http://{s.api_host}:{s.api_port}/api/b1"


def _get(path: str, token: str | None) -> Any:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        res = httpx.get(f"{_base()}{path}", headers=headers, timeout=30)
    except httpx.HTTPError as e:
        raise B1Unavailable(f"b1 결과를 읽지 못했습니다: {e}") from e
    if res.status_code != 200:
        raise B1Unavailable(f"b1 결과를 읽지 못했습니다 ({res.status_code})")
    return res.json()


def load_selection(run_id: int, token: str | None, source: str = "api") -> WeeklySelection:
    if source == "sample":
        return WeeklySelection.model_validate(json.loads(Path(SAMPLE).read_text(encoding="utf-8")))
    return WeeklySelection.model_validate(_get(f"/runs/{run_id}/result", token))


def load_customer_names(token: str | None, source: str = "api") -> dict[str, str]:
    """가명 ID → 화면 표시명. 실명은 이 PC 화면·메일 초안 안에서만 쓴다."""
    if source == "sample":
        # 가상 고객사만 (config/b1/customers/sample_*.json과 같게). C003은 LSH demo_week.json용.
        return {"C001": "A사", "C002": "B사", "C003": "C사"}
    rows: list[dict[str, Any]] = _get("/settings/customers", token)
    return {r["customer_id"]: r["display_name"] for r in rows}
