"""로그인 확인 (C-08). main.py에서 core 일부·b1·b2 라우터 전체에 한 번에 건다.

각 기능 폴더에서 따로 걸지 않는다. 로그인한 사용자 이름이 필요하면
`user: Annotated[str, Depends(require_login)]`로 받는다(예: 메일 승인 approved_by).
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.auth.service import verify_token

_bearer = HTTPBearer(auto_error=False)


def require_login(
    cred: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> str:
    username = verify_token(cred.credentials) if cred else None
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인이 필요합니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username


def current_token(
    cred: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> str | None:
    return cred.credentials if cred else None
