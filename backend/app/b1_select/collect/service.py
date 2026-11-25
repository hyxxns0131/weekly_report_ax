"""B1-01~07 수집 처리 순서. 한 출처가 실패해도 다른 출처는 계속한다."""

import json
from datetime import date
from typing import Any

from app.b1_select.collect.base import CollectResult
from app.b1_select.collect.sources import supabase_public
from app.core.config import REPO_ROOT
from app.core.storage import local_db, repo

SOURCES_JSON = REPO_ROOT / "backend" / "config" / "b1" / "sources.json"


def source_config() -> list[dict[str, Any]]:
    data: dict[str, list[dict[str, Any]]] = json.loads(SOURCES_JSON.read_text(encoding="utf-8"))
    return data["sources"]


def save(run_id: int, result: CollectResult) -> CollectResult:
    for item in result.items:
        repo.save_raw(item)
    repo.save_collect_log(run_id, result.source, result.status, len(result.items), result.message)
    return result


def collect(run_id: int, selected: list[str] | None) -> list[CollectResult]:
    run = local_db.get_run(run_id)
    if run is None:
        raise KeyError(run_id)
    start, end = date.fromisoformat(run.period_start), date.fromisoformat(run.period_end)
    results: list[CollectResult] = []

    # 1) Supabase 공개 정보 DB (PM이 적재한 것)
    if not selected or supabase_public.NAME in selected:
        results.append(save(run_id, supabase_public.collect(run_id, start, end)))

    # 2) 사이트별 수집기: 아직 만들지 않은 출처는 "수동 업로드"로 표시 (P1, LSH)
    for s in source_config():
        if selected and s["id"] not in selected:
            continue
        if s["id"] == "law_api":
            continue  # 법령은 법령 개정 탭(B1-12)에서 가져온다
        if not s.get("enabled"):
            results.append(
                save(run_id, CollectResult(source=s["id"], status="off", message="사용 안 함"))
            )
            continue
        results.append(
            save(
                run_id,
                CollectResult(
                    source=s["id"],
                    status="manual",
                    message="자동 수집기 준비 전 → 수동 업로드",
                ),
            )
        )
    return results
