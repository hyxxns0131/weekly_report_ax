"""B1-04 수입식품 관련법령·정책소식 (공식 Open API).

.env
    IMPFOOD_LAW_POLICY_API=      식품안전나라 서비스 ID 또는 공공데이터포털 API 주소
    IMPFOOD_LAW_POLICY_API_KEY=  인증키 (비우면 FOODSAFETY_API_KEY / DATA_GO_KR_SERVICE_KEY)
비어 있으면 수동 업로드로 남긴다.
더미(samples/b1_input/demo/impfood_law_policy.json)는 mode=demo일 때만 쓴다.

법령 개정 자체는 법령 개정 단계(B1-12, 법제처 OPEN API, LAW_API_OC)가 가져온다.
정책소식용 공식 API 제공 여부는 확인 필요. 화면 읽기는 하지 않는다.
"""

from datetime import date
from typing import Any

from app.b1_select.collect import api_client
from app.b1_select.collect.base import CollectResult

SOURCE_ID = "impfood_law_policy"


def collect(run_id: int, start: date, end: date, cfg: dict[str, Any]) -> CollectResult:
    return api_client.collect(SOURCE_ID, run_id, start, end, cfg)
