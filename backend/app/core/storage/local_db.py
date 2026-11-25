"""로컬 SQLite 연결 (C-04). 테이블 정의는 schema.sql(KHS 고정)에만 있다.

담당자 모듈은 이 파일의 함수로만 읽고 쓴다. SQL을 각자 모듈에 직접 쓰지 않는다.
필요한 함수가 없으면 PR "변경 요청"에 적는다.
처음 만들기: `python -m app.core.storage.local_db --init` (backend 폴더에서)
"""

import sqlite3
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from pydantic import BaseModel

from app.core.config import get_settings
from app.core.period import report_period

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


class RunRow(BaseModel):
    id: int
    reference_date: str
    period_start: str
    period_end: str
    week_label: str
    created_by: str | None
    created_at: str


def now_kst() -> datetime:
    return datetime.now(ZoneInfo(get_settings().tz_name))


@contextmanager
def connect(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    path = db_path or get_settings().local_db_path
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: Path | None = None) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


def create_run(reference_date: str, created_by: str | None) -> RunRow:
    from datetime import date

    period = report_period(date.fromisoformat(reference_date))
    created_at = now_kst().isoformat(timespec="seconds")
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO weekly_run (reference_date, period_start, period_end, week_label,"
            " created_by, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                reference_date,
                period.period_start.isoformat(),
                period.period_end.isoformat(),
                period.week_label,
                created_by,
                created_at,
            ),
        )
        run_id = cur.lastrowid
    run = get_run(int(run_id or 0))
    assert run is not None
    return run


def get_run(run_id: int) -> RunRow | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM weekly_run WHERE id = ?", (run_id,)).fetchone()
    return RunRow(**dict(row)) if row else None


def latest_run() -> RunRow | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM weekly_run ORDER BY id DESC LIMIT 1").fetchone()
    return RunRow(**dict(row)) if row else None


def count(table: str, run_id: int) -> int:
    """단계별 건수 (현황 화면용). table은 아래 허용 목록만."""
    queries = {
        "raw_item": "SELECT COUNT(*) FROM raw_item WHERE run_id = ?",
        "selection": "SELECT COUNT(*) FROM selection s JOIN raw_item r ON r.id = s.item_id"
        " WHERE r.run_id = ?",
        "customer_match": "SELECT COUNT(*) FROM customer_match m JOIN raw_item r"
        " ON r.id = m.item_id WHERE r.run_id = ?",
        "law_change_work": "SELECT COUNT(*) FROM law_change_work WHERE run_id = ?",
        "mail_draft": "SELECT COUNT(*) FROM mail_draft WHERE run_id = ?",
        "mail_sent": "SELECT COUNT(*) FROM mail_draft WHERE run_id = ? AND status = 'sent'",
    }
    with connect() as conn:
        return int(conn.execute(queries[table], (run_id,)).fetchone()[0])


# ── 현황·단계 바 건수 (C-06) ─────────────────────────

KEY_FIELDS = ("product_name_ko", "food_type_raw", "origin_country", "maker", "violation")


class RunCounts(BaseModel):
    raw_items: int = 0
    collect_failed: int = 0
    selected: int = 0
    review_needed: int = 0
    relevant: int = 0
    extracted: int = 0
    empty_fields: int = 0
    matches: int = 0
    laws: int = 0
    law_mismatch: int = 0
    report_done: bool = False
    drafts: int = 0
    draft_warnings: int = 0
    approval_waiting: int = 0
    approved: int = 0
    sent: int = 0
    evaluated: bool = False


