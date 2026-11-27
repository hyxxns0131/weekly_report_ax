"""공식 Open API로 출처 자료 가져오기 (B1-02~06). 화면 읽기(크롤링)는 하지 않는다.

출처마다 .env에 두 줄을 넣으면 바로 API로 바뀐다. 비어 있으면 수동 업로드로 남긴다
(더미는 sources.json mode=demo일 때만). 서비스 ID는 비밀이 아니라서 sources.json의
api.service에 둘 수도 있다(.env 값이 우선).

    <출처ID 대문자>_API=      API 주소 또는 식품안전나라 서비스 ID
    <출처ID 대문자>_API_KEY=  인증키 (비우면 아래 공용 키를 쓴다)

    예) IMPFOOD_UNFIT_API=I1234                       → 식품안전나라 Open API (서비스 ID)
        IMPFOOD_UNFIT_API_KEY=...                     (비우면 FOODSAFETY_API_KEY)
        MFDS_NOTICE_API=https://apis.data.go.kr/...   → 공공데이터포털 Open API
        MFDS_NOTICE_API_KEY=...                       (비우면 DATA_GO_KR_SERVICE_KEY, Decoding 키)

지원하는 형식
- 식품안전나라: http://openapi.foodsafetykorea.go.kr/api/{키}/{서비스ID}/json/{시작}/{끝}
  응답 {서비스ID: {"total_count", "row": [...], "RESULT": {"CODE", "MSG"}}}
- 공공데이터포털 등 그 밖의 주소: GET {주소}?serviceKey=&pageNo=&numOfRows=&type=json
  응답 안에서 첫 번째 "dict 목록"(response.body.items.item 등)을 행으로 쓴다.

API 칸 이름 → 우리 칸 이름은 sources.json 출처의 "api.map"에 적는다. 비어 있으면
제목·날짜 칸을 이름으로 짐작하고, 나머지 칸은 API 이름 그대로 본문에 담는다.
보고 기간 거르기는 공통 단계(base.rows_to_result)에서 한다.
"""

import json
import os
import re
from dataclasses import dataclass
from datetime import date
from typing import Any

from app.b1_select.collect import web
from app.b1_select.collect.base import (
    CollectResult,
    demo_path,
    load_demo,
    rows_to_result,
)
from app.core.config import get_settings

FOODSAFETY_BASE = "http://openapi.foodsafetykorea.go.kr/api"
FOODSAFETY_PAGE = 1000
DATAGO_PAGE = 100
MAX_PAGES = 10
NO_API_NOTE = "API 미설정 → 수동 업로드"

_TITLE_HINTS = ("TITLE", "SJ", "SUBJECT", "NM", "NAME", "제목", "명")
_DATE_HINTS = ("DT", "DE", "DATE", "YMD", "일자", "날짜")


@dataclass
class ApiConfig:
    source_id: str
    value: str  # API 주소 또는 식품안전나라 서비스 ID
    key: str
    style: str  # foodsafety | datagokr


def env_names(source_id: str) -> tuple[str, str]:
    prefix = source_id.upper()
    return f"{prefix}_API", f"{prefix}_API_KEY"


def config_for(source_id: str, cfg: dict[str, Any] | None = None) -> ApiConfig | None:
    """.env(+ sources.json api.service)에서 이 출처의 API 설정을 읽는다. 없으면 None."""
    get_settings()  # .env를 읽어 os.environ에 올린다 (core/config.py)
    api_env, key_env = env_names(source_id)
    service = str(((cfg or {}).get("api") or {}).get("service") or "")
    value = os.environ.get(api_env, "").strip() or service.strip()
    if not value:
        return None
    style = "datagokr" if "://" in value and "foodsafetykorea" not in value else "foodsafety"
    shared = "FOODSAFETY_API_KEY" if style == "foodsafety" else "DATA_GO_KR_SERVICE_KEY"
    key = os.environ.get(key_env, "").strip() or os.environ.get(shared, "").strip()
    if not key:
        return None
    if style == "foodsafety" and "://" in value:
        value = value.rstrip("/").rsplit("/", 1)[-1]  # 주소를 넣었으면 끝의 서비스 ID만 쓴다
    return ApiConfig(source_id=source_id, value=value, key=key, style=style)


def _json(text: str) -> Any:
    try:
        return json.loads(text)
    except ValueError as e:
        raise web.CollectHttpError(f"API 응답이 JSON이 아님: {text[:150]}") from e


def _find_rows(data: Any) -> list[dict[str, Any]]:
    """응답 안에서 첫 번째 dict 목록을 찾는다.

    response.body.items.item 등 모양이 API마다 다르다.
    """
    if isinstance(data, list):
        if data and all(isinstance(x, dict) for x in data):
            return data
        for x in data:
            found = _find_rows(x)
            if found:
                return found
        return []
    if isinstance(data, dict):
        item = data.get("item")
        if isinstance(item, dict):
            return [item]  # 결과가 1건이면 item이 목록이 아니라 dict로 오는 API가 있다
        for v in data.values():
            if isinstance(v, (dict, list)):
                found = _find_rows(v)
                if found:
                    return found
    return []


