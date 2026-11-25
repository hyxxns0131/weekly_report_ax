"""b2(제안서 6번) 하위 라우터 5개 등록. KHW 소유, 1일차 뒤 고정.

엔드포인트는 각 기능 폴더의 router.py에만 추가한다. 로그인 확인은 main.py에서 건다.
"""

from fastapi import APIRouter

from app.b2_mail.draft import router as draft
from app.b2_mail.evaluate import router as evaluate
from app.b2_mail.report import router as report
from app.b2_mail.send import router as send
from app.b2_mail.tips import router as tips

router = APIRouter()
router.include_router(report.router, tags=["b2: report B2-01"])
router.include_router(draft.router, tags=["b2: draft B2-02~04"])
router.include_router(send.router, tags=["b2: send B2-05·08"])
router.include_router(evaluate.router, tags=["b2: evaluate B2-06"])
router.include_router(tips.router, tags=["b2: tips B2-07"])
