"""구글 인증 공통 (Gmail·Drive, C-05). token.json 방식 (기존 도구와 같음).

- 처음 한 번: `cd backend && .venv\\Scripts\\python -m app.core.gmail_client`
  → 브라우저 로그인 → `GOOGLE_TOKEN_FILE`(token.json) 생성.
- 서버는 브라우저를 띄우지 않는다. 토큰이 없거나 권한이 모자라면 GoogleAuthError로 이유를 알린다.
- 로그인은 SCOPES 전부를 한 번에 받는다. 쓰는 곳은 필요한 권한만 get_credentials(scopes)로 요청한다
  (드라이브 읽기는 DRIVE_READ, 드라이브 올리기는 DRIVE_FILE, Gmail 임시보관함·발송은 GMAIL_COMPOSE).
- 권한을 더했으면 token.json을 지우고(또는 그대로 두고) 다시 로그인해야 새 권한이 들어온다.
- OAuth 클라이언트는 .env의 GOOGLE_CLIENT_ID·GOOGLE_CLIENT_SECRET에서 읽는다.
  둘 다 비었으면 예전 방식(GOOGLE_CREDENTIALS_FILE, credentials.json)을 쓴다.
- .env·credentials.json·token.json은 커밋하지 않는다(.gitignore).
"""

import json

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from app.core.config import get_settings

DRIVE_READ = "https://www.googleapis.com/auth/drive.readonly"  # 고객사 목록·법령 자료 읽기
DRIVE_FILE = "https://www.googleapis.com/auth/drive.file"  # 확정 보고서·보낸 메일 올리기 (B2-08)
GMAIL_COMPOSE = "https://www.googleapis.com/auth/gmail.compose"  # 임시보관함 저장·발송 (B2-05)
# 로그인 때 받는 권한 전부. 범위를 더하면 사람이 다시 로그인해야 한다.
# 보관 폴더에 drive.file로 올리지 못하면(남이 만든 폴더) drive 전체 권한으로 넓히는 것을 검토한다.
SCOPES: list[str] = [DRIVE_READ, DRIVE_FILE, GMAIL_COMPOSE]

LOGIN_HINT = (
    "backend 폴더에서 `.venv\\Scripts\\python -m app.core.gmail_client`로 구글 로그인을 해 주세요."
)


CLIENT_HINT = (
    "구글 OAuth 클라이언트 정보가 없습니다. .env에 GOOGLE_CLIENT_ID와 GOOGLE_CLIENT_SECRET을 "
    "넣어 주세요(구글 클라우드 → OAuth 클라이언트 ID → 데스크톱 앱). "
    "예전 방식인 credentials.json 파일을 저장소 맨 위 폴더에 두어도 됩니다."
)
AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URI = "https://oauth2.googleapis.com/token"


class GoogleAuthError(Exception):
    pass


def client_config() -> dict[str, dict[str, object]] | None:
    """.env의 GOOGLE_CLIENT_ID·SECRET으로 OAuth 클라이언트 정보를 메모리에서 만든다.

    둘 중 하나라도 비면 None → login()은 예전 방식(credentials.json)을 쓴다.
    시크릿 값은 파일·로그에 쓰지 않는다.
    """
    s = get_settings()
    if not (s.google_client_id and s.google_client_secret):
        return None
    return {
        "installed": {
            "client_id": s.google_client_id,
            "client_secret": s.google_client_secret,
            "auth_uri": AUTH_URI,
            "token_uri": TOKEN_URI,
            "redirect_uris": ["http://localhost"],
        }
    }


def get_credentials(scopes: list[str] | None = None) -> Credentials:
    """저장된 token.json을 읽고, 만료됐으면 갱신한다.

    scopes를 안 주면 드라이브 읽기(DRIVE_READ)만 요청한다. 예전 토큰(읽기 권한만)도 그대로 쓴다.
    """
    need = scopes or [DRIVE_READ]
    token = get_settings().google_token_file
    if not token.exists():
        raise GoogleAuthError(f"구글 로그인 토큰({token.name})이 없습니다. {LOGIN_HINT}")
    info = json.loads(token.read_text(encoding="utf-8"))
    granted = info.get("scopes")
    if isinstance(granted, str):
        granted = granted.split()
    if granted is not None and not set(need) <= set(granted):
        missing = ", ".join(sorted(set(need) - set(granted)))
        raise GoogleAuthError(f"구글 토큰에 필요한 권한이 없습니다({missing}). 다시 {LOGIN_HINT}")
    creds = Credentials.from_authorized_user_info(info, need)
    if creds.valid:
        return creds
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except RefreshError as e:
            raise GoogleAuthError(f"구글 토큰 갱신 실패. {LOGIN_HINT}") from e
        token.write_text(creds.to_json(), encoding="utf-8")
        return creds
    raise GoogleAuthError(f"구글 토큰이 유효하지 않습니다. {LOGIN_HINT}")


def login(scopes: list[str] | None = None) -> Credentials:
    """브라우저로 OAuth 로그인 후 token.json 저장. 사람이 터미널에서 한 번 실행한다."""
    from google_auth_oauthlib.flow import InstalledAppFlow

    s = get_settings()
    config = client_config()
    if config is not None:
        flow = InstalledAppFlow.from_client_config(config, scopes or SCOPES)
    elif s.google_credentials_file.exists():
        flow = InstalledAppFlow.from_client_secrets_file(
            str(s.google_credentials_file), scopes or SCOPES
        )
    else:
        raise GoogleAuthError(CLIENT_HINT)
    creds = flow.run_local_server(port=0)
    s.google_token_file.write_text(creds.to_json(), encoding="utf-8")
    return creds


if __name__ == "__main__":
    login()
    print(f"구글 로그인 완료 → {get_settings().google_token_file}")
