"""로컬 SQLite 읽기·쓰기 함수 (C-04, KHS). 담당자 모듈은 이 함수들로만 DB를 쓴다.

테이블 정의는 schema.sql(KHS 고정). 목록 칸은 JSON 문자열로 저장한다.
필요한 함수가 없으면 PR "변경 요청"에 적는다.
"""

import json
from datetime import datetime
from typing import Any

from app.core.schema import (
    CustomerMatch,
    EvalResult,
    ExtractedInfo,
    LawChange,
    MailDraft,
    RawItem,
    Selection,
)
from app.core.storage.local_db import connect, now_kst


def _now() -> str:
    return now_kst().isoformat(timespec="seconds")


def _iso(value: Any) -> Any:
    return value.isoformat() if hasattr(value, "isoformat") else value


# ── 원문 항목 ─────────────────────────────────────────
def save_raw(item: RawItem) -> None:
    d = item.model_dump()
    with connect() as c:
        c.execute(
            "INSERT OR REPLACE INTO raw_item (id, run_id, source, title, body, posted_at, url,"
            " collected_at) VALUES (?,?,?,?,?,?,?,?)",
            (
                d["id"],
                d["run_id"],
                str(d["source"]),
                d["title"],
                d["body"],
                _iso(d["posted_at"]),
                d["url"],
                _iso(d["collected_at"]),
            ),
        )


def list_raw(run_id: int) -> list[RawItem]:
    with connect() as c:
        rows = c.execute(
            "SELECT * FROM raw_item WHERE run_id = ? ORDER BY posted_at DESC, id", (run_id,)
        ).fetchall()
    return [RawItem.model_validate(dict(r)) for r in rows]


def get_raw(item_id: str) -> RawItem | None:
    with connect() as c:
        r = c.execute("SELECT * FROM raw_item WHERE id = ?", (item_id,)).fetchone()
    return RawItem.model_validate(dict(r)) if r else None


# ── 선별 ─────────────────────────────────────────────
def save_selection(sel: Selection, prompt_version: str | None = None) -> None:
    d = sel.model_dump()
    with connect() as c:
        c.execute(
            "INSERT OR REPLACE INTO selection (item_id, ai_label, final_label, ai_category,"
            " final_category, ai_reason, evidence_quote, prompt_version, reviewed_by, reviewed_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                d["item_id"],
                str(d["ai_label"]),
                d["final_label"] and str(d["final_label"]),
                str(d["ai_category"]),
                d["final_category"] and str(d["final_category"]),
                d["ai_reason"],
                d["evidence_quote"],
                prompt_version,
                d["reviewed_by"],
                _iso(d["reviewed_at"]),
            ),
        )


def get_selection(item_id: str) -> Selection | None:
    with connect() as c:
        r = c.execute("SELECT * FROM selection WHERE item_id = ?", (item_id,)).fetchone()
    return Selection.model_validate(dict(r)) if r else None


# ── 추출 ─────────────────────────────────────────────
_EXTRACT_FIELDS = [
    "product_name_ko",
    "product_name_en",
    "food_type_raw",
    "food_type_std",
    "origin_country",
    "export_country",
    "maker",
    "hs_code",
    "violation",
    "action",
    "office",
    "period_start",
    "period_end",
]


def save_extracted(info: ExtractedInfo) -> None:
    d = info.model_dump()
    cols = ["item_id", *_EXTRACT_FIELDS, "edited_fields"]
    vals = [d["item_id"], *[_iso(d[f]) for f in _EXTRACT_FIELDS], json.dumps(d["edited_fields"])]
    with connect() as c:
        c.execute(
            f"INSERT OR REPLACE INTO extracted_info ({','.join(cols)})"
            f" VALUES ({','.join('?' * len(cols))})",
            vals,
        )


def get_extracted(item_id: str) -> ExtractedInfo | None:
    with connect() as c:
        r = c.execute("SELECT * FROM extracted_info WHERE item_id = ?", (item_id,)).fetchone()
    if not r:
        return None
    d = dict(r)
    d["edited_fields"] = json.loads(d["edited_fields"])
    return ExtractedInfo.model_validate(d)


# ── 고객사 판단 ───────────────────────────────────────
def save_match(m: CustomerMatch) -> None:
    with connect() as c:
        c.execute(
            "INSERT OR REPLACE INTO customer_match (item_id, customer_id, ai_matched,"
            " final_matched, rule, confidence, reason) VALUES (?,?,?,?,?,?,?)",
            (
                m.item_id,
                m.customer_id,
                int(m.ai_matched),
                None if m.final_matched is None else int(m.final_matched),
                str(m.rule),
                str(m.confidence),
                m.reason,
            ),
        )


