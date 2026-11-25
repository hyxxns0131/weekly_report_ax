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


if __name__ == "__main__":
    if "--init" in sys.argv:
        init_db()
        print(f"로컬 DB를 만들었습니다: {get_settings().local_db_path}")
