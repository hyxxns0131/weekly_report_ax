"""B1-15 출처·고객사 키워드 설정 엔드포인트."""

from fastapi import APIRouter

from app.b1_select.match.customers import Customer
from app.b1_select.settings import customers, sources

router = APIRouter(prefix="/settings")


@router.get("/sources", response_model=list[sources.SourceSetting])
def get_sources() -> list[sources.SourceSetting]:
    return sources.load()


@router.put("/sources", response_model=list[sources.SourceSetting])
def put_sources(body: list[sources.SourceSetting]) -> list[sources.SourceSetting]:
    return sources.save(body)


@router.get("/customers", response_model=list[Customer])
def get_customers() -> list[Customer]:
    return customers.load()
