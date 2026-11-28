"""B2-05 발송. 자동·예약·일괄 발송 없음: 담당자가 초안 하나씩 [발송]을 눌러야만 나간다.

막는 순서 (AGENTS.md 0-7):
1. 승인 기록(승인자·시각)이 없으면 409
2. MAIL_SEND_ENABLED=false면 403
3. 받는 사람이 없으면 409
그다음 승인한 본문으로 Gmail 초안을 맞춘 뒤(저장 뒤 본문이 바뀌었어도 승인한 글이 나가게) 보낸다.
보내면 상태를 '발송'으로 바꾸고 보낸 시각·Gmail 메일 ID를 남긴다.
이후 고치기·다시 만들기는 막힌다(B2-04).
"""

from app.b2_mail.send import gmail_draft
from app.core.config import get_settings
from app.core.schema import MailDraft, MailKind, MailStatus
from app.core.storage import repo
from app.core.storage.local_db import now_kst

NO_STAFF_TO = (
    "받는 사람이 설정되지 않았습니다. .env의 GMAIL_STAFF_TO를 확인해 주세요(KHS). "
    "[Gmail 초안함에 저장] 뒤 Gmail에서 받는 사람을 넣어 보내도 됩니다."
)
NO_CUSTOMER_TO = (
    "고객사 메일 주소는 아직 연결 전입니다(SAMC 미팅 뒤 결정). "
    "[Gmail 초안함에 저장] 뒤 Gmail에서 받는 사람을 넣어 보내 주세요."
)


class SendRejected(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status


def send(d: MailDraft) -> str:
    if d.status != MailStatus.approved or not (d.approved_by and d.approved_at):
        raise SendRejected(409, "담당자 승인 전에는 발송할 수 없습니다.")
    if not get_settings().mail_send_enabled:
        raise SendRejected(
            403, "발송 꺼짐(MAIL_SEND_ENABLED=false). 승인한 본문을 복사해 보내 주세요."
        )
    if not gmail_draft.recipients(d):
        raise SendRejected(409, NO_STAFF_TO if d.kind == MailKind.staff_summary else NO_CUSTOMER_TO)
    try:
        gid = gmail_draft.save_to_gmail(d, recreate_if_missing=False)
        repo.update_draft(d.id, gmail_draft_id=gid)
        message_id = gmail_draft.send_gmail_draft(gid)
    except gmail_draft.GmailMissing as e:
        raise SendRejected(409, str(e)) from e
    except gmail_draft.GmailNotReady as e:
        raise SendRejected(503, str(e)) from e
    except gmail_draft.GmailFailed as e:
        raise SendRejected(502, str(e)) from e
    repo.update_draft(
        d.id, status=MailStatus.sent.value, sent_at=now_kst(), gmail_message_id=message_id
    )
    return message_id
