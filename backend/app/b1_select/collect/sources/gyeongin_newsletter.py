"""B1-06 경인지방식약청 수입검사 뉴스레터 (공식 Open API).

.env
    GYEONGIN_NEWSLETTER_API=      식품안전나라 서비스 ID 또는 공공데이터포털 API 주소
    GYEONGIN_NEWSLETTER_API_KEY=  인증키 (비우면 FOODSAFETY_API_KEY / DATA_GO_KR_SERVICE_KEY)
비어 있으면 수동 업로드로 남긴다.
더미(samples/b1_input/demo/gyeongin_newsletter.json)는 mode=demo일 때만 쓴다.

뉴스레터는 매달 한 번 나오고 내용은 첨부(hwpx)에 있다. 공식 API가 없으면 SAMC가 받는
메일(B1-07 Gmail 수신, GMAIL_INBOX_QUERY)이나 수동 업로드(B1-01)로 받는다. 화면 읽기는 하지 않는다.
"""

from datetime import date
from typing import Any

from app.b1_select.collect import api_client
from app.b1_select.collect.base import CollectResult

SOURCE_ID = "gyeongin_newsletter"


def collect(run_id: int, start: date, end: date, cfg: dict[str, Any]) -> CollectResult:
    return api_client.collect(SOURCE_ID, run_id, start, end, cfg)
