"""B2-01 보고서 조립 엔드포인트."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.b2_mail.input import B1Unavailable
from app.b2_mail.report import service
from app.core.auth.deps import current_token

router = APIRouter()


@router.post("/runs/{run_id}/report", response_model=service.ReportOut)
def build_report(
    run_id: int, token: Annotated[str | None, Depends(current_token)], source: str = "api"
) -> service.ReportOut:
    try:
        out, _ = service.build(run_id, token, source)
    except B1Unavailable as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    return out


class ReannounceBody(BaseModel):
    text: str | None = None


@router.put("/runs/{run_id}/report/reannounce", response_model=ReannounceBody)
def put_reannounce(run_id: int, body: ReannounceBody) -> ReannounceBody:
    """새 개정이 없는 주에 섹션 2에 넣을 재안내 글 저장 (비우면 지움). 다시 조립하면 반영."""
    service.set_reannounce(run_id, body.text)
    return body
