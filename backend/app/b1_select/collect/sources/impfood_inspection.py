"""B1-03 통관단계 검사지시 (공식 Open API).

.env
    IMPFOOD_INSPECTION_API=      식품안전나라 서비스 ID 또는 공공데이터포털 API 주소
    IMPFOOD_INSPECTION_API_KEY=  인증키 (비우면 FOODSAFETY_API_KEY / DATA_GO_KR_SERVICE_KEY)
비어 있으면 수동 업로드로 남긴다.
더미(samples/b1_input/demo/impfood_inspection.json)는 mode=demo일 때만 쓴다.

공식 API 제공 여부 확인 필요 (2026-11-26 검색으로는 찾지 못함). API가 없으면 SAMC가 받는
공문 메일(B1-07 Gmail 수신)이나 수동 업로드(B1-01)로 받는다. 화면 읽기는 하지 않는다.
"""

from datetime import date
from typing import Any

from app.b1_select.collect import api_client
from app.b1_select.collect.base import CollectResult

SOURCE_ID = "impfood_inspection"


def collect(run_id: int, start: date, end: date, cfg: dict[str, Any]) -> CollectResult:
    return api_client.collect(SOURCE_ID, run_id, start, end, cfg)
