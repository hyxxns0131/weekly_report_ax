"""B1-12 법제처 국가법령정보 OPEN API (기존 도구 law_api.py의 search_admrul·admrul_detail 방식).

- OC(LAW_API_OC)와 등록한 공인 IP에서만 동작한다. 검증 실패면 LawApiError로 이유를 알린다.
- 응답 칸 이름은 법제처 JSON 기준. 없는 칸은 None으로 두고 화면에 "확인 필요"로 보인다.
"""

import time
from typing import Any

import httpx

from app.core.config import get_settings

BASE = "https://www.law.go.kr/DRF"
TIMEOUT = 20.0


class LawApiError(Exception):
    pass


def _get(path: str, params: dict[str, str]) -> dict[str, Any]:
    s = get_settings()
    if not s.law_api_oc:
        raise LawApiError(".env에 LAW_API_OC(법제처 OPEN API 아이디)를 넣어 주세요.")
    try:
        res = httpx.get(
            f"{BASE}/{path}",
            params={"OC": s.law_api_oc, "type": "JSON", **params},
            headers={"User-Agent": s.collect_user_agent},
            timeout=TIMEOUT,
        )
    except httpx.HTTPError as e:
        raise LawApiError(f"법제처 API 연결 실패: {e}") from e
    text = res.text
    if "사용자 정보 검증에 실패" in text:
        raise LawApiError("법제처 API: 사용자 정보 검증 실패. 등록 IP·OC 확인 필요")
    try:
        data: dict[str, Any] = res.json()
    except ValueError as e:
        raise LawApiError(f"법제처 API 응답을 읽지 못했습니다: {text[:100]}") from e
    time.sleep(min(s.collect_delay_sec, 1.0))
    return data


def _as_list(v: Any) -> list[dict[str, Any]]:
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def search_admrul(query: str, display: int = 20) -> list[dict[str, Any]]:
    """행정규칙(고시 등) 검색. 최신 발령 순."""
    data = _get(
        "lawSearch.do",
        {"target": "admrul", "query": query, "display": str(display), "sort": "ddes"},
    )
    return _as_list(data.get("AdmRulSearch", {}).get("admrul"))


def admrul_detail(serial: str) -> dict[str, Any]:
    """행정규칙 본문(조문·제개정 이유). 행정규칙일련번호로 조회."""
    data = _get("lawService.do", {"target": "admrul", "ID": serial})
    service: dict[str, Any] = data.get("AdmRulService", data)
    return service
