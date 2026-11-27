"""B1-05 식약처 제개정고시 (공식 Open API).

.env
    MFDS_NOTICE_API=      식품안전나라 서비스 ID 또는 공공데이터포털 API 주소
    MFDS_NOTICE_API_KEY=  인증키 (비우면 FOODSAFETY_API_KEY / DATA_GO_KR_SERVICE_KEY)
비어 있으면 수동 업로드로 남긴다.
더미(samples/b1_input/demo/mfds_notice.json)는 mode=demo일 때만 쓴다.

식약처 고시(행정규칙)의 제·개정은 법령 개정 단계(B1-12)가 법제처 OPEN API(LAW_API_OC,
행정규칙 검색 target=admrul)로 가져온다. 여기는 고시 원문 게시글을 따로 받을 API가 있을 때 쓴다.
같은 개정이 두 곳에 나오면 B1-14 crosscheck가 대조한다. 화면 읽기는 하지 않는다.
"""

from datetime import date
from typing import Any

from app.b1_select.collect import api_client
from app.b1_select.collect.base import CollectResult

SOURCE_ID = "mfds_notice"


def collect(run_id: int, start: date, end: date, cfg: dict[str, Any]) -> CollectResult:
    return api_client.collect(SOURCE_ID, run_id, start, end, cfg)
