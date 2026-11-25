"""주간 실행·현황 (C-06)."""

from pydantic import BaseModel

from app.core.storage import local_db


class StageStatus(BaseModel):
    key: str
    name: str
    status: str  # waiting | in_progress | done | failed
    count: int


class RunStatus(BaseModel):
    run: local_db.RunRow
    stages: list[StageStatus]


STAGES: list[tuple[str, str, str]] = [
    ("collect", "① 수집", "raw_item"),
    ("select", "② 선별", "selection"),
    ("match", "③ 고객사 판단", "customer_match"),
    ("law", "④ 법령 개정", "law_change_work"),
    ("draft", "⑤ 메일 초안", "mail_draft"),
    ("send", "⑥ 승인·발송", "mail_sent"),
]


def run_status(run: local_db.RunRow) -> RunStatus:
    stages = []
    for key, name, table in STAGES:
        n = local_db.count(table, run.id)
        stages.append(StageStatus(key=key, name=name, status="done" if n else "waiting", count=n))
    return RunStatus(run=run, stages=stages)
