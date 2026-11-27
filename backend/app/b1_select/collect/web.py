"""공식 Open API 호출 공통 (B1-02~06, api_client.py가 쓴다). 웹 화면 읽기에는 쓰지 않는다.

- User-Agent: .env의 COLLECT_USER_AGENT
- 요청 간격: .env의 COLLECT_DELAY_SEC (요청마다 기다린다. API 트래픽 한도 보호)
- 실패: CollectHttpError로 이유를 남긴다
  (service.collect가 잡아서 그 출처만 "수집 실패"로 남기고 다른 출처는 계속한다).
"""

import time

import httpx

from app.core.config import get_settings

TIMEOUT = 20.0


class CollectHttpError(Exception):
    pass


def get(url: str, params: dict[str, str] | None = None) -> httpx.Response:
    s = get_settings()
    try:
        res = httpx.get(
            url,
            params=params,
            headers={"User-Agent": s.collect_user_agent},
            timeout=TIMEOUT,
            follow_redirects=True,
        )
        res.raise_for_status()
    except httpx.HTTPError as e:
        raise CollectHttpError(f"요청 실패: {e}") from e
    finally:
        time.sleep(max(s.collect_delay_sec, 0.0))
    return res
