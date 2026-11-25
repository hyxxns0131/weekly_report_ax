"""Supabase 공개 정보 읽기·쓰기 (C-04, KHS).

- 읽기: SUPABASE_ANON_KEY(팀원 publishable 키). RLS로 SELECT만 된다.
- 쓰기: SUPABASE_SERVICE_ROLE_KEY(secret 키)가 있는 PC(HS)에서만. 없으면 쓰기를 건너뛴다.
- 공개 정보만 보낸다. 고객사명·매칭 결과·메일 본문은 절대 보내지 않는다 (AGENTS.md 5-1).
"""

from typing import Any

import httpx

from app.core.config import get_settings

TIMEOUT = 15.0


class SupabaseNotConfiguredError(Exception):
    pass


def _headers(write: bool) -> dict[str, str]:
    s = get_settings()
    key = (
        s.supabase_service_role_key
        if write
        else (s.supabase_anon_key or s.supabase_service_role_key)
    )
    if not (s.supabase_url and key):
        raise SupabaseNotConfiguredError(".env에 SUPABASE_URL과 키를 넣어 주세요.")
    return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def can_write() -> bool:
    s = get_settings()
    return bool(s.supabase_url and s.supabase_service_role_key)


def select(table: str, params: dict[str, str] | None = None) -> list[dict[str, Any]]:
    url = f"{get_settings().supabase_url}/rest/v1/{table}"
    res = httpx.get(
        url, headers=_headers(write=False), params=params or {"select": "*"}, timeout=TIMEOUT
    )
    res.raise_for_status()
    data: list[dict[str, Any]] = res.json()
    return data


def upsert(table: str, rows: list[dict[str, Any]]) -> int:
    """PM(HS) PC에서만 동작. 키가 없으면 0을 돌려주고 아무것도 하지 않는다."""
    if not rows or not can_write():
        return 0
    url = f"{get_settings().supabase_url}/rest/v1/{table}"
    headers = {**_headers(write=True), "Prefer": "resolution=merge-duplicates"}
    res = httpx.post(url, headers=headers, json=rows, timeout=TIMEOUT)
    res.raise_for_status()
    return len(rows)
