"""B2-03 고객사별 안내 메일: 확정된 판단만 본문에, 확인 전 후보는 경고로, 재안내 글 포함.

b1 데모 결과(samples/b1_output/demo_week.json, 가상 A사·B사·C사)를 샘플 입력으로 끼워 쓴다.
demo_week.json은 LSH 파일이라 고치지 않고, 바꿔야 하는 경우는 임시 폴더에 복사본을 만든다.
"""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.config import REPO_ROOT

DEMO = REPO_ROOT / "samples" / "b1_output" / "demo_week.json"

Loader = Callable[[Callable[[dict[str, Any]], None] | None], None]


@pytest.fixture
def use_demo(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Loader:
    """source=sample 입력을 데모 자료로 바꾼다. change가 있으면 복사본을 고쳐서 쓴다."""
    from app.b2_mail import input as b2_input

    def load(change: Callable[[dict[str, Any]], None] | None = None) -> None:
        data = json.loads(DEMO.read_text(encoding="utf-8"))
        if change:
            change(data)
        path = tmp_path / "week.json"
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        monkeypatch.setattr(b2_input, "SAMPLE", path)

    return load


def _run(client: TestClient, h: dict[str, str]) -> int:
    res = client.post("/api/core/runs", json={"reference_date": "2026-11-25"}, headers=h)
    run_id: int = res.json()["id"]
    return run_id


def _drafts(client: TestClient, h: dict[str, str], run_id: int) -> list[dict[str, Any]]:
    res = client.post(f"/api/b2/runs/{run_id}/drafts?source=sample", headers=h)
    assert res.status_code == 200, res.text
    drafts: list[dict[str, Any]] = res.json()
    return drafts


def _by_customer(drafts: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {d["customer_id"]: d for d in drafts if d["kind"] == "customer"}


def _staff(drafts: list[dict[str, Any]]) -> dict[str, Any]:
    return next(d for d in drafts if d["kind"] == "staff_summary")


def test_each_customer_gets_own_mail(
    client: TestClient, auth_headers: dict[str, str], use_demo: Loader
) -> None:
    use_demo(None)
    mails = _by_customer(_drafts(client, auth_headers, _run(client, auth_headers)))
    assert sorted(mails) == ["C001", "C002", "C003"]

    # 고객사 메일마다 다른 고객사 이름이 없다 (3곳이라 상대 2곳 모두 확인)
    names = {"C001": "A사", "C002": "B사", "C003": "C사"}
    for cid, d in mails.items():
        for other_id, other in names.items():
            if other_id != cid:
                assert other not in d["ai_body"], (cid, other)
        assert not any(w.startswith("다른 고객사명") for w in d["warnings"])

    # C사는 같은 제조사 건(Ocean Foods)만 받는다
    c = mails["C003"]["ai_body"]
    assert "Ocean Foods" in c
    assert c.index("1. 수입식품") < c.index("2. 주간 법령") < c.index("3. 주간 검역")


def test_same_maker_mark_only_for_own_match(
    client: TestClient, auth_headers: dict[str, str], use_demo: Loader
) -> None:
    """C사(같은 제조사 규칙) 행에 '귀사 수입 이력과 같은 제조사' 표시. 남의 판단은 안 보인다."""
    use_demo(None)
    drafts = _drafts(client, auth_headers, _run(client, auth_headers))
    mails = _by_customer(drafts)
    mark = "【귀사 수입 이력과 같은 제조사】"
    c_row = next(ln for ln in mails["C003"]["ai_body"].splitlines() if "Ocean Foods" in ln)
    assert mark in c_row
    assert mark not in mails["C002"]["ai_body"]  # B사는 같은 제조사 판단이 없다
    staff = _staff(drafts)["ai_body"]
    assert mark not in staff  # 담당자 메일은 원래 표시(【같은 제조사】) 그대로
    assert "【같은 제조사】" in staff


def test_same_maker_row_comes_first(
    client: TestClient, auth_headers: dict[str, str], use_demo: Loader
) -> None:
    """A사 표에서 같은 제조사 행이 맨 위(머리줄·구분줄 다음)."""
    use_demo(None)
    a = _by_customer(_drafts(client, auth_headers, _run(client, auth_headers)))["C001"]
    rows = [ln for ln in a["ai_body"].splitlines() if ln.startswith("   | ")]
    assert len(rows) >= 3  # 머리줄 + 2행 이상
    assert "【귀사 수입 이력과 같은 제조사】" in rows[1]


def test_body_wording_from_config(
    client: TestClient, auth_headers: dict[str, str], use_demo: Loader
) -> None:
    use_demo(None)
    d = _by_customer(_drafts(client, auth_headers, _run(client, auth_headers)))["C003"]
    body: str = d["ai_body"]
    assert body.startswith(
        "안녕하세요, 관세법인 SAMC입니다.\n"
        "이번 주 귀사 수입 품목과 관련된 검역 정보를 안내드립니다.\n\n1. "
    )
    assert body.endswith(
        "세부 적용은 담당자와 확인 부탁드립니다.\n감사합니다.\n관세법인 SAMC 통관검역팀 드림"
    )
    assert d["subject"] == "[SAMC] 2026년 11월 3주차 귀사 수입 품목 관련 검역 정보 안내"


def test_pending_candidates_stay_out_of_body(
    client: TestClient, auth_headers: dict[str, str], use_demo: Loader
) -> None:
    """B사: 확정 건은 본문에, 신뢰도 중간(확인 전) 건은 경고로만."""
    use_demo(None)
    b = _by_customer(_drafts(client, auth_headers, _run(client, auth_headers)))["C002"]
    assert any(w.startswith("확인 전 후보 1건은 본문에 넣지 않았습니다") for w in b["warnings"])


def test_customer_with_only_pending_gets_no_mail(
    client: TestClient, auth_headers: dict[str, str], use_demo: Loader
) -> None:
    """C사 판단을 신뢰도 중간(확인 전)으로 낮추면 C사 메일은 없고 담당자 경고에 남는다."""

    def lower_c(data: dict[str, Any]) -> None:
        for item in data["items"]:
            for m in item.get("matches", []):
                if m["customer_id"] == "C003":
                    m["confidence"] = "medium"

    use_demo(lower_c)
    drafts = _drafts(client, auth_headers, _run(client, auth_headers))
    assert sorted(_by_customer(drafts)) == ["C001", "C002"]
    assert any(
        w.startswith("확인 전 후보만 있는 고객사 1곳은 안내 메일을 만들지 않았습니다")
        for w in _staff(drafts)["warnings"]
    )


def test_staff_keep_maps_to_customer_mail(
    client: TestClient, auth_headers: dict[str, str], use_demo: Loader
) -> None:
    """확인 전이라도 담당자가 [유지](final_matched=True)하면 메일이 만들어진다."""

    def keep_c(data: dict[str, Any]) -> None:
        for item in data["items"]:
            for m in item.get("matches", []):
                if m["customer_id"] == "C003":
                    m["confidence"] = "medium"
                    m["final_matched"] = True

    use_demo(keep_c)
    drafts = _drafts(client, auth_headers, _run(client, auth_headers))
    assert "C003" in _by_customer(drafts)
    assert not any("확인 전 후보만" in w for w in _staff(drafts)["warnings"])


def _lower_c(data: dict[str, Any]) -> None:
    for item in data["items"]:
        for m in item.get("matches", []):
            if m["customer_id"] == "C003":
                m["confidence"] = "medium"


def test_dropped_customer_draft_is_marked_and_blocked(
    client: TestClient, auth_headers: dict[str, str], use_demo: Loader
) -> None:
    """C사 초안 승인 뒤 C사가 대상에서 빠지면: 초안은 남고 [대상 제외] 경고·승인 풀림·승인 불가.

    다시 대상이 되면 경고가 사라지고 승인할 수 있다.
    """
    h = auth_headers
    run_id = _run(client, h)
    use_demo(None)
    c = _by_customer(_drafts(client, h, run_id))["C003"]
    ok = client.post(
        f"/api/b2/drafts/{c['id']}/approve", json={"acknowledge_warnings": True}, headers=h
    )
    assert ok.json()["status"] == "approved"
    client.patch(f"/api/b2/drafts/{c['id']}", json={"final_body": "C사 수정본"}, headers=h)
    client.post(f"/api/b2/drafts/{c['id']}/approve", json={"acknowledge_warnings": True}, headers=h)

    # C사가 확인 전 후보로 바뀐 뒤 다시 만들기
    use_demo(_lower_c)
    again = _by_customer(_drafts(client, h, run_id))
    d = again["C003"]  # 지우지 않고 결과 목록에도 보인다
    assert d["id"] == c["id"]
    assert d["warnings"][0].startswith("[대상 제외] 이번 주 안내 대상에서 빠진 고객사입니다")
    assert d["status"] == "draft"  # 승인 풀림
    assert d["final_body"] == "C사 수정본"  # 담당자가 고친 글은 그대로
    blocked = client.post(
        f"/api/b2/drafts/{c['id']}/approve", json={"acknowledge_warnings": True}, headers=h
    )
    assert blocked.status_code == 409
    assert "대상에서 빠진" in blocked.json()["detail"]
    assert client.post(f"/api/b2/drafts/{c['id']}/send", headers=h).status_code == 409

    # 한 번 더 만들어도 경고는 1개만
    third = _by_customer(_drafts(client, h, run_id))["C003"]
    assert sum(w.startswith("[대상 제외]") for w in third["warnings"]) == 1

    # 다시 대상이 되면 경고가 사라지고 승인할 수 있다
    use_demo(None)
    back = _by_customer(_drafts(client, h, run_id))["C003"]
    assert not any(w.startswith("[대상 제외]") for w in back["warnings"])
    ok = client.post(
        f"/api/b2/drafts/{c['id']}/approve", json={"acknowledge_warnings": True}, headers=h
    )
    assert ok.status_code == 200 and ok.json()["status"] == "approved"


def test_reannounce_reaches_customer_mail(
    client: TestClient, auth_headers: dict[str, str], use_demo: Loader
) -> None:
    """새 개정이 없는 주의 재안내 글은 담당자 메일과 똑같이 고객사 메일에도 들어간다."""

    def no_law(data: dict[str, Any]) -> None:
        data["law_changes"] = []

    use_demo(no_law)
    h = auth_headers
    run_id = _run(client, h)
    res = client.put(
        f"/api/b2/runs/{run_id}/report/reannounce",
        json={"text": "가상 고시 재안내 문장"},
        headers=h,
    )
    assert res.status_code == 200, res.text
    drafts = _drafts(client, h, run_id)
    assert "가상 고시 재안내 문장" in _staff(drafts)["ai_body"]
    for d in _by_customer(drafts).values():
        assert "가상 고시 재안내 문장" in d["ai_body"]
        assert "해당 없습니다" not in d["ai_body"].split("2. 주간 법령")[1].split("3. ")[0]
