"""외부 연결 상태·연결 검사 (C-01, KHS). 설정 > 연결 설정 화면용.

- 연결마다 "설정 있음/없음" 상태와 [연결 검사] 결과를 돌려준다.
  키·토큰·계정 값은 절대 돌려주지 않는다.
- 검사는 읽기만 한다(목록 1건 조회 등). 쓰기·발송·토큰 소모를 하지 않는다.
- 마지막 검사 결과는 `DATA_DIR/connections.json`(커밋 안 함)에 남긴다.
- AI(OpenAI·Claude)는 core/llm.py의 상태·검사를 그대로 쓴다.
"""

import json
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any, Literal
from zoneinfo import ZoneInfo

import httpx
from pydantic import BaseModel

from app.core import llm
from app.core.config import get_settings

ConnId = Literal["ai", "supabase_read", "supabase_write", "google_drive", "gmail", "law_api"]
ConnState = Literal["off", "no_key", "ready", "ok", "error"]

TIMEOUT = 15.0
GMAIL_SCOPE_PREFIX = "https://www.googleapis.com/auth/gmail"

STATE_LABEL: dict[ConnState, str] = {
    "off": "사용 안 함",
    "no_key": "설정 없음",
    "ready": "연결 확인 전",
    "ok": "연결됨",
    "error": "연결 실패",
}


class ConnTest(BaseModel):
    ok: bool
    message: str
    checked_at: str
    elapsed_ms: int


class ConnStatus(BaseModel):
    id: ConnId
    name: str
    usage: str  # 어디에 쓰는지
    env_names: list[str]  # .env 변수 이름(값은 보내지 않음)
    configured: bool
    state: ConnState
    state_label: str
    hint: str  # 설정이 없을 때 할 일
    last_test: ConnTest | None = None


class _Def(BaseModel):
    id: ConnId
    name: str
    usage: str
    env_names: list[str]


