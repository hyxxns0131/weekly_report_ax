"""B1-01~07 수집 처리 순서. 한 출처가 실패해도 다른 출처는 계속한다."""

import json
from collections.abc import Callable
from datetime import date
from typing import Any

from app.b1_select.collect.base import CollectResult
from app.b1_select.collect.sources import (
    gyeongin_newsletter,
    impfood_inspection,
    impfood_law_policy,
    impfood_unfit,
    mfds_notice,
    supabase_public,
)
from app.core.config import REPO_ROOT
from app.core.storage import local_db, repo

SOURCES_JSON = REPO_ROOT / "backend" / "config" / "b1" / "sources.json"

Collector = Callable[[int, date, date, dict[str, Any]], CollectResult]
# 출처 id → 수집기. 출처를 늘릴 때는 sources/에 파일을 추가하고 여기에 한 줄 더한다.
COLLECTORS: dict[str, Collector] = {
    impfood_unfit.SOURCE_ID: impfood_unfit.collect,
    impfood_inspection.SOURCE_ID: impfood_inspection.collect,
    impfood_law_policy.SOURCE_ID: impfood_law_policy.collect,
    mfds_notice.SOURCE_ID: mfds_notice.collect,
    gyeongin_newsletter.SOURCE_ID: gyeongin_newsletter.collect,
}


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

    # 2) 사이트별 수집기: sources.json의 mode(demo | auto | manual)를 따른다.
    for s in source_config():
        sid = s["id"]
        if selected and sid not in selected:
            continue
        if sid == "law_api":
            continue  # 법령은 법령 개정 단계(B1-12)에서 가져온다
        if not s.get("enabled"):
            results.append(
                save(run_id, CollectResult(source=sid, status="off", message="사용 안 함"))
            )
            continue
        collector = COLLECTORS.get(sid)
        if s.get("mode", "manual") == "manual" or collector is None:
            results.append(
                save(
                    run_id,
                    CollectResult(
                        source=sid, status="manual", message="자동 수집기 준비 전 → 수동 업로드"
                    ),
                )
            )
            continue
        try:
            result = collector(run_id, start, end, s)
        except Exception as e:  # noqa: BLE001 - 한 출처 실패가 전체를 멈추지 않게
            result = CollectResult(source=sid, status="failed", message=f"수집 실패: {e}")
        results.append(save(run_id, result))
    return results
