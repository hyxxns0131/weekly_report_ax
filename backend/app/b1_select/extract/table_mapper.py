"""B1-09 엑셀·CSV 열 이름 → 추출 칸 (LLM 없이). 정보마루 부적합 목록 열 이름 기준(확인 필요)."""

COLUMN_MAP: dict[str, str] = {
    "제품명": "product_name_ko",
    "제품명(영문)": "product_name_en",
    "식품유형": "food_type_raw",
    "제조국": "origin_country",
    "수출국": "export_country",
    "제조업소": "maker",
    "제조회사": "maker",
    "위반내역": "violation",
    "부적합내역": "violation",
    "조치": "action",
    "처리기관": "office",
    "HS코드": "hs_code",
    "제조사": "maker",
    "제조업체": "maker",
    "국가": "origin_country",
    "검사항목": "violation",
    "기간시작": "period_start",
    "기간종료": "period_end",
}


def map_row(row: dict[str, str]) -> dict[str, str]:
    return {COLUMN_MAP[k.strip()]: v for k, v in row.items() if k.strip() in COLUMN_MAP and v}
