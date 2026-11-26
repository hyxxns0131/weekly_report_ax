"""B2-05 담당자 승인. 승인자는 로그인한 사용자 이름 (AGENTS.md 0-6-1)."""

from app.b2_mail.draft.customer import is_dropped
from app.core.schema import MailDraft
from app.core.storage import repo


class ApproveError(Exception):
    pass


def approve(d: MailDraft, user: str, acknowledge_warnings: bool) -> None:
    if d.status == "sent":
        raise ApproveError("이미 발송한 초안입니다.")
    if is_dropped(d):
        # 경고 확인 체크로도 넘길 수 없다 (B2-03: 대상에서 빠진 고객사 초안)
        raise ApproveError("이번 주 안내 대상에서 빠진 고객사 초안이라 승인할 수 없습니다.")
    if d.warnings and not acknowledge_warnings:
        raise ApproveError("경고가 있습니다. 경고를 확인했다고 체크한 뒤 승인해 주세요.")
    repo.approve_draft(d.id, user)
