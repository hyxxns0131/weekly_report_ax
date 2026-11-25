"""로그인 (C-08). 관리자 계정 1개, 값은 .env(ADMIN_USERNAME, ADMIN_PASSWORD)에만 있다.

토큰 형식: base64url("<username>|<만료 epoch>|<무작위>") + "." + HMAC-SHA256 서명.
서명 키는 AUTH_SECRET_KEY. 키를 바꾸면 모든 로그인이 풀린다.
로그아웃한 토큰은 서버가 켜져 있는 동안 메모리에서 막는다.
"""

import base64
import hashlib
import hmac
import secrets
import time

from app.core.config import get_settings

_revoked: set[str] = set()


class LoginNotConfiguredError(Exception):
    """.env에 로그인 값이 비어 있다."""


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _sign(payload: str, key: str) -> str:
    return _b64(hmac.new(key.encode(), payload.encode(), hashlib.sha256).digest())


def check_credentials(username: str, password: str) -> bool:
    s = get_settings()
    if not s.login_configured:
        raise LoginNotConfiguredError
    user_ok = secrets.compare_digest(username.encode(), s.admin_username.encode())
    pass_ok = secrets.compare_digest(password.encode(), s.admin_password.encode())
    return user_ok and pass_ok


def issue_token(username: str) -> tuple[str, int]:
    s = get_settings()
    expires_at = int(time.time()) + s.auth_session_hours * 3600
    payload = _b64(f"{username}|{expires_at}|{secrets.token_urlsafe(8)}".encode())
    return f"{payload}.{_sign(payload, s.auth_secret_key)}", expires_at


def verify_token(token: str) -> str | None:
    """맞는 토큰이면 사용자 이름, 아니면 None."""
    s = get_settings()
    if not s.login_configured or token in _revoked or "." not in token:
        return None
    payload, sig = token.rsplit(".", 1)
    if not secrets.compare_digest(sig, _sign(payload, s.auth_secret_key)):
        return None
    try:
        username, expires_at, _ = _unb64(payload).decode().split("|", 2)
        if int(expires_at) < time.time():
            return None
    except ValueError:
        return None
    return username


def revoke_token(token: str) -> None:
    _revoked.add(token)
