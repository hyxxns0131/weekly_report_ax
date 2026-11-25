"""B1-11 고객사 설정 읽기 (가명 ID).

목업: backend/config/b1/customers/sample_*.json(가상 A사·B사)만 읽는다.
실제 고객사는 구글 드라이브에서 읽도록 바꾼다(core/storage/drive.py). 실명은 저장소에 두지 않는다.
"""

import json

from pydantic import BaseModel, Field

from app.core.config import REPO_ROOT

CUSTOMERS_DIR = REPO_ROOT / "backend" / "config" / "b1" / "customers"


class Keyword(BaseModel):
    origin_country: str | None = None
    food_type: str


class Customer(BaseModel):
    customer_id: str
    display_name: str
    keywords: list[Keyword] = Field(default_factory=list)
    makers: list[str] = Field(default_factory=list)
    hs_codes: list[str] = Field(default_factory=list)


def load_customers() -> list[Customer]:
    files = sorted(CUSTOMERS_DIR.glob("*.json"))
    return [Customer.model_validate(json.loads(f.read_text(encoding="utf-8"))) for f in files]


def names() -> dict[str, str]:
    return {c.customer_id: c.display_name for c in load_customers()}
