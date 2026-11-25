"""B2-03 고객사별 안내 메일 초안 (DESIGN.md 10-2). 그 고객사 관련 항목만 넣는다."""

from app.b2_mail.report import section1_unfit, section2_law, section3_tip
from app.b2_mail.report.service import ReportOut, config


def related_items(out: ReportOut, customer_id: str) -> list:
    return [i for i in out.report.section1_items if customer_id in section1_unfit.matched_ids(i)]


def body(out: ReportOut, customer_id: str) -> str:
    cfg = config()
    t = cfg["section_titles"]
    items = related_items(out, customer_id)
    s1 = section1_unfit.render(items, {}, cfg["empty_section1_customer"], show_customers=False)
    s2 = section2_law.render(out.report.section2_items, cfg["empty_section2"])
    s3 = section3_tip.render(out.report.section3_tip, cfg["empty_section3"])
    return (
        "안녕하세요, 관세법인 SAMC입니다.\n"
        "이번 주 귀사 수입 품목과 관련된 검역 정보를 안내드립니다.\n\n"
        f"{t[0]}\n{s1}\n\n{t[1]}\n{s2}\n\n{t[2]}\n{s3}\n\n"
        "본 안내는 공개된 정보를 바탕으로 작성되었습니다. 세부 적용은 담당자와 확인 부탁드립니다.\n"
        "감사합니다.\n관세법인 SAMC 통관검역팀 드림"
    )