def list_matches(run_id: int) -> list[CustomerMatch]:
    with connect() as c:
        rows = c.execute(
            "SELECT m.* FROM customer_match m JOIN raw_item r ON r.id = m.item_id"
            " WHERE r.run_id = ? ORDER BY m.item_id, m.customer_id",
            (run_id,),
        ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["ai_matched"] = bool(d["ai_matched"])
        d["final_matched"] = None if d["final_matched"] is None else bool(d["final_matched"])
        out.append(CustomerMatch.model_validate(d))
    return out


def delete_ai_matches(item_id: str) -> None:
    """재실행 전에 담당자가 정하지 않은 판단만 지운다 (final_* 보존)."""
    with connect() as c:
        c.execute(
            "DELETE FROM customer_match WHERE item_id = ? AND final_matched IS NULL", (item_id,)
        )


# ── 법령 개정 ─────────────────────────────────────────
_LAW_FIELDS = [
    "law_name",
    "kind",
    "change_type",
    "number",
    "promulgated_at",
    "effective_at",
    "articles",
    "ai_summary",
    "final_summary",
    "source_url",
    "crosscheck",
    "crosscheck_note",
]


def save_law(run_id: int, law: LawChange) -> None:
    d = law.model_dump()
    cols = ["id", "run_id", *_LAW_FIELDS, "related_food_types"]
    vals = [
        d["id"],
        run_id,
        *[str(d[f]) if f == "crosscheck" else _iso(d[f]) for f in _LAW_FIELDS],
        json.dumps(d["related_food_types"], ensure_ascii=False),
    ]
    with connect() as c:
        c.execute(
            f"INSERT OR REPLACE INTO law_change_work ({','.join(cols)})"
            f" VALUES ({','.join('?' * len(cols))})",
            vals,
        )


def _law_from_row(r: Any) -> LawChange:
    d = dict(r)
    d["related_food_types"] = json.loads(d["related_food_types"])
    return LawChange.model_validate(d)


def list_law(run_id: int) -> list[LawChange]:
    with connect() as c:
        rows = c.execute(
            "SELECT * FROM law_change_work WHERE run_id = ? ORDER BY effective_at DESC", (run_id,)
        ).fetchall()
    return [_law_from_row(r) for r in rows]


def get_law(law_id: str) -> tuple[int, LawChange] | None:
    with connect() as c:
        r = c.execute(
            "SELECT * FROM law_change_work WHERE id = ? ORDER BY run_id DESC LIMIT 1", (law_id,)
        ).fetchone()
    return (int(r["run_id"]), _law_from_row(r)) if r else None


def reported_law_ids() -> set[str]:
    with connect() as c:
        return {r[0] for r in c.execute("SELECT law_id FROM reported_law").fetchall()}


def mark_law_reported(run_id: int, law: LawChange) -> None:
    with connect() as c:
        c.execute(
            "INSERT OR IGNORE INTO reported_law (law_id, law_name, effective_at, run_id,"
            " reported_at) VALUES (?,?,?,?,?)",
            (law.id, law.law_name, _iso(law.effective_at), run_id, _now()),
        )


# ── 주간 보고서 ───────────────────────────────────────
def save_report(run_id: int, body: dict[str, Any], status: str = "draft") -> None:
    with connect() as c:
        c.execute(
            "INSERT OR REPLACE INTO weekly_report (run_id, body_json, status, updated_at)"
            " VALUES (?,?,?,?)",
            (run_id, json.dumps(body, ensure_ascii=False, default=str), status, _now()),
        )


def get_report(run_id: int) -> dict[str, Any] | None:
    with connect() as c:
        r = c.execute("SELECT body_json FROM weekly_report WHERE run_id = ?", (run_id,)).fetchone()
    if not r:
        return None
    data: dict[str, Any] = json.loads(r[0])
    return data


# ── 메일 초안 ─────────────────────────────────────────
def _draft_from_row(c: Any, r: Any) -> MailDraft:
    d = dict(r)
    d["warnings"] = json.loads(d["warnings"])
    a = c.execute(
        "SELECT approved_by, approved_at FROM mail_approval WHERE draft_id = ?"
        " AND revoked_at IS NULL ORDER BY id DESC LIMIT 1",
        (d["id"],),
    ).fetchone()
    d["approved_by"], d["approved_at"] = (a[0], a[1]) if a else (None, None)
    return MailDraft.model_validate(d)


def upsert_draft(d: MailDraft) -> MailDraft:
    """같은 run·kind·customer 초안이 있으면 ai_body만 바꾸고 final_body는 그대로 둔다."""
    with connect() as c:
        r = c.execute(
            "SELECT id FROM mail_draft WHERE run_id = ? AND kind = ? AND"
            " IFNULL(customer_id, '') = IFNULL(?, '')",
            (d.run_id, str(d.kind), d.customer_id),
        ).fetchone()
        if r:
            c.execute(
                "UPDATE mail_draft SET subject = ?, ai_body = ?, warnings = ?, updated_at = ?"
                " WHERE id = ?",
                (d.subject, d.ai_body, json.dumps(d.warnings, ensure_ascii=False), _now(), r[0]),
            )
            draft_id = int(r[0])
        else:
            cur = c.execute(
                "INSERT INTO mail_draft (run_id, kind, customer_id, subject, ai_body, final_body,"
                " warnings, status, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    d.run_id,
                    str(d.kind),
                    d.customer_id,
                    d.subject,
                    d.ai_body,
                    None,
                    json.dumps(d.warnings, ensure_ascii=False),
                    "draft",
                    _now(),
                ),
            )
            draft_id = int(cur.lastrowid or 0)
    got = get_draft(draft_id)
    assert got is not None
    return got


