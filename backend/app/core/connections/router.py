"""연결 설정 (C-01, KHS). 외부 연결마다 상태 + 연결 검사. 키·토큰 값은 돌려주지 않는다."""

from fastapi import APIRouter

from app.core.connections import service
from app.core.connections.service import ConnId, ConnStatus

router = APIRouter(prefix="/connections", tags=["core: connections"])


@router.get("", response_model=list[ConnStatus])
def get_all() -> list[ConnStatus]:
    return service.status_all()


@router.post("/{conn_id}/test", response_model=ConnStatus)
def post_test(conn_id: ConnId) -> ConnStatus:
    return service.test(conn_id)
