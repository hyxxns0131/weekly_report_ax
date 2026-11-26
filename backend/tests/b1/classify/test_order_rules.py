"""B1-08 순서형 규칙 Q1~Q4. 모든 문장은 가상 예시다."""

import pytest
from fastapi.testclient import TestClient

from app.b1_select.classify.keyword_rules import classify
from app.core.schema import Category, Label

DEMO_SOURCES = [
    "impfood_unfit",
    "impfood_inspection",
    "impfood_law_policy",
    "mfds_notice",
    "gyeongin_newsletter",
]


@pytest.mark.parametrize(
    ("title", "source", "label"),
    [
        ("수입 사료", "impfood_unfit", Label.review_needed),
        ("의약품 성분 함유 수입 젤리", None, Label.relevant),
        ("국내 유통 수입 과자", None, Label.relevant),
        ("수입 자동차 통관", None, Label.review_needed),
        ("수입 화장품 통관", None, Label.irrelevant),
        ("국내산 김치 할인 행사", None, Label.irrelevant),
        ("국내산 원료 수입 안내", None, Label.review_needed),
        ("화장품 겸용 식용 오일", None, Label.review_needed),
        ("해외제조업소 등록 안내", None, Label.relevant),
    ],
)
def test_order_rules(title: str, source: str | None, label: Label) -> None:
    got, _, reason, _ = classify(title, "", source)
    assert got == label, reason
    assert reason.startswith("Q")


def test_kimjang_inspection() -> None:
    label, category, reason, quote = classify("김장철 김장재료 통관검사 강화", "", None)
    assert label == Label.relevant
    assert category == Category.inspection_order
    assert "Q3" in reason and "통관" in quote


def test_reason_is_short_question_tag() -> None:
    _, _, reason, quote = classify("수입 화장품 통관", "", None)
    assert reason == "Q2 제외 대상: 화장품"
    assert quote == "화장품"


def test_demo_labels(client: TestClient, auth_headers: dict[str, str]) -> None:
    h = auth_headers
    run_id = client.post("/api/core/runs", json={"reference_date": "2026-11-25"}, headers=h).json()[
        "id"
    ]
    client.post(f"/api/b1/runs/{run_id}/collect", json={"sources": DEMO_SOURCES}, headers=h)
    res = client.post(f"/api/b1/runs/{run_id}/analyze", headers=h).json()
    assert res == {**res, "total": 14, "relevant": 10, "review_needed": 2, "irrelevant": 2}

    items = client.get(f"/api/b1/runs/{run_id}/items", headers=h).json()

    def find(word: str) -> dict[str, str]:
        row = next(i for i in items if word in i["raw"]["title"])
        sel: dict[str, str] = row["selection"]
        return sel

    assert find("배합사료")["ai_label"] == "review_needed"
    assert find("냉동새우살")["ai_category"] == "unfit"
    assert find("김장재료")["ai_category"] == "inspection_order"
    assert find("현지실사")["ai_category"] == "policy_news"
    assert find("식품첨가물")["ai_category"] == "law_change"
    assert find("화장품")["ai_label"] == "irrelevant"
    assert find("자동차")["ai_label"] == "review_needed"
    assert find("의약품 허가")["ai_label"] == "irrelevant"
    assert find("냉동연어")["ai_label"] == "relevant"  # '동물용의약품 잔류'는 제외하지 않는다
