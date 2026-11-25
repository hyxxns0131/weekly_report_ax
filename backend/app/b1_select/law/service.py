"""B1-12~14 법령 개정 수집·요약·대조.

출처(같은 ID면 앞 출처 우선): 법제처 API → 구글 드라이브 법령 폴더(DRIVE_LAW_FOLDER_ID)
→ Supabase 공개 DB(pub_law_change).

한 출처가 실패해도 다른 출처는 계속하고, 실패 이유를 돌려준다.
담당자가 고친 final_summary·related_food_types는 덮어쓰지 않는다.
"""

import json
from datetime import date

from pydantic import BaseModel, Field

from app.b1_select.law import (
    crosscheck,
    drive_law,
    law_api,
    new_in_force,
    reported,
    summarize,
)
from app.core.config import REPO_ROOT, get_settings
from app.core.gmail_client import GoogleAuthError
from app.core.schema import LawChange
from app.core.storage import drive, local_db, public_db, repo

SOURCES_JSON = REPO_ROOT / "backend" / "config" / "b1" / "sources.json"


class LawFetchResult(BaseModel):
    window_start: date
    window_end: date
    found: int
    added: int
    errors: list[str] = Field(default_factory=list)


def targets() -> list[str]:
    data = json.loads(SOURCES_JSON.read_text(encoding="utf-8"))
    out: list[str] = data.get("law_targets", {}).get("admrul", [])
    return out


def _from_law_api(errors: list[str]) -> list[LawChange]:
    if not get_settings().law_api_oc:
        return []  # 법제처 API를 안 쓰면(OC 비움) 조용히 건너뛴다. 드라이브 폴더가 기본 출처
    out: list[LawChange] = []
    for q in targets():
        try:
            for row in law_api.search_admrul(q):
                detail = None
                serial = str(row.get("행정규칙일련번호") or "")
                if serial:
                    try:
                        detail = law_api.admrul_detail(serial)
                    except law_api.LawApiError as e:
                        errors.append(f"{q} 본문: {e}")
                out.append(summarize.from_admrul(row, detail))
        except law_api.LawApiError as e:
            errors.append(str(e))
            break  # OC·IP 문제면 다른 검색어도 같은 이유로 실패한다
    return out


def _from_drive(errors: list[str]) -> list[LawChange]:
    folder = get_settings().drive_law_folder_id
    if not folder:
        return []  # 폴더를 안 쓰면 조용히 건너뛴다
    try:
        res = drive_law.fetch(folder)
    except (GoogleAuthError, drive.DriveError) as e:
        errors.append(f"구글 드라이브 법령 폴더: {e}")
        return []
    except Exception as e:  # noqa: BLE001  네트워크 등 예상 밖 오류에도 다른 출처는 계속
        errors.append(f"구글 드라이브 법령 폴더 오류: {e}")
        return []
    if res.skipped:
        errors.append(
            f"구글 드라이브: 읽지 않은 파일 {len(res.skipped)}개(시트·CSV·문서·txt만 읽음): "
            + ", ".join(res.skipped[:5])
            + (" …" if len(res.skipped) > 5 else "")
        )
    return res.changes


def _from_supabase(errors: list[str]) -> list[LawChange]:
    try:
        return [summarize.from_public_row(r) for r in public_db.select("pub_law_change")]
    except Exception as e:  # noqa: BLE001
        errors.append(f"Supabase pub_law_change: {e}")
        return []


def fetch(run_id: int) -> LawFetchResult:
    run = local_db.get_run(run_id)
    if run is None:
        raise KeyError(run_id)
    start, end = date.fromisoformat(run.period_start), date.fromisoformat(run.period_end)
    errors: list[str] = []
    found = {c.id: c for c in _from_law_api(errors)}
    for c in _from_drive(errors) + _from_supabase(errors):
        found.setdefault(c.id, c)
    picked = new_in_force.pick(list(found.values()), start, end, reported.reported_ids())
    picked = crosscheck.crosscheck(picked, notices=[])
    existing = {c.id: c for c in repo.list_law(run_id)}
    for c in picked:
        old = existing.get(c.id)
        if old:
            c.final_summary = old.final_summary
            c.related_food_types = old.related_food_types
        repo.save_law(run_id, c)
    lo, hi = new_in_force.window(start, end)
    return LawFetchResult(
        window_start=lo, window_end=hi, found=len(found), added=len(picked), errors=errors
    )