DEFS: list[_Def] = [
    _Def(
        id="ai",
        name="AI (OpenAI·Claude)",
        usage="선별·정보 추출·법령 요지 요약·메일 초안",
        env_names=["LLM_ENABLED", "AI_PROVIDER", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"],
    ),
    _Def(
        id="supabase_read",
        name="Supabase 읽기",
        usage="공개 정보(법령 개정·부적합·검사지시 원문) 불러오기",
        env_names=["SUPABASE_URL", "SUPABASE_ANON_KEY"],
    ),
    _Def(
        id="supabase_write",
        name="Supabase 쓰기 (PM만)",
        usage="공개 정보 적재, 과거 보고서 정답(비공개 표) 읽기",
        env_names=["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"],
    ),
    _Def(
        id="google_drive",
        name="구글 드라이브",
        usage="고객사 목록·키워드, 법령자료 폴더 읽기, 확정 보고서 보관",
        env_names=[
            "GOOGLE_CLIENT_ID",
            "GOOGLE_CLIENT_SECRET",
            "GOOGLE_TOKEN_FILE",
            "DRIVE_LAW_FOLDER_ID",
        ],
    ),
    _Def(
        id="gmail",
        name="Gmail",
        usage="공문·뉴스레터 받기(B1-07), 승인 후 발송(B2-05)",
        env_names=["GOOGLE_TOKEN_FILE", "GMAIL_INBOX_QUERY", "GMAIL_SENDER"],
    ),
    _Def(
        id="law_api",
        name="법제처 OPEN API",
        usage="법령·고시 개정 수집",
        env_names=["LAW_API_OC"],
    ),
]


class CheckFailed(Exception):
    pass


# ── 저장 ─────────────────────────────────────────────


def _file() -> Path:
    return get_settings().data_dir / "connections.json"


def _load() -> dict[str, Any]:
    f = _file()
    if not f.exists():
        return {}
    try:
        data: dict[str, Any] = json.loads(f.read_text(encoding="utf-8"))
        return data
    except (OSError, ValueError):
        return {}


def _save_test(cid: ConnId, test: ConnTest) -> None:
    data = _load()
    data[cid] = test.model_dump()
    f = _file()
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _now() -> str:
    tz = ZoneInfo(get_settings().tz_name)
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")


# ── 설정 여부 ────────────────────────────────────────


def _configured(cid: ConnId) -> tuple[bool, str]:
    """(설정 있음, 없을 때 안내)."""
    s = get_settings()
    if cid == "supabase_read":
        ok = bool(s.supabase_url and (s.supabase_anon_key or s.supabase_service_role_key))
        return ok, ".env에 SUPABASE_URL과 SUPABASE_ANON_KEY(publishable 키)를 넣어 주세요."
    if cid == "supabase_write":
        ok = bool(s.supabase_url and s.supabase_service_role_key)
        return ok, "PM(KHS) PC에서만 씁니다. 팀원은 비워 두면 됩니다."
    if cid in ("google_drive", "gmail"):
        return (
            s.google_token_file.exists(),
            "구글 로그인 토큰이 없습니다. backend 폴더에서 "
            "`python -m app.core.gmail_client`로 로그인해 주세요.",
        )
    if cid == "law_api":
        return bool(s.law_api_oc), ".env에 LAW_API_OC(법제처 OPEN API 아이디)를 넣어 주세요."
    return True, ""


# ── 검사 ─────────────────────────────────────────────


def _check_supabase(write: bool) -> str:
    s = get_settings()
    key = s.supabase_service_role_key if write else (s.supabase_anon_key or "")
    if not write and not key:
        key = s.supabase_service_role_key
    # 쓰기 키는 비공개 표를 읽어 본다(secret 키로만 읽힌다). 아무것도 쓰지 않는다.
    table = "past_report" if write else "pub_law_change"
    try:
        res = httpx.get(
            f"{s.supabase_url.rstrip('/')}/rest/v1/{table}",
            headers={"apikey": key, "Authorization": f"Bearer {key}"},
            params={"select": "id", "limit": "1"},
            timeout=TIMEOUT,
        )
    except httpx.HTTPError as e:
        raise CheckFailed(
            "Supabase 서버에 접속하지 못했습니다. 인터넷·방화벽을 확인해 주세요."
        ) from e
    if res.status_code in (401, 403):
        raise CheckFailed("키가 맞지 않습니다. 대시보드의 API Keys에서 키를 다시 확인해 주세요.")
    if res.status_code == 404:
        raise CheckFailed(f"표 '{table}'을 찾지 못했습니다. URL이 맞는지 확인해 주세요.")
    if res.status_code >= 400:
        raise CheckFailed(f"Supabase 오류 (HTTP {res.status_code})")
    return "읽기 성공" if not write else "secret 키 확인 (비공개 표 읽기 성공)"


def _google_creds(scopes: list[str] | None = None) -> Any:
    from app.core.gmail_client import GoogleAuthError, get_credentials

    try:
        return get_credentials(scopes)
    except GoogleAuthError as e:
        raise CheckFailed(str(e)) from e


def _check_drive() -> str:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError

    creds = _google_creds()
    try:
        svc = build("drive", "v3", credentials=creds, cache_discovery=False)
        svc.files().list(pageSize=1, fields="files(id)").execute()
        folder = get_settings().drive_law_folder_id
        if folder:
            svc.files().get(fileId=folder, fields="id", supportsAllDrives=True).execute()
            return "드라이브 읽기 성공 · 법령자료 폴더 열림"
    except HttpError as e:
        status = getattr(e.resp, "status", "?")
        if str(status) == "404":
            raise CheckFailed("DRIVE_LAW_FOLDER_ID 폴더를 열 수 없습니다. ID·공유 권한 확인") from e
        raise CheckFailed(f"드라이브 오류 (HTTP {status})") from e
    except Exception as e:  # 네트워크 등
        raise CheckFailed(f"드라이브에 접속하지 못했습니다: {type(e).__name__}") from e
    return "드라이브 읽기 성공"


def _check_gmail() -> str:
    from google.oauth2.credentials import Credentials

    token = get_settings().google_token_file
    try:
        creds = Credentials.from_authorized_user_file(str(token))
    except (OSError, ValueError) as e:
        raise CheckFailed("구글 로그인 토큰을 읽지 못했습니다.") from e
    if not any(sc.startswith(GMAIL_SCOPE_PREFIX) for sc in (creds.scopes or [])):
        raise CheckFailed(
            "구글 로그인은 되어 있지만 Gmail 권한이 아직 없습니다. "
            "권한을 더한 뒤 다시 로그인해 주세요: "
            "backend 폴더에서 `.venv\\Scripts\\python -m app.core.gmail_client`"
        )
    return "Gmail 권한 있음"


def _check_law() -> str:
    # core는 b1 코드를 import하지 않는다. 같은 주소로 1건만 조회한다.
    s = get_settings()
    try:
        res = httpx.get(
            "https://www.law.go.kr/DRF/lawSearch.do",
            params={
                "OC": s.law_api_oc,
                "type": "JSON",
                "target": "admrul",
                "query": "식품",
                "display": "1",
            },
            headers={"User-Agent": s.collect_user_agent},
            timeout=TIMEOUT,
        )
    except httpx.HTTPError as e:
        raise CheckFailed(
            "법제처 서버에 접속하지 못했습니다. 인터넷·방화벽을 확인해 주세요."
        ) from e
    if "사용자 정보 검증에 실패" in res.text:
        raise CheckFailed("법제처 API: 사용자 정보 검증 실패. 등록 IP·OC 확인 필요")
    if res.status_code >= 400:
        raise CheckFailed(f"법제처 API 오류 (HTTP {res.status_code})")
    try:
        res.json()
    except ValueError as e:
        raise CheckFailed("법제처 API 응답을 읽지 못했습니다.") from e
    return "법제처 API 응답 정상"


CHECKS: dict[ConnId, Callable[[], str]] = {
    "supabase_read": lambda: _check_supabase(write=False),
    "supabase_write": lambda: _check_supabase(write=True),
    "google_drive": _check_drive,
    "gmail": _check_gmail,
    "law_api": _check_law,
}


# ── 공개 함수 ────────────────────────────────────────


def _ai_status(d: _Def) -> ConnStatus:
    st = llm.status()
    state: ConnState = {
        "off": "off",
        "no_key": "no_key",
        "no_model": "no_key",
        "ready": "ready",
        "ok": "ok",
        "error": "error",
    }[st.state]  # type: ignore[assignment]
    last = (
        ConnTest(
            ok=st.last_test.ok,
            message=st.last_test.message,
            checked_at=st.last_test.checked_at,
            elapsed_ms=st.last_test.elapsed_ms,
        )
        if st.last_test
        else None
    )
    return ConnStatus(
        **d.model_dump(),
        configured=state not in ("off", "no_key"),
        state=state,
        state_label=st.state_label,
        hint="" if state not in ("off", "no_key") else st.state_label,
        last_test=last,
    )


def status_one(cid: ConnId) -> ConnStatus:
    d = next(x for x in DEFS if x.id == cid)
    if cid == "ai":
        return _ai_status(d)
    configured, hint = _configured(cid)
    saved = _load().get(cid)
    last = ConnTest(**saved) if isinstance(saved, dict) else None
    state: ConnState
    if not configured:
        state = "no_key"
    elif last is None:
        state = "ready"
    else:
        state = "ok" if last.ok else "error"
    return ConnStatus(
        **d.model_dump(),
        configured=configured,
        state=state,
        state_label=STATE_LABEL[state],
        hint="" if configured else hint,
        last_test=last,
    )


def status_all() -> list[ConnStatus]:
    return [status_one(d.id) for d in DEFS]


def test(cid: ConnId) -> ConnStatus:
    if cid == "ai":
        llm.test_connection()
        return status_one(cid)
    configured, hint = _configured(cid)
    start = time.monotonic()
    if not configured:
        ok, msg = False, hint
    else:
        try:
            ok, msg = True, CHECKS[cid]()
        except CheckFailed as e:
            ok, msg = False, str(e)
    _save_test(
        cid,
        ConnTest(
            ok=ok,
            message=msg,
            checked_at=_now(),
            elapsed_ms=int((time.monotonic() - start) * 1000),
        ),
    )
    return status_one(cid)
