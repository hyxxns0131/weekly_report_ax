"""B2-02~04 메일 초안 만들기. 담당자용 1통 + 관련 고객사마다 1통.

다시 만들어도 final_body는 그대로 두고 ai_body만 바꾼다 (AGENTS.md 5-6).
"""

import json
from collections.abc import Callable
from typing import Any

from app.b2_mail.draft import checks, customer, history, staff
from app.b2_mail.input import B1Unavailable, load_customer_names, load_selection
from app.b2_mail.report.service import build
from app.core.config import REPO_ROOT
from app.core.schema import Crosscheck, MailDraft, MailKind, MailStatus, WeeklySelection
from app.core.storage import repo

MAIL_JSON = REPO_ROOT / "backend" / "config" / "b2" / "mail.json"


def mail_config() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(MAIL_JSON.read_text(encoding="utf-8"))
    return data


def generate(run_id: int, token: str | None, source: str = "api") -> list[MailDraft]:
    out, ws = build(run_id, token, source)
    cfg = mail_config()
    names = out.customer_names
    issues = sum(
        1 for c in ws.law_changes if c.crosscheck in (Crosscheck.api_only, Crosscheck.notice_only)
    )
    reannounce = (repo.get_report(run_id) or {}).get("reannounce")
    prev = {(str(d.kind), d.customer_id): d for d in repo.list_drafts(run_id)}
    sbody = staff.body(out, cfg)
    sextra = staff.warnings(out, issues, cfg)
    skipped = customer.pending_only(out)
    if skipped:
        sextra.append(cfg["customer_warnings"]["pending_customers"].format(count=len(skipped)))
    staff_draft = MailDraft(
        id=0,
        run_id=run_id,
        kind=MailKind.staff_summary,
        subject=staff.subject(out, cfg["subject_staff"]),
        ai_body=sbody,
    )
    drafts = [_save(staff_draft, sextra, _checker(ws, []), prev, cfg)]
    for cid in customer.recipients(out):
        others = [n for k, n in names.items() if k != cid]
        cdraft = MailDraft(
            id=0,
            run_id=run_id,
            kind=MailKind.customer,
            customer_id=cid,
            subject=cfg["subject_customer"].format(week_label=out.report.week_label),
            ai_body=customer.body(out, cid, cfg, reannounce),
        )
        extra = customer.warnings(out, cid, cfg)
        drafts.append(_save(cdraft, extra, _checker(ws, others), prev, cfg))
    drafts += _mark_dropped(run_id, set(customer.recipients(out)), cfg)
    return drafts


def _checker(ws: WeeklySelection, others: list[str]) -> Callable[[str], list[str]]:
    return lambda body: checks.check(body, ws, others)


def _save(
    new: MailDraft,
    extra: list[str],
    check: Callable[[str], list[str]],
    prev: dict[tuple[str, str | None], MailDraft],
    cfg: dict[str, Any],
) -> MailDraft:
    """초안 저장 (B2-04 규칙, AGENTS.md 5-6).

    - 담당자가 고친 본문(final_body)이 있으면 그 본문을 검사한다. 실제로 나갈 글이라서.
    - 고친 본문이 있는데 AI 본문이 바뀌면 "AI 초안 바뀜"을 단다. 담당자가 다시 저장할 때까지 남긴다.
    - 고친 본문 없이 AI 본문 그대로 승인했는데 AI 본문이 바뀌면 승인을 푼다.
    - 발송한 초안은 보낸 기록이라 건드리지 않는다 (고치기와 같이 다시 만들기도 막는다).
    """
    old = prev.get((str(new.kind), new.customer_id))
    if old is not None and old.status == MailStatus.sent:
        return old
    edited = old is not None and old.final_body is not None
    body = old.final_body if old is not None and old.final_body is not None else new.ai_body
    warnings = check(body) + extra
    note = cfg["draft_warnings"]
    ai_changed = old is not None and old.ai_body != new.ai_body
    if edited and old is not None and (ai_changed or note["ai_changed"] in old.warnings):
        warnings.append(note["ai_changed"])
    revoke = old is not None and not edited and ai_changed and old.status == MailStatus.approved
    if revoke:
        warnings.append(note["approval_revoked"])
    saved = repo.upsert_draft(new.model_copy(update={"warnings": warnings}))
    if revoke:
        repo.revoke_approval(saved.id)
        got = repo.get_draft(saved.id)
        assert got is not None
        return got
    return saved


class DraftNotFound(Exception):
    pass


class DraftLocked(Exception):
    pass


def save_edit(
    draft_id: int, body: str, user: str, token: str | None, source: str = "api"
) -> MailDraft:
    """B2-04 담당자 수정 저장.

    - 지금 본문과 같으면 아무것도 하지 않는다 (이력·승인 해제 없음).
    - 발송한 초안은 고칠 수 없다. 승인한 초안을 고치면 승인을 푼다 (RULES.md 8-5).
    - 고친 본문으로 경고를 다시 검사하고, "AI 초안 바뀜" 표시는 지운다(담당자가 확인했으므로).
    """
    d = repo.get_draft(draft_id)
    if d is None:
        raise DraftNotFound("초안을 찾을 수 없습니다.")
    if d.status == MailStatus.sent:
        raise DraftLocked("이미 발송한 초안은 고칠 수 없습니다.")
    current = d.final_body if d.final_body is not None else d.ai_body
    if body == current:
        return d
    cfg = mail_config()
    note = cfg["draft_warnings"]
    rest = [
        w
        for w in checks.other_warnings(d.warnings)
        if w not in (note["ai_changed"], note["approval_revoked"])
    ]
    try:
        ws = load_selection(d.run_id, token, source)
        names = load_customer_names(token, source)
        others = [n for k, n in names.items() if k != d.customer_id] if d.customer_id else []
        found = checks.check(body, ws, others)
    except B1Unavailable:
        found = [checks.not_checked("b1 결과를 읽지 못함")]
    if d.status == MailStatus.approved:
        repo.revoke_approval(draft_id)
    repo.update_draft(draft_id, final_body=body, warnings=found + rest)
    history.add(draft_id, user, body)
    got = repo.get_draft(draft_id)
    assert got is not None
    return got


def _mark_dropped(run_id: int, recipients: set[str], cfg: dict[str, Any]) -> list[MailDraft]:
    """예전 고객사 초안 중 이번에 대상에서 빠진 것: 지우지 않고 [대상 제외] 경고 + 승인 풀기.

    발송한 초안은 기록이라 그대로 둔다. 화면에서 보이도록 결과 목록에도 넣는다.
    """
    marked: list[MailDraft] = []
    note = customer.dropped_warning(cfg)
    for d in repo.list_drafts(run_id):
        if d.kind != MailKind.customer or d.customer_id in recipients or d.status == "sent":
            continue
        if not customer.is_dropped(d):
            repo.update_draft(d.id, warnings=[note, *d.warnings])
        if d.status == "approved":
            repo.revoke_approval(d.id)
        got = repo.get_draft(d.id)
        if got:
            marked.append(got)
    return marked
