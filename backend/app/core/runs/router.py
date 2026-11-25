"""주간 실행·현황 엔드포인트 (C-06)."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.auth.deps import require_login
from app.core.runs.service import RunStatus, run_status
from app.core.storage import local_db

router = APIRouter(prefix="/runs", tags=["core: runs"])


class RunCreate(BaseModel):
    reference_date: date | None = None


@router.post("", response_model=local_db.RunRow)
def create_run(body: RunCreate, user: Annotated[str, Depends(require_login)]) -> local_db.RunRow:
    ref = body.reference_date or local_db.now_kst().date()
    return local_db.create_run(ref.isoformat(), created_by=user)


@router.get("/latest", response_model=local_db.RunRow | None)
def latest_run() -> local_db.RunRow | None:
    return local_db.latest_run()


@router.get("/{run_id}/status", response_model=RunStatus)
def get_status(run_id: int) -> RunStatus:
    run = local_db.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="주간 실행을 찾을 수 없습니다.")
    return run_status(run)
