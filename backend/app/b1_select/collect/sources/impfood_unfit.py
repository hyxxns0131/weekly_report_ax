"""B1-02 수입식품 부적합 정보 (공식 Open API).

.env
    IMPFOOD_UNFIT_API=      식품안전나라 서비스 ID 또는 공공데이터포털 API 주소
    IMPFOOD_UNFIT_API_KEY=  인증키 (비우면 FOODSAFETY_API_KEY / DATA_GO_KR_SERVICE_KEY)
비어 있으면 수동 업로드로 남긴다.
더미(samples/b1_input/demo/impfood_unfit.json)는 mode=demo일 때만 쓴다.

어느 공식 API를 쓸지는 확인 필요 (식품안전나라·공공데이터포털에서 "수입식품 부적합" 검색).
API 칸 이름은 sources.json의 api.map.fields에 table_mapper 이름(제품명·제조국가·제조/수출회사·
위반내역 등)으로 적으면 정보 뽑기·고객사 판단까지 그대로 이어진다. 화면 읽기는 하지 않는다.
"""

from datetime import date
from typing import Any

from app.b1_select.collect import api_client
from app.b1_select.collect.base import CollectResult

SOURCE_ID = "impfood_unfit"


def collect(run_id: int, start: date, end: date, cfg: dict[str, Any]) -> CollectResult:
    return api_client.collect(SOURCE_ID, run_id, start, end, cfg)
