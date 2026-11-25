"""B2-02~04 메일 초안 만들기. 담당자용 1통 + 관련 고객사마다 1통.

다시 만들어도 final_body는 그대로 두고 ai_body만 바꾼다 (AGENTS.md 5-6).
"""

import json
from typing import Any

from app.b2_mail.draft import checks, customer, staff
from app.b2_mail.report import section1_unfit
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
    sbody = staff.body(out, issues)
    drafts = [
        repo.upsert_draft(
            MailDraft(
                id=0,
                run_id=run_id,
                kind=MailKind.staff_summary,
                subject=staff.subject(out, cfg["subject_staff"]),
                ai_body=sbody,
                warnings=checks.check(sbody, ws, []),
            )
        )
    ]
    related = sorted(
        {cid for i in out.report.section1_items for cid in section1_unfit.matched_ids(i)}
    )
    for cid in related:
        cbody = customer.body(out, cid)
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
                    warnings=checks.check(cbody, ws, others),
                )
            )
        )
    return drafts
