"""공통 스키마 (C-01, AGENTS.md 5-5). KHS 고정 파일: 바꿀 일이 있으면 PR "변경 요청"에 적는다.

`frontend/lib/types/core.ts`와 같은 모양으로 유지한다.
날짜는 date(YYYY-MM-DD), 시각은 KST datetime.
"""

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Source(StrEnum):
    impfood_unfit = "impfood_unfit"
    impfood_inspection = "impfood_inspection"
    impfood_law_policy = "impfood_law_policy"
    mfds_notice = "mfds_notice"
    gyeongin_newsletter = "gyeongin_newsletter"
    law_api = "law_api"
    gmail_inbox = "gmail_inbox"
    manual = "manual"


class Label(StrEnum):
    relevant = "relevant"
    irrelevant = "irrelevant"
    review_needed = "review_needed"


class Category(StrEnum):
    unfit = "unfit"
    inspection_order = "inspection_order"
    law_change = "law_change"
    policy_news = "policy_news"
    other = "other"


class MatchRule(StrEnum):
    maker = "maker"
    hs_code = "hs_code"
    origin_food_type = "origin_food_type"
    food_type_parent = "food_type_parent"
    food_type_only = "food_type_only"


class Confidence(StrEnum):
    high = "high"
    medium = "medium"


class Crosscheck(StrEnum):
    match = "match"
    api_only = "api_only"
    notice_only = "notice_only"
    not_checked = "not_checked"


class ReportStatus(StrEnum):
    draft = "draft"
    confirmed = "confirmed"


class MailKind(StrEnum):
    staff_summary = "staff_summary"
    customer = "customer"


class MailStatus(StrEnum):
    draft = "draft"
    approved = "approved"
    sent = "sent"


class RawItem(BaseModel):
    """원문 항목."""

    id: str
    run_id: int
    source: Source
    title: str
    body: str
    posted_at: date | None = None
    url: str | None = None
    collected_at: datetime


class Selection(BaseModel):
    """선별 결과. final_*가 있으면 그것을, 없으면 ai_*를 쓴다."""

    item_id: str
    ai_label: Label
    final_label: Label | None = None
    ai_category: Category
    final_category: Category | None = None
    ai_reason: str = ""
    evidence_quote: str = ""
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None


class ExtractedInfo(BaseModel):
    """추출 정보. 못 찾으면 None → 화면 "확인 필요"."""

    item_id: str
    product_name_ko: str | None = None
    product_name_en: str | None = None
    food_type_raw: str | None = None
    food_type_std: str | None = None
    origin_country: str | None = None
    export_country: str | None = None
    maker: str | None = None
    hs_code: str | None = None
    violation: str | None = None
    action: str | None = None
    office: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    edited_fields: list[str] = Field(default_factory=list)


class CustomerMatch(BaseModel):
    """고객사 판단 결과. customer_id는 가명 ID(C001 등)."""

    item_id: str
    customer_id: str
    ai_matched: bool
    final_matched: bool | None = None
    rule: MatchRule
    confidence: Confidence
    reason: str


class LawChange(BaseModel):
    """법령 개정 항목. 법령명·번호·날짜·조항은 원문에서만 채우고 없으면 None."""

    id: str
    law_name: str | None = None
    kind: str | None = None  # 법령 / 행정규칙
    change_type: str | None = None  # 제정, 일부개정, 전부개정, 폐지
    number: str | None = None
    promulgated_at: date | None = None
    effective_at: date | None = None
    articles: str | None = None
    ai_summary: str | None = None
    final_summary: str | None = None
    source_url: str | None = None
    crosscheck: Crosscheck = Crosscheck.not_checked
    crosscheck_note: str = ""
    related_food_types: list[str] = Field(default_factory=list)


class SelectedItem(BaseModel):
    """b1 → b2: 원문 + 선별 + 추출 + 고객사 판단을 한 항목으로 묶은 것."""

    raw: RawItem
    selection: Selection
    extracted: ExtractedInfo | None = None
    matches: list[CustomerMatch] = Field(default_factory=list)


class WeeklySelection(BaseModel):
    """b1 → b2 인터페이스 (GET /api/b1/runs/{run_id}/result, AGENTS.md 5-6)."""

    run_id: int
    period_start: date
    period_end: date
    week_label: str
    items: list[SelectedItem] = Field(default_factory=list)
    law_changes: list[LawChange] = Field(default_factory=list)


class WeeklyReport(BaseModel):
    """주간 보고서. section1_items는 SelectedItem, section2_items는 LawChange."""

    run_id: int
    period_start: date
    period_end: date
    week_label: str
    section1_items: list[SelectedItem] = Field(default_factory=list)
    section2_items: list[LawChange] = Field(default_factory=list)
    section3_tip: str | None = None
    status: ReportStatus = ReportStatus.draft


class MailDraft(BaseModel):
    """메일 초안. 발송은 approved_by·approved_at이 있을 때만 (AGENTS.md 0-7)."""

    id: int
    run_id: int
    kind: MailKind
    customer_id: str | None = None
    subject: str
    ai_body: str
    final_body: str | None = None
    warnings: list[str] = Field(default_factory=list)
    status: MailStatus = MailStatus.draft
    approved_by: str | None = None
    approved_at: datetime | None = None
    sent_at: datetime | None = None
    gmail_draft_id: str | None = None
    gmail_message_id: str | None = None


class EvalResult(BaseModel):
    """과거 보고서 대비 검증 결과."""

    run_id: int
    golden_week: str
    selection_recall: float | None = None
    selection_precision: float | None = None
    match_recall: float | None = None
    match_precision: float | None = None
    review_needed_ratio: float | None = None
    missed_items: list[str] = Field(default_factory=list)
    extra_items: list[str] = Field(default_factory=list)
    wrong_matches: list[str] = Field(default_factory=list)
    elapsed_sec: float | None = None