def run_counts(run_id: int) -> RunCounts:
    label = "COALESCE(s.final_label, s.ai_label)"
    empties = " + ".join(f"(e.{f} IS NULL OR e.{f} = '')" for f in KEY_FIELDS)
    q: dict[str, str] = {
        "raw_items": "SELECT COUNT(*) FROM raw_item WHERE run_id = :r",
        "collect_failed": "SELECT COUNT(*) FROM collect_log"
        " WHERE run_id = :r AND status = 'failed'",
        "selected": "SELECT COUNT(*) FROM selection s JOIN raw_item r ON r.id = s.item_id"
        " WHERE r.run_id = :r",
        "review_needed": "SELECT COUNT(*) FROM selection s JOIN raw_item r ON r.id = s.item_id"
        f" WHERE r.run_id = :r AND {label} = 'review_needed'",
        "relevant": "SELECT COUNT(*) FROM selection s JOIN raw_item r ON r.id = s.item_id"
        f" WHERE r.run_id = :r AND {label} = 'relevant'",
        "extracted": "SELECT COUNT(*) FROM extracted_info e JOIN raw_item r ON r.id = e.item_id"
        " WHERE r.run_id = :r",
        "empty_fields": f"SELECT COALESCE(SUM({empties}), 0) FROM extracted_info e"
        " JOIN raw_item r ON r.id = e.item_id WHERE r.run_id = :r",
        "matches": "SELECT COUNT(*) FROM customer_match m JOIN raw_item r ON r.id = m.item_id"
        " WHERE r.run_id = :r AND COALESCE(m.final_matched, m.ai_matched) = 1",
        "laws": "SELECT COUNT(*) FROM law_change_work WHERE run_id = :r",
        "law_mismatch": "SELECT COUNT(*) FROM law_change_work WHERE run_id = :r"
        " AND crosscheck IN ('api_only', 'notice_only')",
        "report_done": "SELECT COUNT(*) FROM weekly_report WHERE run_id = :r",
        "drafts": "SELECT COUNT(*) FROM mail_draft WHERE run_id = :r",
        "draft_warnings": "SELECT COALESCE(SUM(json_array_length(warnings)), 0) FROM mail_draft"
        " WHERE run_id = :r AND status = 'draft'",
        "approval_waiting": "SELECT COUNT(*) FROM mail_draft"
        " WHERE run_id = :r AND status = 'draft'",
        "approved": "SELECT COUNT(*) FROM mail_draft WHERE run_id = :r AND status = 'approved'",
        "sent": "SELECT COUNT(*) FROM mail_draft WHERE run_id = :r AND status = 'sent'",
        "evaluated": "SELECT COUNT(*) FROM eval_result WHERE run_id = :r",
    }
    out: dict[str, int] = {}
    with connect() as conn:
        for k, sql in q.items():
            out[k] = int(conn.execute(sql, {"r": run_id}).fetchone()[0] or 0)
    return RunCounts(
        **{k: v for k, v in out.items() if k not in ("report_done", "evaluated")},
        report_done=out["report_done"] > 0,
        evaluated=out["evaluated"] > 0,
    )


# ── 알림 (C-06, DESIGN.md 3-2) ───────────────────────


def notice_laws(run_id: int) -> list[dict[str, object]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, law_name, change_type, number, effective_at, ai_summary, final_summary,"
            " source_url, crosscheck, related_food_types FROM law_change_work"
            " WHERE run_id = ? ORDER BY effective_at DESC, id",
            (run_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def notice_inspections(run_id: int) -> list[dict[str, object]]:
    """통관단계 검사지시 중 관련·검토 필요 항목 + 추출 정보 + 관련 고객사(가명 ID)."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT r.id AS item_id, r.title, r.source, r.url, r.posted_at,"
            " e.origin_country, e.food_type_std, e.food_type_raw, e.product_name_ko,"
            " e.violation, e.period_start, e.period_end,"
            " (SELECT GROUP_CONCAT(m.customer_id) FROM customer_match m"
            "   WHERE m.item_id = r.id AND COALESCE(m.final_matched, m.ai_matched) = 1)"
            "   AS customers"
            " FROM raw_item r JOIN selection s ON s.item_id = r.id"
            " LEFT JOIN extracted_info e ON e.item_id = r.id"
            " WHERE r.run_id = ?"
            " AND COALESCE(s.final_category, s.ai_category) = 'inspection_order'"
            " AND COALESCE(s.final_label, s.ai_label) IN ('relevant', 'review_needed')"
            " ORDER BY r.posted_at DESC, r.id",
            (run_id,),
        ).fetchall()
    return [dict(r) for r in rows]


class NoticeState(BaseModel):
    notice_id: str
    run_id: int | None = None
    read_by: str | None = None
    read_at: str | None = None
    dismissed_by: str | None = None
    dismissed_at: str | None = None


def notice_states(ids: list[str]) -> dict[str, NoticeState]:
    if not ids:
        return {}
    marks = ",".join("?" for _ in ids)
    with connect() as conn:
        rows = conn.execute(
            f"SELECT * FROM notice_state WHERE notice_id IN ({marks})", ids
        ).fetchall()
    return {r["notice_id"]: NoticeState(**dict(r)) for r in rows}


def mark_notice(notice_id: str, run_id: int | None, action: str, user: str) -> NoticeState:
    """action: read | dismiss. 지우면 읽음도 같이 남긴다. 이미 읽은 기록은 바꾸지 않는다."""
    at = now_kst().isoformat(timespec="seconds")
    with connect() as conn:
        conn.execute(
            "INSERT INTO notice_state (notice_id, run_id) VALUES (?, ?)"
            " ON CONFLICT(notice_id) DO NOTHING",
            (notice_id, run_id),
        )
        conn.execute(
            "UPDATE notice_state SET read_by = ?, read_at = ? WHERE notice_id = ?"
            " AND read_at IS NULL",
            (user, at, notice_id),
        )
        if action == "dismiss":
            conn.execute(
                "UPDATE notice_state SET dismissed_by = ?, dismissed_at = ? WHERE notice_id = ?",
                (user, at, notice_id),
            )
        row = conn.execute(
            "SELECT * FROM notice_state WHERE notice_id = ?", (notice_id,)
        ).fetchone()
    return NoticeState(**dict(row))


if __name__ == "__main__":
    if "--init" in sys.argv:
        init_db()
        print(f"로컬 DB를 만들었습니다: {get_settings().local_db_path}")
