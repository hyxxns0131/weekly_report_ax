"""B2-06 검증 엔드포인트."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.b2_mail.evaluate import golden, service
from app.b2_mail.input import B1Unavailable
from app.core.auth.deps import current_token
from app.core.schema import EvalResult
from app.core.storage import repo

router = APIRouter()


class EvalRequest(BaseModel):
    run_id: int
    golden_week: str


@router.get("/eval/weeks", response_model=list[str])
def weeks() -> list[str]:
    return golden.list_weeks()


@router.post("/eval", response_model=EvalResult)
def run_eval(
    body: EvalRequest, token: Annotated[str | None, Depends(current_token)], source: str = "api"
) -> EvalResult:
    try:
        return service.run_eval(body.run_id, body.golden_week, token, source)
    except service.NoGolden as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except B1Unavailable as e:
        raise HTTPException(status_code=502, detail=str(e)) from e


@router.get("/runs/{run_id}/eval", response_model=EvalResult | None)
def get_eval(run_id: int) -> EvalResult | None:
    return repo.get_eval(run_id)
