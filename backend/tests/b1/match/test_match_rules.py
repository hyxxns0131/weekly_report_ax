"""B1-11 고객사 찾기. 고객사·제조사는 모두 가상(A사·B사·C사)."""

from fastapi.testclient import TestClient

from app.b1_select.match.customers import Customer, Keyword, load_customers
from app.b1_select.match.rules.maker import normalize_maker
from app.b1_select.match.service import judge
from app.core.schema import Category, Confidence, ExtractedInfo, MatchRule

DEMO_SOURCES = [
    "impfood_unfit",
    "impfood_inspection",
    "impfood_law_policy",
    "mfds_notice",
    "gyeongin_newsletter",
]


def _by_customer(info: ExtractedInfo, **kw: object) -> dict[str, tuple[MatchRule, Confidence, str]]:
    ms = judge(info, load_customers(), **kw)  # type: ignore[arg-type]
    return {m.customer_id: (m.rule, m.confidence, m.reason) for m in ms}


def test_same_maker_normalized_and_flagged() -> None:
    assert normalize_maker("Ocean Foods Co., Ltd.") == normalize_maker("OCEAN FOODS")
    assert normalize_maker("ocean  foods, inc.") == "oceanfoods"
    info = ExtractedInfo(item_id="x", maker="Ocean Foods Co., Ltd.")
    got = _by_customer(info)
    rule, conf, reason = got["C003"]
    assert rule == MatchRule.maker and conf == Confidence.high
    assert reason.endswith("같은 제조사 → 강조, 별도 안내")


def test_china_shrimp_alias_high() -> None:
    info = ExtractedInfo(
        item_id="x", origin_country="중국", food_type_raw="새우살", food_type_std="냉동새우"
    )
    got = _by_customer(info)
    assert got["C001"][:2] == (MatchRule.origin_food_type, Confidence.high)
    assert got["C003"][:2] == (MatchRule.origin_food_type, Confidence.high)


def test_hs_skipped_without_hs() -> None:
    c = Customer(customer_id="C9", display_name="가상사", hs_codes=["2208.30"])
    assert judge(ExtractedInfo(item_id="x"), [c]) == []
    m = judge(ExtractedInfo(item_id="x", hs_code="2208.30.1000"), [c])
    assert m and m[0].rule == MatchRule.hs_code


def test_three_customers_on_one_item() -> None:
    info = ExtractedInfo(
        item_id="x",
        origin_country="중국",
        food_type_raw="냉동새우살",
        food_type_std="냉동새우",
        maker="Ocean Foods Co., Ltd.",
    )
    got = _by_customer(info)
    assert set(got) == {"C001", "C002", "C003"}
    assert got["C003"][0] == MatchRule.maker
    assert got["C001"][0] == MatchRule.origin_food_type
    assert got["C002"][:2] == (MatchRule.food_type_only, Confidence.medium)


def test_law_news_body_food_type_medium() -> None:
    info = ExtractedInfo(item_id="x")
    text = "[가상] 수입식품 검사 대상에 건강기능식품 일부 품목 서류 기준 변경"
    got = _by_customer(info, category=Category.law_change, text=text)
    rule, conf, reason = got["C002"]
    assert (rule, conf) == (MatchRule.food_type_only, Confidence.medium)
    assert "본문에 '건강기능식품' 언급" in reason
    # 같은 글이라도 부적합 항목이면 본문 단어로 매칭하지 않는다
    assert _by_customer(info, category=Category.unfit, text=text) == {}


def test_missing_origin_or_food_type_no_match() -> None:
    c = Customer(
        customer_id="C9",
        display_name="가상사",
        keywords=[Keyword(origin_country=None, food_type="과자")],
    )
    assert judge(ExtractedInfo(item_id="x", food_type_std="과자"), [c]) == []
    assert judge(ExtractedInfo(item_id="x", origin_country="베트남"), [c]) == []


def test_demo_end_to_end(client: TestClient, auth_headers: dict[str, str]) -> None:
    h = auth_headers
    run_id = client.post("/api/core/runs", json={"reference_date": "2026-11-25"}, headers=h).json()[
        "id"
    ]
    client.post(f"/api/b1/runs/{run_id}/collect", json={"sources": DEMO_SOURCES}, headers=h)
    client.post(f"/api/b1/runs/{run_id}/analyze", headers=h)
    rows = client.get(f"/api/b1/runs/{run_id}/matches", headers=h).json()

    def names(word: str) -> set[str]:
        return {m["customer_name"] for m in rows if word in m["item_title"]}

    assert names("냉동새우살") == {"A사", "B사", "C사"}
    assert names("스카치위스키") == {"A사"}
    assert names("쌀과자") == {"B사"}
    assert names("레드와인") == {"A사"}
    assert names("김장재료") == {"B사"}
    assert names("냉동연어") == set()
    assert names("현지실사") == set()
    assert names("검사에 관한 규정") == {"B사"}
    whisky = next(m for m in rows if "스카치위스키" in m["item_title"])
    assert whisky["rule"] == "maker"
