"""B2-01 보고서 조립 엔드포인트."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

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
