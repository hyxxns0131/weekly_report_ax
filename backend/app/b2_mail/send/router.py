"""B2-05·08 승인·발송 엔드포인트."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.b2_mail.send import approve, gmail_draft, send
from app.core.auth.deps import require_login
from app.core.config import get_settings
from app.core.schema import MailDraft
from app.core.storage import repo

router = APIRouter()


class ApproveBody(BaseModel):
    acknowledge_warnings: bool = False


class SendInfo(BaseModel):
    mail_send_enabled: bool


def _draft(draft_id: int) -> MailDraft:
    d = repo.get_draft(draft_id)
    if d is None:
        raise HTTPException(status_code=404, detail="초안을 찾을 수 없습니다.")
    return d


@router.get("/send/info", response_model=SendInfo)
def send_info() -> SendInfo:
    return SendInfo(mail_send_enabled=get_settings().mail_send_enabled)


@router.post("/drafts/{draft_id}/gmail-draft", response_model=MailDraft)
def to_gmail(draft_id: int) -> MailDraft:
    d = _draft(draft_id)
    try:
        gid = gmail_draft.save_to_gmail(d.subject, d.final_body or d.ai_body)
    except gmail_draft.GmailNotReady as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    repo.update_draft(draft_id, gmail_draft_id=gid)
    return _draft(draft_id)


@router.post("/drafts/{draft_id}/approve", response_model=MailDraft)
def approve_draft(
    draft_id: int, body: ApproveBody, user: Annotated[str, Depends(require_login)]
) -> MailDraft:
    try:
        approve.approve(_draft(draft_id), user, body.acknowledge_warnings)
    except approve.ApproveError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return _draft(draft_id)


@router.post("/drafts/{draft_id}/send", response_model=MailDraft)
def send_draft(draft_id: int) -> MailDraft:
    try:
        send.send(_draft(draft_id))
    except send.SendRejected as e:
        raise HTTPException(status_code=e.status, detail=str(e)) from e
    return _draft(draft_id)
