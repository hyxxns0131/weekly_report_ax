"""b1(제안서 5번) 하위 라우터 등록 (기능 7개 + 분석 연결 pipeline). LSH 소유, 1일차 뒤 고정.

엔드포인트는 각 기능 폴더의 router.py에만 추가한다. 로그인 확인은 main.py에서 건다.
"""

from fastapi import APIRouter

from app.b1_select import pipeline, result
from app.b1_select.classify import router as classify
from app.b1_select.collect import router as collect
from app.b1_select.extract import router as extract
from app.b1_select.law import router as law
from app.b1_select.match import router as match
from app.b1_select.settings import router as settings

router = APIRouter()
router.include_router(collect.router, tags=["b1: collect B1-01~07"])
router.include_router(classify.router, tags=["b1: classify B1-08"])
router.include_router(extract.router, tags=["b1: extract B1-09"])
router.include_router(match.router, tags=["b1: match B1-11"])
router.include_router(law.router, tags=["b1: law B1-12~14"])
router.include_router(settings.router, tags=["b1: settings B1-15"])
router.include_router(pipeline.router, tags=["b1: analyze B1-08~11"])
router.include_router(result.router, tags=["b1: result"])
