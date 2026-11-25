"""구글 인증 공통 (Gmail·Drive, C-05). token.json 방식 (기존 도구와 같음).

- 처음 한 번: `cd backend && .venv\\Scripts\\python -m app.core.gmail_client`
  → 브라우저 로그인 → `GOOGLE_TOKEN_FILE`(token.json) 생성.
- 서버는 브라우저를 띄우지 않는다. 토큰이 없거나 권한이 모자라면 GoogleAuthError로 이유를 알린다.
- credentials.json·token.json은 커밋하지 않는다(.gitignore).
"""

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from app.core.config import get_settings

# 지금은 드라이브 읽기만. Gmail(B1-07, B2-05)을 붙일 때 여기에 범위를 더하고 다시 로그인한다.
SCOPES: list[str] = ["https://www.googleapis.com/auth/drive.readonly"]

LOGIN_HINT = (
    "backend 폴더에서 `.venv\\Scripts\\python -m app.core.gmail_client`로 구글 로그인을 해 주세요."
)


class GoogleAuthError(Exception):
    pass


def get_credentials(scopes: list[str] | None = None) -> Credentials:
    """저장된 token.json을 읽고, 만료됐으면 갱신한다."""
    need = scopes or SCOPES
    token = get_settings().google_token_file
    if not token.exists():
        raise GoogleAuthError(f"구글 로그인 토큰({token.name})이 없습니다. {LOGIN_HINT}")
    creds = Credentials.from_authorized_user_file(str(token), need)
    if creds.scopes is not None and not set(need) <= set(creds.scopes):
        raise GoogleAuthError(f"구글 토큰에 필요한 권한이 없습니다. {LOGIN_HINT}")
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
    if not s.google_credentials_file.exists():
        raise GoogleAuthError(
            f"{s.google_credentials_file.name}이 없습니다. 구글 클라우드에서 OAuth 데스크톱 앱 "
            "클라이언트를 만들어 받은 파일을 저장소 맨 위 폴더에 두세요."
        )
    flow = InstalledAppFlow.from_client_secrets_file(
        str(s.google_credentials_file), scopes or SCOPES
    )
    creds = flow.run_local_server(port=0)
    s.google_token_file.write_text(creds.to_json(), encoding="utf-8")
    return creds


if __name__ == "__main__":
    login()
    print(f"구글 로그인 완료 → {get_settings().google_token_file}")
