"""로그인 엔드포인트 (C-08). /api/core/auth/login만 로그인 없이 부를 수 있다."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.auth import service
from app.core.auth.deps import current_token, require_login

router = APIRouter(prefix="/auth", tags=["core: auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    username: str
    expires_at: int


class Me(BaseModel):
    username: str


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest) -> LoginResponse:
    try:
        ok = service.check_credentials(body.username, body.password)
    except service.LoginNotConfiguredError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=".env에 ADMIN_USERNAME, ADMIN_PASSWORD, AUTH_SECRET_KEY를 채워 주세요.",
        ) from e
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 맞지 않습니다.",
        )
    token, expires_at = service.issue_token(body.username)
    return LoginResponse(token=token, username=body.username, expires_at=expires_at)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    _: Annotated[str, Depends(require_login)],
    token: Annotated[str | None, Depends(current_token)],
) -> None:
    if token:
        service.revoke_token(token)


@router.get("/me", response_model=Me)
def me(username: Annotated[str, Depends(require_login)]) -> Me:
    return Me(username=username)
