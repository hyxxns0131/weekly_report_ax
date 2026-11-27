"""B1-09 엑셀·CSV 열 이름 → 추출 칸 (LLM 없이). 정보마루 부적합 목록 열 이름 + SAMC 실제 열 이름.

- "관련 화주"는 읽지 않는다. 담당자가 채운 결과 칸이라 판단 입력으로 쓰면 안 된다.
- 값 앞뒤의 "[가공식품]" 같은 꼬리표는 떼어 낸다. 꼬리표는 수집 단계에서 본문에
  "분류: 가공식품" 줄로 남는다(collect/base.py).
"""

import re

COLUMN_MAP: dict[str, str] = {
    "제품명": "product_name_ko",
    "제품명(영문)": "product_name_en",
    "식품유형": "food_type_raw",
    "식품유형/품목명": "food_type_raw",
    "제조국": "origin_country",
    "제조국가": "origin_country",
    "수출국": "export_country",
    "제조업소": "maker",
    "제조회사": "maker",
    "제조/수출회사": "maker",
    "위반내역": "violation",
    "위반 내역": "violation",
    "부적합내역": "violation",
    "부적합 사유": "violation",
    "조치": "action",
    "처리기관": "office",
    "HS코드": "hs_code",
    "HS 코드": "hs_code",
    "제조사": "maker",
    "제조업체": "maker",
    "국가": "origin_country",
    "검사항목": "violation",
    "기간시작": "period_start",
    "기간종료": "period_end",
}

IGNORED_COLUMNS = {"관련 화주", "관련화주"}

TAG = re.compile(r"\s*\[([^\[\]]{1,20})\]\s*")


def split_tag(value: str) -> tuple[str, str | None]:
    """ "[가공식품] 냉동새우살" → ("냉동새우살", "가공식품"). 꼬리표가 없으면 (값, None)."""
    m = TAG.search(value)
    if not m:
        return value.strip(), None
    return TAG.sub(" ", value).strip(), m.group(1).strip()


# 꼬리표("[가공식품] …")를 떼는 칸. 위반내역 등의 "[기준: 불검출]" 같은 괄호는 원문 그대로 둔다.
TAGGED_FIELDS = {"food_type_raw", "product_name_ko"}


def map_row(row: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in row.items():
        key = k.strip()
        if key in IGNORED_COLUMNS or key not in COLUMN_MAP or not v:
            continue
        field = COLUMN_MAP[key]
        clean = split_tag(v)[0] if field in TAGGED_FIELDS else v.strip()
        if clean:
            out[field] = clean
    return out
