"""B1-08 관련/무관/검토 필요 분류.

순서: LLM 분류(준비되면) → 없으면 키워드 규칙. 재실행 때 final_*는 덮어쓰지 않는다.
"""

from app.b1_select.classify import keyword_rules, llm_classifier
from app.core.schema import Selection
from app.core.storage import repo


def classify_item(item_id: str, title: str, body: str) -> Selection:
    sel = llm_classifier.classify(item_id, title, body)
    if sel is None:
        label, category, reason, quote = keyword_rules.classify(title, body)
        sel = Selection(
            item_id=item_id,
            ai_label=label,
            ai_category=category,
            ai_reason=reason,
            evidence_quote=quote,
        )
    old = repo.get_selection(item_id)
    if old:
        sel.final_label = old.final_label
        sel.final_category = old.final_category
        sel.reviewed_by = old.reviewed_by
        sel.reviewed_at = old.reviewed_at
    repo.save_selection(sel, prompt_version="keyword_rules")
    return sel


def run_classify(run_id: int) -> None:
    for raw in repo.list_raw(run_id):
        classify_item(raw.id, raw.title, raw.body)
