"""b2 input.py 샘플 모드: 가상 고객사 이름표 (LSH PR #12 요청, demo_week.json의 C003)."""

import json

from app.b2_mail.input import load_customer_names
from app.core.config import REPO_ROOT


def test_sample_names_cover_all_virtual_customers() -> None:
    names = load_customer_names(None, "sample")
    assert names == {"C001": "A사", "C002": "B사", "C003": "C사"}

    # b1 샘플 설정(가상 고객사)과 이름이 같아야 한다
    for path in (REPO_ROOT / "backend" / "config" / "b1" / "customers").glob("sample_*.json"):
        c = json.loads(path.read_text(encoding="utf-8"))
        assert names[c["customer_id"]] == c["display_name"]


def test_demo_week_customers_have_names() -> None:
    demo = json.loads(
        (REPO_ROOT / "samples" / "b1_output" / "demo_week.json").read_text(encoding="utf-8")
    )
    ids = {m["customer_id"] for i in demo["items"] for m in i.get("matches", [])}
    assert ids <= set(load_customer_names(None, "sample"))  # "C003"처럼 ID로 보이는 곳이 없다
