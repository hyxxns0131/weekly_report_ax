"""FastAPI 시작점 (C-01). KHS 고정 파일: 바꿀 일이 있으면 PR "변경 요청"에 적는다.

라우터는 /api/core, /api/b1, /api/b2 세 개만 등록한다.
로그인(C-08): /api/core/health, /api/core/auth/login 두 개만 로그인 없이 열려 있고,
나머지는 모두 require_login을 여기서 한 번에 건다.
실행: backend 폴더에서 `uvicorn app.main:app --reload`
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.b1_select.router import router as b1_router
from app.b2_mail.router import router as b2_router
from app.core.ai.router import router as ai_router
from app.core.auth.deps import require_login
from app.core.auth.router import router as auth_router
from app.core.config import get_settings
from app.core.runs.router import router as runs_router
from app.core.storage.local_db import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()  # 로컬 DB 테이블이 없으면 만든다 (schema.sql, KHS)
    yield


app = FastAPI(title="수입식품 주간 검역 보고서", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Health(BaseModel):
    status: str
    llm_enabled: bool
    login_configured: bool


core_router = APIRouter()


@core_router.get("/health", response_model=Health)
def health() -> Health:
    return Health(
        status="ok",
        llm_enabled=settings.llm_enabled,
        login_configured=settings.login_configured,
    )


core_router.include_router(auth_router)  # login만 열림, logout·me는 각자 require_login
core_router.include_router(runs_router, dependencies=[Depends(require_login)])
core_router.include_router(ai_router, dependencies=[Depends(require_login)])

app.include_router(core_router, prefix="/api/core")
app.include_router(b1_router, prefix="/api/b1", dependencies=[Depends(require_login)])
app.include_router(b2_router, prefix="/api/b2", dependencies=[Depends(require_login)])
