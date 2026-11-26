"""B2-03 고객사별 안내 메일 초안 (DESIGN.md 10-2). 그 고객사 관련 항목만 넣는다.

- 본문에는 담당자 메일과 같은 기준으로 '확정된' 판단만 넣는다
  (담당자 [유지], 또는 확인 전이라도 신뢰도 높음 = section1_unfit.confirmed_ids).
- 확인 전 후보(신뢰도 중간)는 본문에 넣지 않고 warnings()로 초안 경고에만 남긴다.
  확인 전 후보만 있는 고객사에는 메일을 만들지 않는다 (pending_only).
- 예전에 만든 초안의 고객사가 다시 만들 때 대상에서 빠지면, 초안은 지우지 않고
  [대상 제외] 경고를 붙이고 승인을 푼다. 이 경고가 있으면 승인할 수 없다.
  다시 대상이 되면 초안을 다시 만들 때 경고가 사라진다.
- 섹션 2·3은 담당자 메일과 같다 (새 개정이 없는 주의 재안내 글 포함).
- 머리말·맺음말 문구는 config/b2/mail.json의 customer_body에서만 고친다.
"""

from typing import Any

from app.b2_mail.report import section1_unfit, section2_law, section3_tip
from app.b2_mail.report.service import ReportOut, config
from app.core.schema import MailDraft, SelectedItem


def related_items(out: ReportOut, customer_id: str) -> list[SelectedItem]:
    """본문에 넣을 항목: 그 고객사와의 판단이 확정된 것만."""
    return [i for i in out.report.section1_items if customer_id in section1_unfit.confirmed_ids(i)]


def pending_items(out: ReportOut, customer_id: str) -> list[SelectedItem]:
    """확인 전 후보: 관련으로 나왔지만 아직 확정되지 않은 항목 (본문에 넣지 않음)."""
    return [
        i
        for i in out.report.section1_items
        if customer_id in section1_unfit.matched_ids(i)
        and customer_id not in section1_unfit.confirmed_ids(i)
    ]


def recipients(out: ReportOut) -> list[str]:
    """안내 메일을 만들 고객사: 확정된 관련 항목이 1건 이상인 곳."""
    return sorted(
        {cid for i in out.report.section1_items for cid in section1_unfit.confirmed_ids(i)}
    )


def pending_only(out: ReportOut) -> list[str]:
    """확인 전 후보만 있어 메일을 만들지 않은 고객사."""
    candidates = {cid for i in out.report.section1_items for cid in section1_unfit.matched_ids(i)}
    return sorted(candidates - set(recipients(out)))


def body(
    out: ReportOut,
    customer_id: str,
    cfg: dict[str, Any] | None = None,
    reannounce: str | None = None,
) -> str:
    if cfg is None:
        from app.b2_mail.draft.service import mail_config  # service가 이 파일을 import한다

        cfg = mail_config()
    rcfg = config()
    t = rcfg["section_titles"]
    m = cfg["customer_body"]
    items = related_items(out, customer_id)
    s1 = section1_unfit.render(
        items, {}, rcfg["empty_section1_customer"], show_customers=False, customer_id=customer_id
    )
    s2 = section2_law.render(out.report.section2_items, rcfg["empty_section2"], reannounce)
    s3 = section3_tip.render(out.report.section3_tip, rcfg["empty_section3"])
    head = "\n".join([m["greeting"], m["intro"]])
    tail = "\n".join([m["notice"], m["closing"]])
    return "\n\n".join([head, f"{t[0]}\n{s1}", f"{t[1]}\n{s2}", f"{t[2]}\n{s3}", tail])


DROPPED_MARK = "[대상 제외]"  # 이 표시가 붙은 초안은 승인할 수 없다 (send/approve.py)


def dropped_warning(cfg: dict[str, Any]) -> str:
    return f"{DROPPED_MARK} {cfg['customer_warnings']['dropped']}"


def is_dropped(d: MailDraft) -> bool:
    """예전에 만들었지만 다시 만들 때 안내 대상에서 빠진 고객사 초안."""
    return any(w.startswith(DROPPED_MARK) for w in d.warnings)


def warnings(out: ReportOut, customer_id: str, cfg: dict[str, Any]) -> list[str]:
    count = len(pending_items(out, customer_id))
    if not count:
        return []
    return [cfg["customer_warnings"]["pending_items"].format(count=count)]
