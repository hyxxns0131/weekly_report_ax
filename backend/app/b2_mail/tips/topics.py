"""B2-07 오늘의 팁 주제 후보 (제안서 6번 예시). 근거는 담당자가 확인한 뒤에만 넣는다."""

from pydantic import BaseModel


class Topic(BaseModel):
    id: str
    title: str
    basis: str  # 근거를 찾을 곳 (확인 필요)


TOPICS: list[Topic] = [
    Topic(
        id="same_vessel",
        title="동일 모선·동일 식품은 함께 검역 신고",
        basis="수입식품안전관리 특별법 시행규칙 관련 조항 · 최신본 확인 필요",
    ),
    Topic(
        id="japan_radiation",
        title="일본 특정 지역 생산품 방사능 검사 증명서",
        basis="수입식품등 검사에 관한 규정 · 최신본 확인 필요",
    ),
    Topic(
        id="labeling_claims",
        title="Natural·유기농·Gluten Free 표시 조건",
        basis="식품등의 표시기준, 부당한 표시·광고 내용 기준 · 최신본 확인 필요",
    ),
    Topic(
        id="documents",
        title="식품유형·용도별 구비서류",
        basis="수입식품등 검사에 관한 규정 · 최신본 확인 필요",
    ),
]
