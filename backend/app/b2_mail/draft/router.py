"""B2-02~04 메일 초안 엔드포인트."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.b2_mail.draft import history, service
from app.b2_mail.input import B1Unavailable
from app.core.auth.deps import current_token, require_login
from app.core.schema import MailDraft
from app.core.storage import repo

router = APIRouter()


class DraftPatch(BaseModel):
    final_body: str


@router.post("/runs/{run_id}/drafts", response_model=list[MailDraft])
def make_drafts(
    run_id: int, token: Annotated[str | None, Depends(current_token)], source: str = "api"
) -> list[MailDraft]:
    try:
        return service.generate(run_id, token, source)
    except B1Unavailable as e:
        raise HTTPException(status_code=502, detail=str(e)) from e


@router.get("/runs/{run_id}/drafts", response_model=list[MailDraft])
def list_drafts(run_id: int) -> list[MailDraft]:
    return repo.list_drafts(run_id)


@router.patch("/drafts/{draft_id}", response_model=MailDraft)
def patch_draft(
    draft_id: int,
    body: DraftPatch,
    user: Annotated[str, Depends(require_login)],
    token: Annotated[str | None, Depends(current_token)],
    source: str = "api",
) -> MailDraft:
    try:
        return service.save_edit(draft_id, body.final_body, user, token, source)
    except service.DraftNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except service.DraftLocked as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.get("/drafts/{draft_id}/history")
def draft_history(draft_id: int) -> list[dict[str, Any]]:
    return history.list_for(draft_id)
