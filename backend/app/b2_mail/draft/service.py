"""B2-02~04 메일 초안 만들기. 담당자용 1통 + 관련 고객사마다 1통.

다시 만들어도 final_body는 그대로 두고 ai_body만 바꾼다 (AGENTS.md 5-6).
"""

import json
from typing import Any

from app.b2_mail.draft import checks, customer, staff
from app.b2_mail.report.service import build
from app.core.config import REPO_ROOT
from app.core.schema import Crosscheck, MailDraft, MailKind
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
    sbody = staff.body(out, cfg)
    swarn = checks.check(sbody, ws, []) + staff.warnings(out, issues, cfg)
    skipped = customer.pending_only(out)
    if skipped:
        swarn.append(cfg["customer_warnings"]["pending_customers"].format(count=len(skipped)))
    drafts = [
        repo.upsert_draft(
            MailDraft(
                id=0,
                run_id=run_id,
                kind=MailKind.staff_summary,
                subject=staff.subject(out, cfg["subject_staff"]),
                ai_body=sbody,
                warnings=swarn,
            )
        )
    ]
    for cid in customer.recipients(out):
        cbody = customer.body(out, cid, cfg, reannounce)
        others = [n for k, n in names.items() if k != cid]
        drafts.append(
            repo.upsert_draft(
                MailDraft(
                    id=0,
                    run_id=run_id,
                    kind=MailKind.customer,
                    customer_id=cid,
                    subject=cfg["subject_customer"].format(week_label=out.report.week_label),
                    ai_body=cbody,
                    warnings=checks.check(cbody, ws, others) + customer.warnings(out, cid, cfg),
                )
            )
        )
    drafts += _mark_dropped(run_id, set(customer.recipients(out)), cfg)
    return drafts


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
