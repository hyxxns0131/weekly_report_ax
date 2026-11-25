"""B1-08 LLM 분류 (core/llm.py 준비 후 연결, LSH).

규칙: 결과가 키워드 규칙과 다르면 review_needed. 형식 오류는 1회 재시도 후 review_needed.
지금은 LLM을 부르지 않고 None을 돌려준다(키워드 규칙만 사용).
"""

from app.core.schema import Selection


def classify(item_id: str, title: str, body: str) -> Selection | None:
    return None
