"""B2-05 Gmail 초안함 저장과 Gmail 연결.

- 구글 인증은 core/gmail_client.py(KHS)의 get_credentials([GMAIL_COMPOSE])만 쓴다.
  토큰이 없거나 Gmail 권한이 없으면 GmailNotReady로 멈춘다(아무것도 저장·발송하지 않음).
- 본문은 담당자가 고친 본문(final_body)이 있으면 그것, 없으면 AI 본문.
- mail.json의 body_format이 "html"이면 일반 글 + HTML(표)을 함께 넣는다. 메일 프로그램이 고른다.
- 받는 사람: 담당자용은 .env의 GMAIL_STAFF_TO(쉼표로 여러 명).
  고객사 메일 주소는 아직 없음(미팅 뒤).
- 이미 저장한 초안이면 새로 만들지 않고 같은 Gmail 초안을 고쳐 쓴다(중복 방지).
- 발송(drafts.send)은 여기서 하지 않는다. send.py가 승인·발송 스위치를 확인한 뒤에만 부른다.
"""

import base64
from email.message import EmailMessage
from email.policy import SMTP
from typing import Any

from app.b2_mail.draft.service import mail_config
from app.b2_mail.send import mail_html
from app.core.config import get_settings
from app.core.schema import MailDraft, MailKind, MailStatus

NOT_READY = (
    "Gmail 권한이 없습니다. 구글 로그인에 Gmail 권한(gmail.compose)이 있어야 합니다. "
    "KHS에게 확인해 주세요. 지금은 본문을 [복사]해 Gmail에 붙여 넣어 주세요."
)


class GmailNotReady(Exception):
    """구글 로그인·Gmail 권한이 없음 (503)."""


class GmailFailed(Exception):
    """Gmail이 요청을 거부했거나 연결이 끊김 (502)."""


class GmailLocked(Exception):
    """이미 발송한 초안 (409)."""


def gmail_service() -> Any:
    """Gmail API 클라이언트. 테스트에서는 이 함수를 가짜로 바꾼다."""
    from googleapiclient.discovery import build

    from app.core.gmail_client import GMAIL_COMPOSE, GoogleAuthError, get_credentials

    try:
        creds = get_credentials([GMAIL_COMPOSE])
    except GoogleAuthError as e:
        raise GmailNotReady(f"{NOT_READY} (사유: {e})") from e
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def body_of(d: MailDraft) -> str:
    return d.final_body if d.final_body is not None else d.ai_body


def recipients(d: MailDraft) -> list[str]:
    """받는 사람 주소. 값은 화면·로그에 내보내지 않는다(개수만)."""
    if d.kind == MailKind.staff_summary:
        raw = get_settings().gmail_staff_to
        return [a.strip() for a in raw.split(",") if a.strip()]
    return []  # 고객사 메일 주소: 드라이브 고객사 목록 연결 전 (SAMC 미팅 뒤 결정)


def build_message(d: MailDraft) -> EmailMessage:
    cfg = mail_config()
    msg = EmailMessage(policy=SMTP)
    msg["Subject"] = d.subject
    to = recipients(d)
    if to:
        msg["To"] = ", ".join(to)
    sender = get_settings().gmail_sender
    if sender:
        msg["From"] = sender
    body = body_of(d)
    msg.set_content(body)
    if cfg.get("body_format", "html") == "html":
        msg.add_alternative(mail_html.to_html(body), subtype="html")
    return msg


def _raw(d: MailDraft) -> dict[str, Any]:
    data = base64.urlsafe_b64encode(build_message(d).as_bytes()).decode("ascii")
    return {"message": {"raw": data}}


def _status_of(e: Exception) -> int | None:
    resp = getattr(e, "resp", None)
    status = getattr(resp, "status", None)
    return int(status) if status is not None else None


def _call(fn: Any) -> Any:
    """Gmail 요청 하나. 실패는 GmailFailed로 바꿔 화면에 이유를 알린다."""
    try:
        return fn.execute()
    except (GmailNotReady, GmailLocked):
        raise
    except Exception as e:  # HttpError·연결 오류 모두: 저장·발송 안 됨을 그대로 알린다
        status = _status_of(e)
        if status in (401, 403):
            raise GmailNotReady(f"{NOT_READY} (Gmail 응답 {status})") from e
        code = f"Gmail 응답 {status}" if status else type(e).__name__
        raise GmailFailed(f"Gmail 요청이 실패했습니다 ({code}). 잠시 뒤 다시 눌러 주세요.") from e


def save_to_gmail(d: MailDraft) -> str:
    """Gmail 초안함에 저장하고 Gmail 초안 ID를 돌려준다. 있던 초안이면 내용을 바꾼다."""
    if d.status == MailStatus.sent:
        raise GmailLocked("이미 발송한 초안은 Gmail 초안함에 다시 저장할 수 없습니다.")
    drafts = gmail_service().users().drafts()
    if d.gmail_draft_id:
        try:
            got = _call(drafts.update(userId="me", id=d.gmail_draft_id, body=_raw(d)))
            return str(got["id"])
        except GmailFailed as e:
            # 담당자가 Gmail에서 초안을 지웠으면(404) 새로 만든다
            if _status_of(e.__cause__ or e) != 404:
                raise
    got = _call(drafts.create(userId="me", body=_raw(d)))
    return str(got["id"])


def send_gmail_draft(gmail_draft_id: str) -> str:
    """승인·발송 스위치 확인을 마친 Gmail 초안을 보낸다(send.py에서만 부름). 보낸 메일 ID."""
    drafts = gmail_service().users().drafts()
    got = _call(drafts.send(userId="me", body={"id": gmail_draft_id}))
    return str(got["id"])
