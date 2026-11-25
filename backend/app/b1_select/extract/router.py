"""B1-09 추출 수정 엔드포인트."""

from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.b1_select import pipeline
from app.core.schema import ExtractedInfo
from app.core.storage import repo

router = APIRouter()


class ExtractedPatch(BaseModel):
    product_name_ko: str | None = None
    product_name_en: str | None = None
    food_type_raw: str | None = None
    food_type_std: str | None = None
    origin_country: str | None = None
    export_country: str | None = None
    maker: str | None = None
    hs_code: str | None = None
    violation: str | None = None
    action: str | None = None
    office: str | None = None
    period_start: date | None = None
    period_end: date | None = None


@router.patch("/items/{item_id}/extracted", response_model=ExtractedInfo)
def patch_extracted(item_id: str, body: ExtractedPatch) -> ExtractedInfo:
    raw = repo.get_raw(item_id)
    if raw is None:
        raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다.")
    info = repo.get_extracted(item_id) or ExtractedInfo(item_id=item_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(info, field, value or None)
        if field not in info.edited_fields:
            info.edited_fields.append(field)
    repo.save_extracted(info)
    pipeline.after_extracted(raw.run_id, item_id)
    return info
