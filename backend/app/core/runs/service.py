"""주간 실행·현황·단계 바 (C-06). 현황 화면과 단계 바가 같은 응답을 읽는다 (DESIGN.md 1-0·3장)."""

from typing import Literal

from pydantic import BaseModel

from app.core.storage import local_db
from app.core.storage.local_db import RunCounts

Group = Literal["b1", "b2"]
StepState = Literal["waiting", "current", "done"]


class StepStatus(BaseModel):
    key: str  # components/ui/steps.ts의 key와 같다
    group: Group
    name: str
    state: StepState
    done: bool
    note: str  # 단계 바 칸 아래 작은 글 ("검토 필요 1건" 등)


class Todo(BaseModel):
    key: str
    text: str
    count: int
    href: str
    group: Group


class RunStatus(BaseModel):
    run: local_db.RunRow
    counts: RunCounts
    steps: list[StepStatus]
    current: dict[Group, str | None]  # 탭마다 지금 단계 key (모두 끝났으면 None)
    materials_ready: bool  # 재료 준비 5단계가 모두 끝났는지
    todos: list[Todo]  # 사람이 확인할 일 (0건은 뺀다)


def _steps(c: RunCounts) -> list[tuple[str, Group, str, bool, str]]:
    """(key, group, 이름, 끝남, 상태 글)."""
    sel_note = (
        f"검토 필요 {c.review_needed}건"
        if c.review_needed
        else (f"관련 {c.relevant}건" if c.selected else "")
    )
    ext_note = (
        f"확인 필요 {c.empty_fields}칸"
        if c.empty_fields
        else (f"{c.extracted}건" if c.extracted else "")
    )
    law_note = (
        f"대조 불일치 {c.law_mismatch}건" if c.law_mismatch else (f"{c.laws}건" if c.laws else "")
    )
    total_mail = c.drafts
    done_mail = c.approved + c.sent
    collect_note = (
        f"{c.raw_items}건 · 수집 실패 {c.collect_failed}곳"
        if c.collect_failed
        else (f"{c.raw_items}건" if c.raw_items else "")
    )
    return [
        ("collect", "b1", "자료 모으기", c.raw_items > 0, collect_note),
        (
            "select",
            "b1",
            "선별",
            c.raw_items > 0 and c.selected >= c.raw_items and c.review_needed == 0,
            sel_note,
        ),
        ("extract", "b1", "정보 뽑기", c.extracted > 0 and c.empty_fields == 0, ext_note),
        ("match", "b1", "고객사 판단", c.matches > 0, f"관련 {c.matches}건" if c.matches else ""),
        ("law", "b1", "법령 정리", c.laws > 0 and c.law_mismatch == 0, law_note),
        ("report", "b2", "보고서 조립", c.report_done, "조립됨" if c.report_done else ""),
        (
            "draft",
            "b2",
            "메일 초안",
            c.drafts > 0 and c.draft_warnings == 0,
            f"경고 {c.draft_warnings}건"
            if c.draft_warnings
            else (f"{c.drafts}통" if c.drafts else ""),
        ),
        (
            "send",
            "b2",
            "승인·발송",
            total_mail > 0 and done_mail == total_mail,
            f"승인 {done_mail}/{total_mail}" if total_mail else "",
        ),
        ("evaluate", "b2", "검증", c.evaluated, "계산됨" if c.evaluated else ""),
    ]


def _todos(c: RunCounts) -> list[Todo]:
    items = [
        Todo(
            key="review_needed",
            text=f"선별에서 '검토 필요' {c.review_needed}건을 정해 주세요",
            count=c.review_needed,
            href="/collect/?step=select&label=review_needed",
            group="b1",
        ),
        Todo(
            key="empty_fields",
            text=f"정보 뽑기에서 '확인 필요' 빈 칸 {c.empty_fields}개를 채워 주세요",
            count=c.empty_fields,
            href="/collect/?step=extract",
            group="b1",
        ),
        Todo(
            key="law_mismatch",
            text=f"법령 대조 불일치 {c.law_mismatch}건을 공문과 맞춰 봐 주세요",
            count=c.law_mismatch,
            href="/law/",
            group="b1",
        ),
        Todo(
            key="draft_warnings",
            text=f"메일 초안 경고 {c.draft_warnings}건을 확인해 주세요",
            count=c.draft_warnings,
            href="/drafts/?step=draft",
            group="b2",
        ),
        Todo(
            key="approval_waiting",
            text=f"승인 기다리는 메일 {c.approval_waiting}통",
            count=c.approval_waiting,
            href="/drafts/?step=send",
            group="b2",
        ),
    ]
    return [t for t in items if t.count > 0]


def run_status(run: local_db.RunRow) -> RunStatus:
    c = local_db.run_counts(run.id)
    raw = _steps(c)
    current: dict[Group, str | None] = {"b1": None, "b2": None}
    for key, group, _, done, _ in raw:
        if not done and current[group] is None:
            current[group] = key
    steps = [
        StepStatus(
            key=key,
            group=group,
            name=name,
            done=done,
            state="done" if done else ("current" if current[group] == key else "waiting"),
            note=note,
        )
        for key, group, name, done, note in raw
    ]
    return RunStatus(
        run=run,
        counts=c,
        steps=steps,
        current=current,
        materials_ready=current["b1"] is None,
        todos=_todos(c),
    )
