"""B1-09 본문형 자료 추출 (core/llm.py 준비 후 연결, LSH).

숫자·날짜는 원문에 있는 것만 쓴다. 지금은 None을 돌려준다(규칙 추출만 사용).
"""

from app.core.schema import ExtractedInfo, RawItem


def extract(raw: RawItem) -> ExtractedInfo | None:
    return None