def list_drafts(run_id: int) -> list[MailDraft]:
    with connect() as c:
        rows = c.execute(
            "SELECT * FROM mail_draft WHERE run_id = ? ORDER BY kind DESC, customer_id", (run_id,)
        ).fetchall()
        return [_draft_from_row(c, r) for r in rows]


def get_draft(draft_id: int) -> MailDraft | None:
    with connect() as c:
        r = c.execute("SELECT * FROM mail_draft WHERE id = ?", (draft_id,)).fetchone()
        return _draft_from_row(c, r) if r else None


def update_draft(draft_id: int, **fields: Any) -> None:
    if "warnings" in fields:
        fields["warnings"] = json.dumps(fields["warnings"], ensure_ascii=False)
    sets = ", ".join(f"{k} = ?" for k in fields)
    with connect() as c:
        c.execute(
            f"UPDATE mail_draft SET {sets}, updated_at = ? WHERE id = ?",
            (
                *[_iso(v) if isinstance(v, datetime) else v for v in fields.values()],
                _now(),
                draft_id,
            ),
        )


def approve_draft(draft_id: int, user: str) -> None:
    with connect() as c:
        c.execute(
            "INSERT INTO mail_approval (draft_id, approved_by, approved_at) VALUES (?,?,?)",
            (draft_id, user, _now()),
        )
        c.execute("UPDATE mail_draft SET status = 'approved' WHERE id = ?", (draft_id,))


def revoke_approval(draft_id: int) -> None:
    with connect() as c:
        c.execute(
            "UPDATE mail_approval SET revoked_at = ? WHERE draft_id = ? AND revoked_at IS NULL",
            (_now(), draft_id),
        )
        c.execute("UPDATE mail_draft SET status = 'draft' WHERE id = ?", (draft_id,))


# ── 검증 ─────────────────────────────────────────────
def save_eval(e: EvalResult) -> None:
    d = e.model_dump()
    with connect() as c:
        c.execute(
            "INSERT OR REPLACE INTO eval_result (run_id, golden_week, selection_recall,"
            " selection_precision, match_recall, match_precision, review_needed_ratio,"
            " missed_items, extra_items, wrong_matches, elapsed_sec, created_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                d["run_id"],
                d["golden_week"],
                d["selection_recall"],
                d["selection_precision"],
                d["match_recall"],
                d["match_precision"],
                d["review_needed_ratio"],
                json.dumps(d["missed_items"], ensure_ascii=False),
                json.dumps(d["extra_items"], ensure_ascii=False),
                json.dumps(d["wrong_matches"], ensure_ascii=False),
                d["elapsed_sec"],
                _now(),
            ),
        )


def get_eval(run_id: int) -> EvalResult | None:
    with connect() as c:
        r = c.execute(
            "SELECT * FROM eval_result WHERE run_id = ? ORDER BY created_at DESC LIMIT 1",
            (run_id,),
        ).fetchone()
    if not r:
        return None
    d = dict(r)
    for k in ("missed_items", "extra_items", "wrong_matches"):
        d[k] = json.loads(d[k])
    return EvalResult.model_validate(d)


def add_history(draft_id: int, user: str, body: str) -> None:
    with connect() as c:
        c.execute(
            "INSERT INTO mail_draft_history (draft_id, edited_by, edited_at, body)"
            " VALUES (?,?,?,?)",
            (draft_id, user, _now(), body),
        )


def list_history(draft_id: int) -> list[dict[str, Any]]:
    with connect() as c:
        rows = c.execute(
            "SELECT edited_by, edited_at, body FROM mail_draft_history WHERE draft_id = ?"
            " ORDER BY id DESC",
            (draft_id,),
        ).fetchall()
    return [dict(r) for r in rows]


# ── 수집 결과 ─────────────────────────────────────────
def save_collect_log(run_id: int, source: str, status: str, count: int, message: str) -> None:
    with connect() as c:
        c.execute(
            "INSERT OR REPLACE INTO collect_log (run_id, source, status, count, message, at)"
            " VALUES (?,?,?,?,?,?)",
            (run_id, source, status, count, message, _now()),
        )


def list_collect_log(run_id: int) -> list[dict[str, Any]]:
    with connect() as c:
        rows = c.execute("SELECT * FROM collect_log WHERE run_id = ?", (run_id,)).fetchall()
    return [dict(r) for r in rows]


def list_matches_for_item(item_id: str) -> list[CustomerMatch]:
    with connect() as c:
        rows = c.execute("SELECT * FROM customer_match WHERE item_id = ?", (item_id,)).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["ai_matched"] = bool(d["ai_matched"])
        d["final_matched"] = None if d["final_matched"] is None else bool(d["final_matched"])
        out.append(CustomerMatch.model_validate(d))
    return out
