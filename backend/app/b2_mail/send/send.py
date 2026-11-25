"""B2-05 발송. 승인 기록(승인자·시각)이 없는 초안은 거부한다(409). 자동·예약·일괄 발송 없음."""

from app.core.config import get_settings
from app.core.schema import MailDraft, MailStatus


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
    raise SendRejected(503, "구글 연결(C-05) 전이라 발송할 수 없습니다.")
