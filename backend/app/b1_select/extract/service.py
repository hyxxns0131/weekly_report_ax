"""B1-09 정보 추출.

순서: 표 형식("열 이름: 값" 줄)은 table_mapper(LLM 없이) → 본문형은 "칸: 값" 패턴 →
LLM 추출(llm_extractor, 준비 후). 못 찾은 칸은 None(화면 "확인 필요").
담당자가 고친 칸(edited_fields)은 재실행 때 덮어쓰지 않는다.
"""

import re

from app.b1_select.extract import llm_extractor, table_mapper
from app.b1_select.food_type.country import normalize_country
from app.b1_select.food_type.normalize import normalize_food_type
from app.core.schema import ExtractedInfo, RawItem
from app.core.storage import repo

LINE = re.compile(r"^\s*([^:：\n]{1,20})\s*[:：]\s*(.+?)\s*$", re.M)


def extract_item(raw: RawItem) -> ExtractedInfo:
    pairs = {k.strip(): v for k, v in LINE.findall(raw.body)}
    fields = table_mapper.map_row(pairs)
    info = ExtractedInfo(item_id=raw.id, **fields)
    llm = llm_extractor.extract(raw)
    if llm:
        for f, v in llm.model_dump(exclude={"item_id", "edited_fields"}).items():
            if getattr(info, f) is None and v is not None:
                setattr(info, f, v)
    info.food_type_std = normalize_food_type(info.food_type_raw)
    info.origin_country = normalize_country(info.origin_country)

    old = repo.get_extracted(raw.id)
    if old:
        for f in old.edited_fields:
            setattr(info, f, getattr(old, f))
        info.edited_fields = old.edited_fields
    repo.save_extracted(info)
    return info
