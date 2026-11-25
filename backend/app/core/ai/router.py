"""AI 연결 상태·연결 검사·모델 선택 (C-02). 키 값은 절대 돌려주지 않는다."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core import llm

router = APIRouter(prefix="/ai", tags=["core: ai"])


class AiChoice(BaseModel):
    provider: llm.Provider
    model: str


@router.get("/status", response_model=llm.AiStatus)
def get_status() -> llm.AiStatus:
    return llm.status()


@router.put("/settings", response_model=llm.AiStatus)
def put_settings(body: AiChoice) -> llm.AiStatus:
    model = body.model.strip()
    if len(model) > 100 or any(c.isspace() for c in model):
        raise HTTPException(422, "모델 이름이 올바르지 않습니다")
    llm.set_choice(body.provider, model)
    return llm.status()


@router.post("/test", response_model=llm.AiTest)
def post_test() -> llm.AiTest:
    return llm.test_connection()
