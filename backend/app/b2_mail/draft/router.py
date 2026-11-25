"""B2-02~04 메일 초안 엔드포인트."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.b2_mail.draft import history, service
from app.b2_mail.input import B1Unavailable
from app.core.auth.deps import current_token, require_login
from app.core.schema import MailDraft, MailStatus
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
    draft_id: int, body: DraftPatch, user: Annotated[str, Depends(require_login)]
) -> MailDraft:
    d = repo.get_draft(draft_id)
    if d is None:
        raise HTTPException(status_code=404, detail="초안을 찾을 수 없습니다.")
    if d.status == MailStatus.sent:
        raise HTTPException(status_code=409, detail="이미 발송한 초안은 고칠 수 없습니다.")
    if d.status == MailStatus.approved:
        repo.revoke_approval(draft_id)  # 승인 뒤 고치면 승인 해제 (RULES.md 8-5)
    repo.update_draft(draft_id, final_body=body.final_body)
    history.add(draft_id, user, body.final_body)
    got = repo.get_draft(draft_id)
    assert got is not None
    return got


@router.get("/drafts/{draft_id}/history")
def draft_history(draft_id: int) -> list[dict[str, Any]]:
    return history.list_for(draft_id)
