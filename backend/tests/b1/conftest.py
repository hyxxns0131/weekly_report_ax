"""b1 테스트 공통 (LSH). 실제 API·Supabase를 부르지 않게 막는다.

테스트는 기본으로
- 데모 응답이 있는 출처와 법령 단계를 demo 모드로 바꾸고,
- 출처 API 주소·키를 모두 빈 값으로 둔다 (.env에 실제 키가 있어도 테스트는 쓰지 않는다.
  빈 값으로 "넣어 두어야" core/config.py의 load_dotenv가 .env 값으로 덮지 않는다),
- HTTP 요청(collect/web.get)은 "연결 실패", Supabase 쓰기는 "키 없음"으로 둔다.
API 모드를 시험하는 테스트는 이 위에 monkeypatch로 다시 바꾼다.
"""

from typing import Any

import pytest

from app.b1_select.collect import api_client, web
from app.b1_select.collect import service as collect_service
from app.b1_select.law import service as law_service
from app.core.storage import public_db

API_SOURCES = [
    "impfood_unfit",
    "impfood_inspection",
    "impfood_law_policy",
    "mfds_notice",
    "gyeongin_newsletter",
]


@pytest.fixture(autouse=True)
def demo_mode_and_no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    sources = collect_service.source_config
    law = law_service.law_source

    def demo_sources() -> list[dict[str, Any]]:
        return [{**s, "mode": "demo"} if s.get("demo_file") else s for s in sources()]

    def blocked(url: str, params: dict[str, str] | None = None) -> Any:
        raise web.CollectHttpError(f"테스트에서는 실제 API를 부르지 않는다: {url}")

    for sid in API_SOURCES:
        for name in api_client.env_names(sid):
            monkeypatch.setenv(name, "")
    monkeypatch.setenv("FOODSAFETY_API_KEY", "")
    monkeypatch.setenv("DATA_GO_KR_SERVICE_KEY", "")
    monkeypatch.setattr(collect_service, "source_config", demo_sources)
    monkeypatch.setattr(law_service, "law_source", lambda: {**law(), "mode": "demo"})
    monkeypatch.setattr(web, "get", blocked)
    monkeypatch.setattr(public_db, "can_write", lambda: False)