def _foodsafety_pages(cfg: ApiConfig) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for page in range(MAX_PAGES):
        lo, hi = page * FOODSAFETY_PAGE + 1, (page + 1) * FOODSAFETY_PAGE
        url = f"{FOODSAFETY_BASE}/{cfg.key}/{cfg.value}/json/{lo}/{hi}"
        data = _json(web.get(url).text)
        body = data.get(cfg.value, {}) if isinstance(data, dict) else {}
        result = body.get("RESULT") or (data.get("RESULT") if isinstance(data, dict) else None)
        code = str((result or {}).get("CODE", ""))
        if code and code not in ("INFO-000", "INFO-200"):
            raise web.CollectHttpError(f"식품안전나라 API {code}: {(result or {}).get('MSG', '')}")
        part = body.get("row") or []
        rows += part
        total = int(body.get("total_count") or 0)
        if not part or hi >= total:
            break
    return rows


def _datagokr_pages(cfg: ApiConfig) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for page in range(1, MAX_PAGES + 1):
        params = {
            "serviceKey": cfg.key,
            "pageNo": str(page),
            "numOfRows": str(DATAGO_PAGE),
            "type": "json",
        }
        data = _json(web.get(cfg.value, params).text)
        header = data.get("response", {}).get("header", {}) if isinstance(data, dict) else {}
        code = str(header.get("resultCode", "00"))
        if code not in ("00", "0", "000"):
            raise web.CollectHttpError(f"공공데이터 API {code}: {header.get('resultMsg', '')}")
        part = _find_rows(data)
        rows += part
        if len(part) < DATAGO_PAGE:
            break
    return rows


def _pick(item: dict[str, Any], name: str | None) -> str:
    if not name:
        return ""
    v = item.get(name)
    return "" if v is None else str(v).strip()


def parse_date(value: str) -> date | None:
    """'20261120', '2026-11-20', '2026.11.20 10:00' 등 → date."""
    m = re.search(r"(20\d\d)[-./]?(\d\d)[-./]?(\d\d)", value or "")
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def _guess(item: dict[str, Any], hints: tuple[str, ...], want_date: bool) -> str:
    for k, v in item.items():
        if v in (None, "") or isinstance(v, (dict, list)):
            continue
        if any(h in k.upper() or h in k for h in hints):
            if not want_date or parse_date(str(v)):
                return str(v).strip()
    return ""


def to_row(item: dict[str, Any], mapping: dict[str, Any]) -> dict[str, Any]:
    """API 한 줄 → base.py 행 형식. 값은 API 원문 그대로 둔다."""
    fields_map: dict[str, str] = mapping.get("fields") or {}
    if fields_map:
        fields = {ours: _pick(item, theirs) for ours, theirs in fields_map.items()}
    else:
        fields = {
            k: str(v).strip()
            for k, v in item.items()
            if v not in (None, "") and not isinstance(v, (dict, list))
        }
    title = _pick(item, mapping.get("title")) or _guess(item, _TITLE_HINTS, want_date=False)
    day_raw = _pick(item, mapping.get("date")) or _guess(item, _DATE_HINTS, want_date=True)
    day = parse_date(day_raw)
    return {
        "key": _pick(item, mapping.get("key")) or None,
        "title": title or "(제목 칸 확인 필요)",
        "posted_at": day.isoformat() if day else None,
        "url": _pick(item, mapping.get("url")) or None,
        "body": _pick(item, mapping.get("body")),
        "fields": {k: v for k, v in fields.items() if v},
    }


def fetch_rows(cfg: ApiConfig, mapping: dict[str, Any]) -> list[dict[str, Any]]:
    items = _foodsafety_pages(cfg) if cfg.style == "foodsafety" else _datagokr_pages(cfg)
    return [to_row(i, mapping) for i in items]


def collect(
    source_id: str, run_id: int, start: date, end: date, cfg: dict[str, Any]
) -> CollectResult:
    """출처 공통 순서: API 설정이 있으면 API, 없으면 수동 업로드(더미는 mode=demo만)."""
    if cfg.get("mode") == "demo":
        return load_demo(source_id, demo_path(cfg), run_id, start, end)
    api = config_for(source_id, cfg)
    if api is None:
        return CollectResult(source=source_id, status="manual", message=NO_API_NOTE)
    mapping: dict[str, Any] = (cfg.get("api") or {}).get("map") or {}
    rows = fetch_rows(
        api, mapping
    )  # 실패하면 오류가 그대로 올라가 service.collect가 "수집 실패"로 남긴다
    return rows_to_result(source_id, rows, run_id, start, end, label="API")


def uses_api(source_id: str, cfg: dict[str, Any]) -> bool:
    """이번 수집이 실제 API에서 온 것인지 (서버 DB에 올릴지 정할 때 쓴다)."""
    return cfg.get("mode") != "demo" and config_for(source_id, cfg) is not None
