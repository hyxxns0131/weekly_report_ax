"""주간 실행·현황·알림 엔드포인트 (C-06)."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.auth.deps import require_login
from app.core.runs import notices
from app.core.runs.service import RunStatus, run_status
from app.core.storage import local_db

router = APIRouter(tags=["core: runs"])


class RunCreate(BaseModel):
    reference_date: date | None = None


@router.post("/runs", response_model=local_db.RunRow)
def create_run(body: RunCreate, user: Annotated[str, Depends(require_login)]) -> local_db.RunRow:
    ref = body.reference_date or local_db.now_kst().date()
    return local_db.create_run(ref.isoformat(), created_by=user)


@router.get("/runs/latest", response_model=local_db.RunRow | None)
def latest_run() -> local_db.RunRow | None:
    return local_db.latest_run()


@router.get("/runs/{run_id}/status", response_model=RunStatus)
def get_status(run_id: int) -> RunStatus:
    run = local_db.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="주간 실행을 찾을 수 없습니다.")
    return run_status(run)


@router.get("/runs/{run_id}/notices", response_model=notices.NoticeList)
def get_notices(run_id: int) -> notices.NoticeList:
    if local_db.get_run(run_id) is None:
        raise HTTPException(status_code=404, detail="주간 실행을 찾을 수 없습니다.")
    return notices.list_notices(run_id)


class NoticeMark(BaseModel):
    action: notices.NoticeAction
    run_id: int | None = None


@router.patch("/notices/{notice_id:path}", response_model=local_db.NoticeState)
def patch_notice(
    notice_id: str, body: NoticeMark, user: Annotated[str, Depends(require_login)]
) -> local_db.NoticeState:
    """읽음·지움. 기록자는 로그인한 사용자 (DESIGN.md 3-2)."""
    return notices.mark(notice_id, body.run_id, body.action, user)
